"""Tests for BrainHealthScoreService.

Covers:
  1. calculate_domain_average — empty, partial, full
  2. calculate_lifestyle_score — empty, partial, boundary conditions
  3. calculate_brain_health_score — combined scoring
"""
import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch
from backend.services.brain_health_score import (
    BrainHealthScoreService,
    DOMAIN_SCORE_WEIGHT,
    LIFESTYLE_SCORE_WEIGHT,
    TARGET_EXERCISE_MINUTES,
    TARGET_SLEEP_HOURS,
    MAX_LIFESTYLE_FACTOR_SCORE,
)
from backend.models import DomainProgress, LifestyleLog


def make_mock_db():
    return MagicMock()


def make_domain_progress(domain, last_score):
    p = MagicMock(spec=DomainProgress)
    p.domain = domain
    p.last_score = last_score
    return p


def make_lifestyle_log(
    exercise_minutes=30,
    sleep_hours=7,
    stress_level=2,
    mood=4,
):
    log = MagicMock(spec=LifestyleLog)
    log.exercise_minutes = exercise_minutes
    log.sleep_hours = sleep_hours
    log.stress_level = stress_level
    log.mood = mood
    return log


class TestCalculateDomainAverage:
    def _setup_db_for_domains(self, db, domain_scores: dict):
        """Configure db.query(...).filter(...).first() to return appropriate DomainProgress."""
        domains = ["processing_speed", "working_memory", "attention"]
        call_index = [0]

        def filter_mock(*args):
            m = MagicMock()
            idx = call_index[0] % len(domains)
            domain = domains[idx]
            call_index[0] += 1
            score = domain_scores.get(domain)
            if score is None:
                m.first.return_value = None
            else:
                p = make_domain_progress(domain, score)
                m.first.return_value = p
            return m

        db.query.return_value.filter.side_effect = filter_mock

    def test_returns_zero_when_no_domain_progress(self):
        db = make_mock_db()
        self._setup_db_for_domains(db, {})
        result = BrainHealthScoreService.calculate_domain_average(db, user_id=1)
        assert result == 0.0

    def test_returns_average_of_all_three_domains(self):
        db = make_mock_db()
        self._setup_db_for_domains(db, {
            "processing_speed": 60,
            "working_memory": 80,
            "attention": 70,
        })
        result = BrainHealthScoreService.calculate_domain_average(db, user_id=1)
        assert result == pytest.approx(70.0)

    def test_partial_domains_averages_available_only(self):
        db = make_mock_db()
        self._setup_db_for_domains(db, {
            "processing_speed": 60,
            "working_memory": None,
            "attention": None,
        })
        result = BrainHealthScoreService.calculate_domain_average(db, user_id=1)
        assert result == pytest.approx(60.0)

    def test_single_domain_with_zero_score(self):
        db = make_mock_db()
        self._setup_db_for_domains(db, {
            "processing_speed": 0,
            "working_memory": None,
            "attention": None,
        })
        result = BrainHealthScoreService.calculate_domain_average(db, user_id=1)
        assert result == 0.0

    def test_all_domains_100_returns_100(self):
        db = make_mock_db()
        self._setup_db_for_domains(db, {
            "processing_speed": 100,
            "working_memory": 100,
            "attention": 100,
        })
        result = BrainHealthScoreService.calculate_domain_average(db, user_id=1)
        assert result == pytest.approx(100.0)


class TestCalculateLifestyleScore:
    def _setup_db_for_logs(self, db, logs):
        db.query.return_value.filter.return_value.all.return_value = logs

    def test_returns_zero_when_no_logs(self):
        db = make_mock_db()
        self._setup_db_for_logs(db, [])
        result = BrainHealthScoreService.calculate_lifestyle_score(db, user_id=1)
        assert result == 0.0

    def test_perfect_log_returns_100(self):
        db = make_mock_db()
        log = make_lifestyle_log(
            exercise_minutes=TARGET_EXERCISE_MINUTES,
            sleep_hours=TARGET_SLEEP_HOURS,
            stress_level=1,  # low stress
            mood=5,  # high mood
        )
        self._setup_db_for_logs(db, [log])
        result = BrainHealthScoreService.calculate_lifestyle_score(db, user_id=1)
        assert result == pytest.approx(100.0)

    def test_zero_exercise_contributes_zero(self):
        db = make_mock_db()
        log = make_lifestyle_log(exercise_minutes=0, sleep_hours=TARGET_SLEEP_HOURS, stress_level=1, mood=5)
        self._setup_db_for_logs(db, [log])
        result = BrainHealthScoreService.calculate_lifestyle_score(db, user_id=1)
        # exercise contributes 0, others contribute 25 each = 75 total
        assert result == pytest.approx(75.0)

    def test_half_exercise_contributes_half_max(self):
        db = make_mock_db()
        log = make_lifestyle_log(
            exercise_minutes=TARGET_EXERCISE_MINUTES // 2,
            sleep_hours=TARGET_SLEEP_HOURS,
            stress_level=1,
            mood=5,
        )
        self._setup_db_for_logs(db, [log])
        result = BrainHealthScoreService.calculate_lifestyle_score(db, user_id=1)
        # exercise: 12.5, sleep: 25, stress: 25, mood: 25 = 87.5
        assert result == pytest.approx(87.5)

    def test_score_capped_at_100(self):
        db = make_mock_db()
        # Everything above target
        log = make_lifestyle_log(
            exercise_minutes=TARGET_EXERCISE_MINUTES * 10,
            sleep_hours=TARGET_SLEEP_HOURS * 2,
            stress_level=1,
            mood=5,
        )
        self._setup_db_for_logs(db, [log])
        result = BrainHealthScoreService.calculate_lifestyle_score(db, user_id=1)
        assert result <= 100.0

    def test_high_stress_reduces_score(self):
        db = make_mock_db()
        log_low_stress = make_lifestyle_log(exercise_minutes=TARGET_EXERCISE_MINUTES, sleep_hours=TARGET_SLEEP_HOURS, stress_level=1, mood=5)
        log_high_stress = make_lifestyle_log(exercise_minutes=TARGET_EXERCISE_MINUTES, sleep_hours=TARGET_SLEEP_HOURS, stress_level=10, mood=5)

        db_low = make_mock_db()
        db_high = make_mock_db()
        db_low.query.return_value.filter.return_value.all.return_value = [log_low_stress]
        db_high.query.return_value.filter.return_value.all.return_value = [log_high_stress]

        score_low = BrainHealthScoreService.calculate_lifestyle_score(db_low, user_id=1)
        score_high = BrainHealthScoreService.calculate_lifestyle_score(db_high, user_id=1)
        assert score_low > score_high

    def test_multiple_logs_averaged(self):
        db = make_mock_db()
        log1 = make_lifestyle_log(exercise_minutes=TARGET_EXERCISE_MINUTES, sleep_hours=TARGET_SLEEP_HOURS, stress_level=1, mood=5)
        log2 = make_lifestyle_log(exercise_minutes=0, sleep_hours=0, stress_level=10, mood=1)
        self._setup_db_for_logs(db, [log1, log2])
        result = BrainHealthScoreService.calculate_lifestyle_score(db, user_id=1)
        # Should be between 0 and 100
        assert 0 <= result <= 100


class TestCalculateBrainHealthScore:
    def _setup_all_mocks(self, db, domain_avg, lifestyle_score):
        with patch.object(BrainHealthScoreService, 'calculate_domain_average', return_value=domain_avg), \
             patch.object(BrainHealthScoreService, 'calculate_lifestyle_score', return_value=lifestyle_score):
            return BrainHealthScoreService.calculate_brain_health_score(db, user_id=1)

    def test_returns_int(self):
        db = make_mock_db()
        result = self._setup_all_mocks(db, 50.0, 50.0)
        assert isinstance(result, int)

    def test_zero_domain_zero_lifestyle_returns_0(self):
        db = make_mock_db()
        result = self._setup_all_mocks(db, 0.0, 0.0)
        assert result == 0

    def test_full_domain_full_lifestyle_returns_100(self):
        db = make_mock_db()
        result = self._setup_all_mocks(db, 100.0, 100.0)
        assert result == 100

    def test_weighted_combination(self):
        db = make_mock_db()
        result = self._setup_all_mocks(db, 100.0, 0.0)
        expected = int(100.0 * DOMAIN_SCORE_WEIGHT + 0.0 * LIFESTYLE_SCORE_WEIGHT)
        assert result == expected

    def test_lifestyle_only_weighted(self):
        db = make_mock_db()
        result = self._setup_all_mocks(db, 0.0, 100.0)
        expected = int(0.0 * DOMAIN_SCORE_WEIGHT + 100.0 * LIFESTYLE_SCORE_WEIGHT)
        assert result == expected

    def test_result_never_exceeds_100(self):
        db = make_mock_db()
        result = self._setup_all_mocks(db, 200.0, 200.0)
        assert result <= 100

    def test_result_never_below_0(self):
        db = make_mock_db()
        result = self._setup_all_mocks(db, -100.0, -100.0)
        assert result >= 0
