import { describe, it, expect } from 'vitest';
import { computeStroopResult } from '../components/exercises/Stroop';

describe('computeStroopResult', () => {
  it('returns correct trials_presented', () => {
    const r = computeStroopResult({ trialsPresented: 8, trialsCorrect: 6, responseTimes: [300, 400] });
    expect(r.trials_presented).toBe(8);
  });

  it('returns correct trials_correct', () => {
    const r = computeStroopResult({ trialsPresented: 8, trialsCorrect: 6, responseTimes: [300, 400] });
    expect(r.trials_correct).toBe(6);
  });

  it('avg_response_ms is mean of response times', () => {
    const r = computeStroopResult({ trialsPresented: 8, trialsCorrect: 6, responseTimes: [200, 400] });
    expect(r.avg_response_ms).toBe(300);
  });

  it('avg_response_ms is 0 when no response times', () => {
    const r = computeStroopResult({ trialsPresented: 8, trialsCorrect: 0, responseTimes: [] });
    expect(r.avg_response_ms).toBe(0);
  });

  it('avg_response_ms is non-negative', () => {
    const r = computeStroopResult({ trialsPresented: 5, trialsCorrect: 3, responseTimes: [100, 200, 300] });
    expect(r.avg_response_ms).toBeGreaterThanOrEqual(0);
  });

  it('perfect session: all 8 correct', () => {
    const r = computeStroopResult({ trialsPresented: 8, trialsCorrect: 8, responseTimes: [300, 320, 340, 360, 310, 290, 330, 350] });
    expect(r.trials_correct).toBe(8);
    expect(r.trials_presented).toBe(8);
  });

  it('zero correct session', () => {
    const r = computeStroopResult({ trialsPresented: 8, trialsCorrect: 0, responseTimes: [500, 600, 700, 800, 900, 1000, 1100, 1200] });
    expect(r.trials_correct).toBe(0);
    expect(r.avg_response_ms).toBe(850);
  });
});
