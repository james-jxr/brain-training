import { describe, it, expect } from 'vitest';
import { applyAdaptiveStep } from './BaselineGameWrapper';

describe('applyAdaptiveStep', () => {
  const initialState = (level = 1) => ({ level, consecutiveCorrect: 0 });

  describe('correct answers', () => {
    it('one correct answer does not increase level', () => {
      const state = applyAdaptiveStep(initialState(1), true);
      expect(state.level).toBe(1);
      expect(state.consecutiveCorrect).toBe(1);
    });

    it('two consecutive correct answers increase level by 1', () => {
      let s = applyAdaptiveStep(initialState(1), true);
      s = applyAdaptiveStep(s, true);
      expect(s.level).toBe(2);
      expect(s.consecutiveCorrect).toBe(0);
    });

    it('counter resets after level up', () => {
      let s = applyAdaptiveStep(initialState(1), true);
      s = applyAdaptiveStep(s, true); // level up to 2
      s = applyAdaptiveStep(s, true); // one more correct
      expect(s.level).toBe(2);
      expect(s.consecutiveCorrect).toBe(1);
    });

    it('two more correct after level up increases level again', () => {
      let s = initialState(2);
      s = applyAdaptiveStep(s, true);
      s = applyAdaptiveStep(s, true);
      expect(s.level).toBe(3);
    });

    it('all correct answers converge to ceiling (level 3)', () => {
      let s = initialState(1);
      for (let i = 0; i < 20; i++) {
        s = applyAdaptiveStep(s, true);
      }
      expect(s.level).toBe(3);
    });
  });

  describe('incorrect answers', () => {
    it('one incorrect answer decreases level by 1', () => {
      const s = applyAdaptiveStep(initialState(2), false);
      expect(s.level).toBe(1);
      expect(s.consecutiveCorrect).toBe(0);
    });

    it('incorrect answer resets consecutive counter', () => {
      let s = applyAdaptiveStep(initialState(1), true); // consecutiveCorrect = 1
      s = applyAdaptiveStep(s, false);
      expect(s.consecutiveCorrect).toBe(0);
    });

    it('incorrect then two correct steps up again', () => {
      let s = initialState(2);
      s = applyAdaptiveStep(s, false); // level 1
      s = applyAdaptiveStep(s, true);
      expect(s.level).toBe(1);
      s = applyAdaptiveStep(s, true); // level 2
      expect(s.level).toBe(2);
    });

    it('all incorrect stays at floor (level 1)', () => {
      let s = initialState(2);
      for (let i = 0; i < 20; i++) {
        s = applyAdaptiveStep(s, false);
      }
      expect(s.level).toBe(1);
    });
  });

  describe('boundary conditions', () => {
    it('does not go below floor (level 1)', () => {
      const s = applyAdaptiveStep(initialState(1), false);
      expect(s.level).toBe(1);
    });

    it('does not exceed ceiling (level 3)', () => {
      let s = initialState(3);
      s = applyAdaptiveStep(s, true);
      s = applyAdaptiveStep(s, true);
      expect(s.level).toBe(3);
    });

    it('alternating correct/incorrect keeps level low', () => {
      let s = initialState(1);
      for (let i = 0; i < 20; i++) {
        s = applyAdaptiveStep(s, i % 2 === 0);
      }
      expect(s.level).toBeLessThanOrEqual(2);
    });
  });
});
