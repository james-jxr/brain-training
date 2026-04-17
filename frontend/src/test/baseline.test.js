import { describe, it, expect } from 'vitest';
import { applyAdaptiveStep } from '../components/baseline/BaselineGameWrapper';

const init = (level = 1) => ({ level, consecutiveCorrect: 0 });

describe('applyAdaptiveStep — 2-up/1-down adaptive algorithm', () => {

  // ── Level increases ────────────────────────────────────────────────────────

  it('one correct does not increase level', () => {
    const s = applyAdaptiveStep(init(1), true);
    expect(s.level).toBe(1);
    expect(s.consecutiveCorrect).toBe(1);
  });

  it('two consecutive corrects increases level', () => {
    let s = applyAdaptiveStep(init(1), true);
    s = applyAdaptiveStep(s, true);
    expect(s.level).toBe(2);
    expect(s.consecutiveCorrect).toBe(0);
  });

  it('counter resets to 0 after level-up', () => {
    let s = applyAdaptiveStep(init(1), true);
    s = applyAdaptiveStep(s, true); // level → 2, counter reset
    s = applyAdaptiveStep(s, true); // counter = 1, not a level-up yet
    expect(s.level).toBe(2);
    expect(s.consecutiveCorrect).toBe(1);
  });

  // ── Level decreases ────────────────────────────────────────────────────────

  it('one incorrect decreases level immediately', () => {
    const s = applyAdaptiveStep(init(2), false);
    expect(s.level).toBe(1);
    expect(s.consecutiveCorrect).toBe(0);
  });

  it('incorrect resets consecutive correct counter', () => {
    let s = applyAdaptiveStep(init(1), true);  // counter = 1
    s = applyAdaptiveStep(s, false);            // counter reset
    expect(s.consecutiveCorrect).toBe(0);
  });

  it('after an error, two corrects are required to step back up', () => {
    let s = applyAdaptiveStep(init(2), false);  // → level 1
    s = applyAdaptiveStep(s, true);              // counter = 1, still level 1
    expect(s.level).toBe(1);
    s = applyAdaptiveStep(s, true);              // counter = 2 → level up
    expect(s.level).toBe(2);
  });

  // ── Floor and ceiling ──────────────────────────────────────────────────────

  it('floor: cannot go below level 1', () => {
    const s = applyAdaptiveStep(init(1), false);
    expect(s.level).toBe(1);
  });

  it('ceiling: cannot go above level 3', () => {
    let s = init(3);
    s = applyAdaptiveStep(s, true);
    s = applyAdaptiveStep(s, true);
    expect(s.level).toBe(3);
  });

  // ── Convergence ────────────────────────────────────────────────────────────

  it('all correct converges to ceiling (level 3)', () => {
    let s = init(1);
    for (let i = 0; i < 20; i++) s = applyAdaptiveStep(s, true);
    expect(s.level).toBe(3);
  });

  it('all incorrect stays at floor (level 1)', () => {
    let s = init(2);
    for (let i = 0; i < 20; i++) s = applyAdaptiveStep(s, false);
    expect(s.level).toBe(1);
  });

  it('alternating correct/incorrect never reaches ceiling', () => {
    let s = init(1);
    for (let i = 0; i < 20; i++) s = applyAdaptiveStep(s, i % 2 === 0);
    expect(s.level).toBeLessThanOrEqual(2);
  });
});
