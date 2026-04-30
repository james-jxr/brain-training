import { describe, it, expect } from 'vitest';

// ─── Pure helpers extracted from CardMemoryGame logic ─────────────────────────

/**
 * Mirror of calculateSpeedBonus from CardMemoryGame.jsx
 */
function calculateSpeedBonus(responseTimeMs, memorizationTime) {
  const windowMs = (15 - memorizationTime) * 1000 + 5000;
  if (responseTimeMs >= windowMs) return 0;
  const bonus = (1 - responseTimeMs / windowMs) * 100;
  return Math.max(0, Math.min(100, bonus));
}

/**
 * Mirror of getDifficultyString from CardMemoryGame.jsx
 */
function getDifficultyString(numDifficulty) {
  if (numDifficulty <= 3) return 'easy';
  if (numDifficulty <= 6) return 'medium';
  return 'hard';
}

const difficultyConfig = {
  easy:   { cardCount: 4,  memorizationTime: 15, shuffleCount: 0 },
  medium: { cardCount: 8,  memorizationTime: 15, shuffleCount: 1 },
  hard:   { cardCount: 12, memorizationTime: 15, shuffleCount: 2 },
};

/**
 * Mirror of getGridCols from CardMemoryGame.jsx
 */
function getGridCols(cardCount) {
  if (cardCount === 4) return 2;
  if (cardCount === 8) return 4;
  return 4;
}

/**
 * Mirror of getShapeName
 */
function getShapeName(shape) {
  const names = {
    '◯': 'Circle',
    '△': 'Triangle',
    '★': 'Star',
    '□': 'Square',
    '◇': 'Diamond',
  };
  return names[shape] || 'Shape';
}

// ─── getDifficultyString ──────────────────────────────────────────────────────

describe('getDifficultyString', () => {
  it('returns easy for difficulty 1', () => {
    expect(getDifficultyString(1)).toBe('easy');
  });

  it('returns easy for difficulty 3', () => {
    expect(getDifficultyString(3)).toBe('easy');
  });

  it('returns medium for difficulty 4', () => {
    expect(getDifficultyString(4)).toBe('medium');
  });

  it('returns medium for difficulty 6', () => {
    expect(getDifficultyString(6)).toBe('medium');
  });

  it('returns hard for difficulty 7', () => {
    expect(getDifficultyString(7)).toBe('hard');
  });

  it('returns hard for difficulty 10', () => {
    expect(getDifficultyString(10)).toBe('hard');
  });
});

// ─── difficultyConfig ─────────────────────────────────────────────────────────

describe('difficultyConfig', () => {
  it('easy: cardCount=4, memorizationTime=15, shuffleCount=0', () => {
    expect(difficultyConfig.easy).toEqual({ cardCount: 4, memorizationTime: 15, shuffleCount: 0 });
  });

  it('medium: cardCount=8, memorizationTime=15, shuffleCount=1', () => {
    expect(difficultyConfig.medium).toEqual({ cardCount: 8, memorizationTime: 15, shuffleCount: 1 });
  });

  it('hard: cardCount=12, memorizationTime=15, shuffleCount=2', () => {
    expect(difficultyConfig.hard).toEqual({ cardCount: 12, memorizationTime: 15, shuffleCount: 2 });
  });
});

// ─── calculateSpeedBonus ──────────────────────────────────────────────────────

describe('calculateSpeedBonus', () => {
  it('returns 100 (max) for near-instant response', () => {
    const bonus = calculateSpeedBonus(1, 15);
    // windowMs = (15-15)*1000 + 5000 = 5000; bonus = (1 - 1/5000)*100 ≈ 100
    expect(bonus).toBeCloseTo(100, 0);
  });

  it('returns 0 when response equals window', () => {
    // windowMs = 5000; responseTimeMs = 5000
    const bonus = calculateSpeedBonus(5000, 15);
    expect(bonus).toBe(0);
  });

  it('returns 0 when response exceeds window', () => {
    const bonus = calculateSpeedBonus(9999, 15);
    expect(bonus).toBe(0);
  });

  it('returns ~50 for half-window response', () => {
    // windowMs = 5000; responseTimeMs = 2500; bonus = 0.5 * 100 = 50
    const bonus = calculateSpeedBonus(2500, 15);
    expect(bonus).toBeCloseTo(50, 0);
  });

  it('bonus is clamped to [0, 100]', () => {
    for (const rt of [0, 100, 2500, 4999, 5000, 5001, 10000]) {
      const bonus = calculateSpeedBonus(rt, 15);
      expect(bonus).toBeGreaterThanOrEqual(0);
      expect(bonus).toBeLessThanOrEqual(100);
    }
  });

  it('window expands when memorizationTime < 15', () => {
    // memorizationTime=10 -> windowMs = (15-10)*1000+5000 = 10000
    const bonus = calculateSpeedBonus(5000, 10);
    expect(bonus).toBeCloseTo(50, 0);
  });
});

// ─── getGridCols ──────────────────────────────────────────────────────────────

describe('getGridCols', () => {
  it('returns 2 for 4 cards', () => {
    expect(getGridCols(4)).toBe(2);
  });

  it('returns 4 for 8 cards', () => {
    expect(getGridCols(8)).toBe(4);
  });

  it('returns 4 for 12 cards', () => {
    expect(getGridCols(12)).toBe(4);
  });
});

// ─── getShapeName ─────────────────────────────────────────────────────────────

describe('getShapeName', () => {
  it('returns Circle for ◯', () => {
    expect(getShapeName('◯')).toBe('Circle');
  });

  it('returns Triangle for △', () => {
    expect(getShapeName('△')).toBe('Triangle');
  });

  it('returns Star for ★', () => {
    expect(getShapeName('★')).toBe('Star');
  });

  it('returns Square for □', () => {
    expect(getShapeName('□')).toBe('Square');
  });

  it('returns Diamond for ◇', () => {
    expect(getShapeName('◇')).toBe('Diamond');
  });

  it('returns Shape for unknown', () => {
    expect(getShapeName('X')).toBe('Shape');
  });

  it('returns Shape for empty string', () => {
    expect(getShapeName('')).toBe('Shape');
  });
});

// ─── proceedAfterRound logic ──────────────────────────────────────────────────

describe('proceedAfterRound score aggregation', () => {
  /**
   * Mirror of the completion payload assembly inside proceedAfterRound
   */
  function buildCompletionPayload(updatedResults, numRounds, difficultyString, cardCount) {
    const totalSessionScore = updatedResults.reduce((sum, r) => sum + r.score, 0);
    const totalCorrect = updatedResults.filter(r => r.correct).length;
    const avgResponseTime = updatedResults.reduce((sum, r) => sum + r.response_time_ms, 0) / updatedResults.length;

    return {
      difficulty: difficultyString,
      card_count: cardCount,
      correct: totalCorrect === numRounds,
      response_time_ms: Math.round(avgResponseTime),
      score: Math.round(totalSessionScore / numRounds),
      rounds: updatedResults,
      total_rounds: numRounds,
      rounds_correct: totalCorrect,
    };
  }

  it('correct=true when all rounds correct', () => {
    const results = [
      { correct: true, response_time_ms: 500, score: 150 },
      { correct: true, response_time_ms: 600, score: 140 },
      { correct: true, response_time_ms: 400, score: 160 },
    ];
    const payload = buildCompletionPayload(results, 3, 'easy', 4);
    expect(payload.correct).toBe(true);
    expect(payload.rounds_correct).toBe(3);
  });

  it('correct=false when any round incorrect', () => {
    const results = [
      { correct: true,  response_time_ms: 500, score: 150 },
      { correct: false, response_time_ms: 600, score: 0   },
      { correct: true,  response_time_ms: 400, score: 160 },
    ];
    const payload = buildCompletionPayload(results, 3, 'easy', 4);
    expect(payload.correct).toBe(false);
    expect(payload.rounds_correct).toBe(2);
  });

  it('score is avg of round scores', () => {
    const results = [
      { correct: true, response_time_ms: 500, score: 100 },
      { correct: true, response_time_ms: 500, score: 200 },
      { correct: true, response_time_ms: 500, score: 150 },
    ];
    const payload = buildCompletionPayload(results, 3, 'medium', 8);
    expect(payload.score).toBe(150);
  });

  it('response_time_ms is rounded avg', () => {
    const results = [
      { correct: true, response_time_ms: 100, score: 100 },
      { correct: true, response_time_ms: 200, score: 100 },
      { correct: true, response_time_ms: 300, score: 100 },
    ];
    const payload = buildCompletionPayload(results, 3, 'easy', 4);
    expect(payload.response_time_ms).toBe(200);
  });

  it('total_rounds equals numRounds', () => {
    const results = [
      { correct: true, response_time_ms: 500, score: 100 },
    ];
    const payload = buildCompletionPayload(results, 5, 'hard', 12);
    expect(payload.total_rounds).toBe(5);
  });

  it('difficulty and card_count are passed through', () => {
    const results = [{ correct: false, response_time_ms: 999, score: 0 }];
    const payload = buildCompletionPayload(results, 1, 'hard', 12);
    expect(payload.difficulty).toBe('hard');
    expect(payload.card_count).toBe(12);
  });

  it('rounds array equals the input results', () => {
    const results = [
      { correct: true, response_time_ms: 400, score: 120 },
      { correct: true, response_time_ms: 350, score: 130 },
    ];
    const payload = buildCompletionPayload(results, 2, 'medium', 8);
    expect(payload.rounds).toEqual(results);
  });
});
