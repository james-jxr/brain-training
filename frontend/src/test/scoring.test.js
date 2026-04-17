import { describe, it, expect } from 'vitest';
import {
  calculateScore,
  calculateScoreFromAccuracy,
  calculateDigitSpanScore,
  formatScore,
  getScoreFeedback,
  getAverageScore,
  getDifficultyColor,
  calculateBrainHealthScore,
} from '../utils/scoring';

describe('calculateScore', () => {
  it('returns 0 when totalMoves is 0', () => {
    expect(calculateScore(0, 0, 0)).toBe(0);
  });

  it('calculates correct percentage', () => {
    expect(calculateScore(3, 5, 10)).toBe(80);
  });

  it('returns 100 when all moves are correct', () => {
    expect(calculateScore(5, 5, 10)).toBe(100);
  });
});

describe('calculateScoreFromAccuracy', () => {
  it('returns 0 when totalMoves is 0', () => {
    expect(calculateScoreFromAccuracy(0, 0)).toBe(0);
  });

  it('calculates accuracy percentage', () => {
    expect(calculateScoreFromAccuracy(7, 10)).toBe(70);
  });

  it('returns 100 for perfect accuracy', () => {
    expect(calculateScoreFromAccuracy(8, 8)).toBe(100);
  });
});

describe('calculateDigitSpanScore', () => {
  it('returns 0 when trialsPresented is 0', () => {
    expect(calculateDigitSpanScore(0, 0, 0)).toBe(0);
  });

  it('computes composite from accuracy and maxLengthRecalled', () => {
    // accuracyPct = (4/8)*100 = 50, composite = 50*0.5 + 4*5 = 25 + 20 = 45
    expect(calculateDigitSpanScore(4, 8, 4)).toBe(45);
  });

  it('caps the score at 100', () => {
    // accuracyPct = 100, composite = 100*0.5 + 10*5 = 50 + 50 = 100
    expect(calculateDigitSpanScore(8, 8, 10)).toBe(100);
  });

  it('caps when composite would exceed 100', () => {
    // accuracyPct = 100, composite = 50 + 15*5 = 50+75 = 125 → capped at 100
    expect(calculateDigitSpanScore(8, 8, 15)).toBe(100);
  });

  it('returns low score for low accuracy and low maxLength', () => {
    // accuracyPct = (1/8)*100 = 12.5, composite = 12.5*0.5 + 2*5 = 6.25 + 10 = 16.25
    expect(calculateDigitSpanScore(1, 8, 2)).toBeCloseTo(16.25);
  });

  it('returns 0 composite when both trialsCorrect and maxLengthRecalled are 0', () => {
    // accuracyPct = 0, composite = 0*0.5 + 0*5 = 0
    expect(calculateDigitSpanScore(0, 8, 0)).toBe(0);
  });

  it('handles perfect score with reasonable maxLength', () => {
    // accuracyPct = 100, composite = 50 + 7*5 = 50+35 = 85
    expect(calculateDigitSpanScore(8, 8, 7)).toBe(85);
  });

  it('handles single trial correct', () => {
    // accuracyPct = (1/1)*100 = 100, composite = 50 + 3*5 = 65
    expect(calculateDigitSpanScore(1, 1, 3)).toBe(65);
  });
});

describe('formatScore', () => {
  it('rounds to one decimal place', () => {
    expect(formatScore(85.55)).toBe(85.6);
  });

  it('handles whole numbers', () => {
    expect(formatScore(90)).toBe(90);
  });
});

describe('getScoreFeedback', () => {
  it('returns excellent for score >= 80', () => {
    expect(getScoreFeedback(80).status).toBe('excellent');
    expect(getScoreFeedback(95).status).toBe('excellent');
  });

  it('returns good for score >= 70', () => {
    expect(getScoreFeedback(70).status).toBe('good');
    expect(getScoreFeedback(79).status).toBe('good');
  });

  it('returns fair for score >= 50', () => {
    expect(getScoreFeedback(50).status).toBe('fair');
    expect(getScoreFeedback(69).status).toBe('fair');
  });

  it('returns poor for score < 50', () => {
    expect(getScoreFeedback(49).status).toBe('poor');
    expect(getScoreFeedback(0).status).toBe('poor');
  });
});

describe('getAverageScore', () => {
  it('returns 0 for empty array', () => {
    expect(getAverageScore([])).toBe(0);
  });

  it('returns the score for a single element', () => {
    expect(getAverageScore([75])).toBe(75);
  });

  it('calculates average correctly', () => {
    expect(getAverageScore([60, 80, 100])).toBeCloseTo(80);
  });
});

describe('getDifficultyColor', () => {
  it('returns success color for difficulty <= 3', () => {
    expect(getDifficultyColor(1)).toBe('var(--color-success)');
    expect(getDifficultyColor(3)).toBe('var(--color-success)');
  });

  it('returns warning color for difficulty <= 6', () => {
    expect(getDifficultyColor(4)).toBe('var(--color-warning)');
    expect(getDifficultyColor(6)).toBe('var(--color-warning)');
  });

  it('returns error color for difficulty > 6', () => {
    expect(getDifficultyColor(7)).toBe('var(--color-error)');
    expect(getDifficultyColor(10)).toBe('var(--color-error)');
  });
});

describe('calculateBrainHealthScore', () => {
  it('combines domain and lifestyle scores with correct weights', () => {
    expect(calculateBrainHealthScore(80, 60)).toBe(Math.round(80 * 0.6 + 60 * 0.4));
  });

  it('returns 0 for all-zero inputs', () => {
    expect(calculateBrainHealthScore(0, 0)).toBe(0);
  });

  it('rounds the result', () => {
    // 70*0.6 + 70*0.4 = 42 + 28 = 70 (exact)
    expect(calculateBrainHealthScore(70, 70)).toBe(70);
  });
});
