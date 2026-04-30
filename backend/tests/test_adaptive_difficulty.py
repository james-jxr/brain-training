import os
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-ci')
os.environ.setdefault('DATABASE_URL', 'sqlite:///./test.db')

import pytest
from backend.services.adaptive_difficulty import adjust_difficulty_in_session, AdaptiveDifficultyService


class TestAdjustDifficultyInSession:
    """Unit tests for the 2-up/1-down staircase adapt function."""

    def test_below_50_decreases_difficulty(self):
        assert adjust_difficulty_in_session(5, 40.0, 0) == 4

    def test_exactly_50_no_change(self):
        assert adjust_difficulty_in_session(5, 50.0, 0) == 5

    def test_above_80_with_one_consecutive_no_change(self):
        assert adjust_difficulty_in_session(5, 90.0, 1) == 5

    def test_above_80_with_two_consecutive_increases(self):
        assert adjust_difficulty_in_session(5, 90.0, 2) == 6

    def test_above_80_with_more_than_two_consecutive_increases(self):
        assert adjust_difficulty_in_session(5, 90.0, 3) == 6

    def test_floor_at_1(self):
        assert adjust_difficulty_in_session(1, 10.0, 0) == 1

    def test_ceiling_at_10(self):
        assert adjust_difficulty_in_session(10, 95.0, 2) == 10

    def test_score_between_50_and_80_no_change(self):
        assert adjust_difficulty_in_session(5, 65.0, 5) == 5

    def test_score_exactly_80_no_change(self):
        assert adjust_difficulty_in_session(5, 80.0, 2) == 5

    def test_score_exactly_81_with_two_consecutive_increases(self):
        assert adjust_difficulty_in_session(5, 81.0, 2) == 6

    def test_zero_score_decreases_difficulty(self):
        assert adjust_difficulty_in_session(3, 0.0, 0) == 2

    def test_100_score_with_two_consecutive_increases(self):
        assert adjust_difficulty_in_session(7, 100.0, 2) == 8


class TestCalculateScore:
    def test_perfect_score(self):
        assert AdaptiveDifficultyService.calculate_score(10, 10) == 100.0

    def test_zero_score(self):
        assert AdaptiveDifficultyService.calculate_score(10, 0) == 0.0

    def test_partial_score(self):
        assert AdaptiveDifficultyService.calculate_score(4, 3) == 75.0

    def test_zero_trials_presented_returns_zero(self):
        assert AdaptiveDifficultyService.calculate_score(0, 0) == 0.0

    def test_fractional_score(self):
        result = AdaptiveDifficultyService.calculate_score(3, 1)
        assert abs(result - 33.333) < 0.1
