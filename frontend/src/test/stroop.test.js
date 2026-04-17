import { describe, it, expect } from 'vitest';
import { computeStroopResult } from '../components/exercises/Stroop';

describe('computeStroopResult', () => {
  it('returns zero avgResponseMs when responseTimes is empty', () => {
    const result = computeStroopResult({
      trialsPresented: 0,
      trialsCorrect: 0,
      responseTimes: [],
    });
    expect(result.avg_response_ms).toBe(0);
    expect(result.trials_presented).toBe(0);
    expect(result.trials_correct).toBe(0);
  });

  it('calculates average response time correctly', () => {
    const result = computeStroopResult({
      trialsPresented: 3,
      trialsCorrect: 2,
      responseTimes: [100, 200, 300],
    });
    expect(result.avg_response_ms).toBe(200);
  });

  it('passes through trials_presented and trials_correct', () => {
    const result = computeStroopResult({
      trialsPresented: 8,
      trialsCorrect: 6,
      responseTimes: [500],
    });
    expect(result.trials_presented).toBe(8);
    expect(result.trials_correct).toBe(6);
  });

  it('handles single response time', () => {
    const result = computeStroopResult({
      trialsPresented: 1,
      trialsCorrect: 1,
      responseTimes: [450],
    });
    expect(result.avg_response_ms).toBe(450);
  });

  it('handles all incorrect trials', () => {
    const result = computeStroopResult({
      trialsPresented: 4,
      trialsCorrect: 0,
      responseTimes: [200, 400],
    });
    expect(result.trials_correct).toBe(0);
    expect(result.avg_response_ms).toBe(300);
  });

  it('returns correct shape of result object', () => {
    const result = computeStroopResult({
      trialsPresented: 5,
      trialsCorrect: 3,
      responseTimes: [100, 200],
    });
    expect(result).toHaveProperty('trials_presented');
    expect(result).toHaveProperty('trials_correct');
    expect(result).toHaveProperty('avg_response_ms');
  });

  it('computes average over many response times', () => {
    const times = [100, 200, 300, 400, 500, 600, 700, 800];
    const result = computeStroopResult({
      trialsPresented: 8,
      trialsCorrect: 8,
      responseTimes: times,
    });
    expect(result.avg_response_ms).toBe(450);
  });
});
