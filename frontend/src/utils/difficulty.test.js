import { describe, it, expect } from 'vitest';
import { BASELINE_LEVEL_TO_DIFFICULTY } from './difficulty';

describe('BASELINE_LEVEL_TO_DIFFICULTY', () => {
  it('maps level 1 to difficulty 1', () => {
    expect(BASELINE_LEVEL_TO_DIFFICULTY[1]).toBe(1);
  });

  it('maps level 2 to difficulty 4', () => {
    expect(BASELINE_LEVEL_TO_DIFFICULTY[2]).toBe(4);
  });

  it('maps level 3 to difficulty 7', () => {
    expect(BASELINE_LEVEL_TO_DIFFICULTY[3]).toBe(7);
  });

  it('returns undefined for unknown level 0', () => {
    expect(BASELINE_LEVEL_TO_DIFFICULTY[0]).toBeUndefined();
  });

  it('returns undefined for unknown level 4', () => {
    expect(BASELINE_LEVEL_TO_DIFFICULTY[4]).toBeUndefined();
  });

  it('has exactly 3 entries', () => {
    expect(Object.keys(BASELINE_LEVEL_TO_DIFFICULTY)).toHaveLength(3);
  });

  it('all difficulty values are positive integers', () => {
    for (const val of Object.values(BASELINE_LEVEL_TO_DIFFICULTY)) {
      expect(typeof val).toBe('number');
      expect(val).toBeGreaterThan(0);
      expect(Number.isInteger(val)).toBe(true);
    }
  });

  it('difficulty values are in ascending order', () => {
    const vals = [1, 2, 3].map((k) => BASELINE_LEVEL_TO_DIFFICULTY[k]);
    for (let i = 1; i < vals.length; i++) {
      expect(vals[i]).toBeGreaterThan(vals[i - 1]);
    }
  });
});
