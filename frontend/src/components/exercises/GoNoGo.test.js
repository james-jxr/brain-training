import { describe, it, expect } from 'vitest';
import { generateStimuli, computeResult } from './GoNoGo.jsx';

// ─── generateStimuli ──────────────────────────────────────────────────────────

describe('generateStimuli', () => {
  it('returns exactly 20 stimuli', () => {
    const result = generateStimuli({ noGoCount: 1, goRatio: 0.75 });
    expect(result).toHaveLength(20);
  });

  it('each stimulus has required fields', () => {
    const result = generateStimuli({ noGoCount: 1, goRatio: 0.75 });
    for (const s of result) {
      expect(s).toHaveProperty('shape');
      expect(s).toHaveProperty('colorVar');
      expect(s).toHaveProperty('label');
      expect(s).toHaveProperty('isGo');
    }
  });

  it('Easy config: ~75% go stimuli (15 go, 5 no-go)', () => {
    const result = generateStimuli({ noGoCount: 1, goRatio: 0.75 });
    const goCount = result.filter(s => s.isGo).length;
    expect(goCount).toBe(15);
    expect(result.filter(s => !s.isGo)).toHaveLength(5);
  });

  it('Medium config: ~70% go stimuli (14 go, 6 no-go)', () => {
    const result = generateStimuli({ noGoCount: 2, goRatio: 0.70 });
    const goCount = result.filter(s => s.isGo).length;
    expect(goCount).toBe(14);
    expect(result.filter(s => !s.isGo)).toHaveLength(6);
  });

  it('Hard config: ~65% go stimuli (13 go, 7 no-go)', () => {
    const result = generateStimuli({ noGoCount: 3, goRatio: 0.65 });
    const goCount = result.filter(s => s.isGo).length;
    expect(goCount).toBe(13);
    expect(result.filter(s => !s.isGo)).toHaveLength(7);
  });

  it('Easy (noGoCount=1): only one no-go variant', () => {
    const result = generateStimuli({ noGoCount: 1, goRatio: 0.75 });
    const noGoLabels = new Set(result.filter(s => !s.isGo).map(s => s.label));
    expect(noGoLabels.size).toBe(1);
  });

  it('Medium (noGoCount=2): at most two no-go variants', () => {
    const result = generateStimuli({ noGoCount: 2, goRatio: 0.70 });
    const noGoLabels = new Set(result.filter(s => !s.isGo).map(s => s.label));
    expect(noGoLabels.size).toBeLessThanOrEqual(2);
  });

  it('Hard (noGoCount=3): up to three no-go variants', () => {
    const result = generateStimuli({ noGoCount: 3, goRatio: 0.65 });
    const noGoLabels = new Set(result.filter(s => !s.isGo).map(s => s.label));
    expect(noGoLabels.size).toBeLessThanOrEqual(3);
  });

  it('go stimuli are green circles', () => {
    const result = generateStimuli({ noGoCount: 1, goRatio: 1.0 });
    for (const s of result) {
      expect(s.shape).toBe('circle');
      expect(s.colorVar).toBe('--color-success');
      expect(s.isGo).toBe(true);
    }
  });

  it('produces different orderings (shuffle works)', () => {
    // run 10 times and check at least two are different
    const sequences = Array.from({ length: 10 }, () =>
      generateStimuli({ noGoCount: 2, goRatio: 0.70 }).map(s => s.isGo ? 'G' : 'N').join('')
    );
    const unique = new Set(sequences);
    // Very unlikely all 10 shuffles produce identical sequences
    expect(unique.size).toBeGreaterThan(1);
  });
});

// ─── computeResult ────────────────────────────────────────────────────────────

describe('computeResult', () => {
  it('perfect score: all hits and correct rejections', () => {
    const result = computeResult({
      hits: 15,
      misses: 0,
      falseAlarms: 0,
      correctRejections: 5,
      responseTimes: [200, 250, 300, 180, 220, 190, 210, 230, 240, 205, 215, 225, 195, 185, 235],
    });
    expect(result.trials_presented).toBe(20);
    expect(result.trials_correct).toBe(20);
    expect(result.accuracy).toBe(1);
    expect(result.hits).toBe(15);
    expect(result.misses).toBe(0);
    expect(result.false_alarms).toBe(0);
    expect(result.correct_rejections).toBe(5);
    expect(result.avg_response_ms).toBeGreaterThan(0);
  });

  it('zero input: all zeros', () => {
    const result = computeResult({
      hits: 0,
      misses: 0,
      falseAlarms: 0,
      correctRejections: 0,
      responseTimes: [],
    });
    expect(result.trials_presented).toBe(0);
    expect(result.trials_correct).toBe(0);
    expect(result.accuracy).toBe(0);
    expect(result.avg_response_ms).toBe(0);
  });

  it('all misses: accuracy is 0', () => {
    const result = computeResult({
      hits: 0,
      misses: 15,
      falseAlarms: 0,
      correctRejections: 5,
      responseTimes: [],
    });
    // rawScore = 0 + 5 - 0 - 15 = -10 => max(0,-10)=0
    expect(result.accuracy).toBe(0);
    expect(result.trials_presented).toBe(20);
  });

  it('all false alarms: accuracy clamped to 0', () => {
    const result = computeResult({
      hits: 0,
      misses: 15,
      falseAlarms: 5,
      correctRejections: 0,
      responseTimes: [],
    });
    expect(result.accuracy).toBe(0);
  });

  it('mixed performance: correct formula', () => {
    // hits=10, misses=5, falseAlarms=2, correctRejections=3
    // total=20, rawScore=10+3-2-5=6, accuracy=6/20=0.3, trialsCorrect=13
    const result = computeResult({
      hits: 10,
      misses: 5,
      falseAlarms: 2,
      correctRejections: 3,
      responseTimes: [200, 300, 250],
    });
    expect(result.trials_presented).toBe(20);
    expect(result.trials_correct).toBe(13);
    expect(result.accuracy).toBeCloseTo(0.3);
    expect(result.hits).toBe(10);
    expect(result.misses).toBe(5);
    expect(result.false_alarms).toBe(2);
    expect(result.correct_rejections).toBe(3);
  });

  it('avg_response_ms is rounded average of responseTimes', () => {
    const result = computeResult({
      hits: 3,
      misses: 0,
      falseAlarms: 0,
      correctRejections: 0,
      responseTimes: [100, 200, 300],
    });
    expect(result.avg_response_ms).toBe(200);
  });

  it('avg_response_ms is 0 when no response times', () => {
    const result = computeResult({
      hits: 0,
      misses: 20,
      falseAlarms: 0,
      correctRejections: 0,
      responseTimes: [],
    });
    expect(result.avg_response_ms).toBe(0);
  });

  it('accuracy is clamped to 0, never negative', () => {
    const result = computeResult({
      hits: 0,
      misses: 10,
      falseAlarms: 10,
      correctRejections: 0,
      responseTimes: [],
    });
    expect(result.accuracy).toBeGreaterThanOrEqual(0);
  });

  it('payload has all required fields for onComplete', () => {
    const result = computeResult({
      hits: 5,
      misses: 5,
      falseAlarms: 5,
      correctRejections: 5,
      responseTimes: [250],
    });
    expect(result).toHaveProperty('trials_presented');
    expect(result).toHaveProperty('trials_correct');
    expect(result).toHaveProperty('avg_response_ms');
    expect(result).toHaveProperty('accuracy');
    expect(result).toHaveProperty('hits');
    expect(result).toHaveProperty('misses');
    expect(result).toHaveProperty('false_alarms');
    expect(result).toHaveProperty('correct_rejections');
  });

  it('accuracy is between 0 and 1', () => {
    const result = computeResult({
      hits: 15,
      misses: 2,
      falseAlarms: 1,
      correctRejections: 2,
      responseTimes: [200],
    });
    expect(result.accuracy).toBeGreaterThanOrEqual(0);
    expect(result.accuracy).toBeLessThanOrEqual(1);
  });
});
