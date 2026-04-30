"""Tests for SessionPlannerService.

Covers:
  1. plan_session domain selection logic (balanced vs unbalanced scores)
  2. Priority domain selection when one domain is significantly behind
  3. get_trials_per_domain / get_trials_per_exercise / get_rounds_for_exercise
  4. is_no_scoring_exercise
"""
import pytest
from unittest.mock import MagicMock
from backend.services.session_planner import SessionPlannerService
from backend.models import DomainProgress


def make_mock_db(domain_scores: dict):
    """Create a mock DB session that returns DomainProgress objects for given domain scores."""
    db = MagicMock()

    def query_side_effect(model):
        mock_query = MagicMock()

        def filter_side_effect(*args, **kwargs):
            mock_filter = MagicMock()

            def first_side_effect():
                # Extract domain from filter args - inspect the filter call
                # We'll intercept via a different approach
                return mock_filter._first_result

            mock_filter.first = first_side_effect
            return mock_filter

        mock_query.filter = filter_side_effect
        return mock_query

    db.query.side_effect = query_side_effect
    return db


def make_mock_db_simple(domain_scores: dict):
    """Simpler mock DB using a closure over domain_scores."""
    db = MagicMock()

    def build_chain(domain_name):
        score = domain_scores.get(domain_name)
        mock_progress = MagicMock(spec=DomainProgress)
        if score is not None:
            mock_progress.last_score = score
        else:
            mock_progress = None

        chain = MagicMock()
        chain.first.return_value = mock_progress
        return chain

    call_count = [0]
    domains_order = ["processing_speed", "working_memory", "attention"]

    def filter_func(*args):
        idx = call_count[0] % len(domains_order)
        domain = domains_order[idx]
        call_count[0] += 1
        return build_chain(domain)

    db.query.return_value.filter.side_effect = filter_func
    return db


class TestSessionPlannerDomainSelection:
    """Tests for plan_session domain priority logic."""

    def _plan_with_scores(self, scores: dict):
        """Run plan_session with explicit per-domain scores."""
        db = MagicMock()
        domains = ["processing_speed", "working_memory", "attention"]
        call_index = [0]

        def make_progress(score):
            if score is None:
                return None
            p = MagicMock()
            p.last_score = score
            return p

        def filter_mock(*args):
            m = MagicMock()
            idx = call_index[0] % len(domains)
            domain = domains[idx]
            call_index[0] += 1
            m.first.return_value = make_progress(scores.get(domain))
            return m

        db.query.return_value.filter.side_effect = filter_mock
        return SessionPlannerService.plan_session(db, user_id=1)

    def test_returns_domain_1_and_domain_2(self):
        result = self._plan_with_scores(
            {"processing_speed": 50, "working_memory": 50, "attention": 50}
        )
        assert "domain_1" in result
        assert "domain_2" in result
        assert "exercises" in result

    def test_balanced_domains_prioritise_highest_score(self):
        """When all domains within 10 pts, highest-scoring domain is domain_1."""
        result = self._plan_with_scores(
            {"processing_speed": 60, "working_memory": 65, "attention": 62}
        )
        # All within 10 pts of max (65), so priority = highest = working_memory
        assert result["domain_1"] == "working_memory"

    def test_weak_domain_is_prioritised(self):
        """When one domain is >10pts behind the max, it is prioritised."""
        result = self._plan_with_scores(
            {"processing_speed": 80, "working_memory": 80, "attention": 50}
        )
        # attention is 30pts behind max (80) -> should be prioritised
        assert result["domain_1"] == "attention"

    def test_no_scores_all_zero(self):
        """When no scores exist, all domains are 0 and balanced logic applies."""
        result = self._plan_with_scores(
            {"processing_speed": None, "working_memory": None, "attention": None}
        )
        # All zero, balanced - highest (all tied) should give last in sorted order
        assert result["domain_1"] in ["processing_speed", "working_memory", "attention"]
        assert result["domain_2"] in ["processing_speed", "working_memory", "attention"]
        assert result["domain_1"] != result["domain_2"]

    def test_exercises_contain_both_selected_domains(self):
        result = self._plan_with_scores(
            {"processing_speed": 70, "working_memory": 70, "attention": 70}
        )
        assert result["domain_1"] in result["exercises"]
        assert result["domain_2"] in result["exercises"]

    def test_exercises_always_include_mindfulness(self):
        result = self._plan_with_scores(
            {"processing_speed": 70, "working_memory": 70, "attention": 70}
        )
        assert "mindfulness" in result["exercises"]

    def test_exercise_types_are_lists(self):
        result = self._plan_with_scores(
            {"processing_speed": 50, "working_memory": 50, "attention": 50}
        )
        for domain, exercises in result["exercises"].items():
            assert isinstance(exercises, list), f"{domain} exercises should be a list"

    def test_exactly_10_pts_difference_is_not_weak(self):
        """Exactly 10 pts behind is NOT more than 10, so balanced logic applies."""
        result = self._plan_with_scores(
            {"processing_speed": 80, "working_memory": 80, "attention": 70}
        )
        # 70 is exactly 10 behind 80 (not > 10), so highest (ps or wm) is prioritised
        assert result["domain_1"] in ["processing_speed", "working_memory"]

    def test_11_pts_difference_triggers_weak_domain_priority(self):
        """11 pts behind -> weak domain is prioritised."""
        result = self._plan_with_scores(
            {"processing_speed": 80, "working_memory": 80, "attention": 69}
        )
        assert result["domain_1"] == "attention"


class TestSessionPlannerHelpers:
    """Tests for helper static methods."""

    def test_get_trials_per_domain_returns_positive_int(self):
        result = SessionPlannerService.get_trials_per_domain()
        assert isinstance(result, int)
        assert result > 0

    def test_get_trials_per_domain_returns_8(self):
        assert SessionPlannerService.get_trials_per_domain() == 8

    def test_get_trials_per_exercise_returns_positive_int(self):
        result = SessionPlannerService.get_trials_per_exercise()
        assert isinstance(result, int)
        assert result > 0

    def test_get_trials_per_exercise_returns_4(self):
        assert SessionPlannerService.get_trials_per_exercise() == 4

    def test_get_rounds_for_exercise_default_is_1(self):
        assert SessionPlannerService.get_rounds_for_exercise("n_back") == 1
        assert SessionPlannerService.get_rounds_for_exercise("stroop") == 1

    def test_get_rounds_for_exercise_card_memory_minimum_3(self):
        assert SessionPlannerService.get_rounds_for_exercise("card_memory") == 3

    def test_get_rounds_for_exercise_never_below_1(self):
        result = SessionPlannerService.get_rounds_for_exercise("unknown_exercise")
        assert result >= 1


class TestNoScoringExercises:
    """Tests for is_no_scoring_exercise."""

    def test_mindfulness_is_no_scoring(self):
        assert SessionPlannerService.is_no_scoring_exercise("mindfulness") is True

    def test_regular_exercises_are_scoring(self):
        scoring_exercises = [
            "n_back", "digit_span", "go_no_go", "stroop",
            "symbol_matching", "visual_categorisation"
        ]
        for ex in scoring_exercises:
            assert SessionPlannerService.is_no_scoring_exercise(ex) is False, (
                f"{ex} should be a scoring exercise"
            )

    def test_empty_string_is_scoring(self):
        assert SessionPlannerService.is_no_scoring_exercise("") is False

    def test_unknown_exercise_is_scoring(self):
        assert SessionPlannerService.is_no_scoring_exercise("unknown") is False
