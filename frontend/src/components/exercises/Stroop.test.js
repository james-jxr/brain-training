import { describe, it, expect } from 'vitest';
import { computeStroopResult } from './Stroop';

describe('computeStroopResult', () => {
  it('returns correct structure', () => {
    const result = computeStroopResult({
      trialsPresented: 8,
      trialsCorrect: 6,
      responseTimes: [500, 600, 700],
    });
    expect(result).toHaveProperty('trials_presented', 8);
    expect(result).toHaveProperty('trials_correct', 6);
    expect(result).toHaveProperty('avg_response_ms');
  });

  it('computes average response time correctly', () => {
    const result = computeStroopResult({
      trialsPresented: 3,
      trialsCorrect: 3,
      responseTimes: [300, 600, 900],
    });
    expect(result.avg_response_ms).toBe(600);
  });

  it('returns 0 avg_response_ms for empty responseTimes', () => {
    const result = computeStroopResult({
      trialsPresented: 0,
      trialsCorrect: 0,
      responseTimes: [],
    });
    expect(result.avg_response_ms).toBe(0);
  });

  it('handles single response time', () => {
    const result = computeStroopResult({
      trialsPresented: 1,
      trialsCorrect: 1,
      responseTimes: [450],
    });
    expect(result.avg_response_ms).toBe(450);
  });

  it('handles all incorrect (0 correct)', () => {
    const result = computeStroopResult({
      trialsPresented: 8,
      trialsCorrect: 0,
      responseTimes: [400, 500],
    });
    expect(result.trials_correct).toBe(0);
    expect(result.trials_presented).toBe(8);
  });

  it('handles perfect score', () => {
    const result = computeStroopResult({
      trialsPresented: 8,
      trialsCorrect: 8,
      responseTimes: [200, 200, 200, 200, 200, 200, 200, 200],
    });
    expect(result.trials_correct).toBe(8);
    expect(result.avg_response_ms).toBe(200);
  });

  it('does not mutate the input responseTimes array', () => {
    const times = [100, 200, 300];
    computeStroopResult({ trialsPresented: 3, trialsCorrect: 2, responseTimes: times });
    expect(times).toEqual([100, 200, 300]);
  });
});
