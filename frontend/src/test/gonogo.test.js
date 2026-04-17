import { describe, it, expect } from 'vitest';
import { computeResult } from '../components/exercises/GoNoGo';

describe('computeResult — GoNoGo scoring', () => {

  it('perfect score: all hits, no false alarms', () => {
    const result = computeResult({
      hits: 10, misses: 0, falseAlarms: 0, correctRejections: 5, responseTimes: [300, 350],
    });
    expect(result.accuracy).toBe(1.0);
    expect(result.trials_presented).toBe(15);
    expect(result.trials_correct).toBe(15);
  });

  it('zero score: all misses and false alarms', () => {
    const result = computeResult({
      hits: 0, misses: 10, falseAlarms: 5, correctRejections: 0, responseTimes: [],
    });
    expect(result.accuracy).toBe(0);
  });

  it('accuracy is clamped to 0 (no negative values)', () => {
    const result = computeResult({
      hits: 0, misses: 5, falseAlarms: 10, correctRejections: 0, responseTimes: [],
    });
    expect(result.accuracy).toBeGreaterThanOrEqual(0);
  });

  it('avg_response_ms is 0 when no response times recorded', () => {
    const result = computeResult({
      hits: 5, misses: 0, falseAlarms: 0, correctRejections: 0, responseTimes: [],
    });
    expect(result.avg_response_ms).toBe(0);
  });

  it('avg_response_ms is mean of response times', () => {
    const result = computeResult({
      hits: 2, misses: 0, falseAlarms: 0, correctRejections: 0,
      responseTimes: [200, 400],
    });
    expect(result.avg_response_ms).toBe(300);
  });

  it('trials_correct = hits + correctRejections', () => {
    const result = computeResult({
      hits: 7, misses: 1, falseAlarms: 2, correctRejections: 3, responseTimes: [],
    });
    expect(result.trials_correct).toBe(10); // 7 + 3
  });

  it('trials_presented = hits + misses + falseAlarms + correctRejections', () => {
    const result = computeResult({
      hits: 5, misses: 2, falseAlarms: 1, correctRejections: 4, responseTimes: [],
    });
    expect(result.trials_presented).toBe(12);
  });

  it('result includes false_alarms and correct_rejections fields', () => {
    const result = computeResult({
      hits: 5, misses: 1, falseAlarms: 2, correctRejections: 3, responseTimes: [],
    });
    expect(result.false_alarms).toBe(2);
    expect(result.correct_rejections).toBe(3);
  });
});
