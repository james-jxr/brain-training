import { describe, it, expect } from 'vitest';
import {
  BASELINE_LEVEL_TO_DIFFICULTY,
  MAX_ROUNDS,
  INITIAL_LEVEL,
} from './gameConstants';

describe('gameConstants', () => {
  describe('BASELINE_LEVEL_TO_DIFFICULTY', () => {
    it('maps level 1 (Easy) to difficulty 2', () => {
      expect(BASELINE_LEVEL_TO_DIFFICULTY[1]).toBe(2);
    });

    it('maps level 2 (Medium) to difficulty 5', () => {
      expect(BASELINE_LEVEL_TO_DIFFICULTY[2]).toBe(5);
    });

    it('maps level 3 (Hard) to difficulty 8', () => {
      expect(BASELINE_LEVEL_TO_DIFFICULTY[3]).toBe(8);
    });

    it('has exactly 3 entries', () => {
      expect(Object.keys(BASELINE_LEVEL_TO_DIFFICULTY).length).toBe(3);
    });

    it('all difficulty values are within 1-10 range', () => {
      Object.values(BASELINE_LEVEL_TO_DIFFICULTY).forEach((val) => {
        expect(val).toBeGreaterThanOrEqual(1);
        expect(val).toBeLessThanOrEqual(10);
      });
    });

    it('difficulties are ordered ascending with level', () => {
      expect(BASELINE_LEVEL_TO_DIFFICULTY[1]).toBeLessThan(BASELINE_LEVEL_TO_DIFFICULTY[2]);
      expect(BASELINE_LEVEL_TO_DIFFICULTY[2]).toBeLessThan(BASELINE_LEVEL_TO_DIFFICULTY[3]);
    });
  });

  describe('MAX_ROUNDS', () => {
    it('is a positive integer', () => {
      expect(MAX_ROUNDS).toBeGreaterThan(0);
      expect(Number.isInteger(MAX_ROUNDS)).toBe(true);
    });

    it('equals 10', () => {
      expect(MAX_ROUNDS).toBe(10);
    });
  });

  describe('INITIAL_LEVEL', () => {
    it('equals 1', () => {
      expect(INITIAL_LEVEL).toBe(1);
    });

    it('is within the valid level range 1-3', () => {
      expect(INITIAL_LEVEL).toBeGreaterThanOrEqual(1);
      expect(INITIAL_LEVEL).toBeLessThanOrEqual(3);
    });
  });
});
