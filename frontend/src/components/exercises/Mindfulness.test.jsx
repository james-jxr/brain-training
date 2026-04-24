import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import Mindfulness, { getPhaseForTime, getCycleNumber, isSessionComplete } from './Mindfulness';

describe('Mindfulness pure functions', () => {
  it('getPhaseForTime returns inhale for start of cycle', () => {
    const phase = getPhaseForTime(0);
    expect(phase.key).toBe('inhale');
    expect(phase.label).toBe('Breathe in...');
  });

  it('getPhaseForTime returns hold after 4 seconds', () => {
    const phase = getPhaseForTime(4000);
    expect(phase.key).toBe('hold');
    expect(phase.label).toBe('Hold...');
  });

  it('getPhaseForTime returns exhale after 8 seconds', () => {
    const phase = getPhaseForTime(8000);
    expect(phase.key).toBe('exhale');
    expect(phase.label).toBe('Breathe out...');
  });

  it('getPhaseForTime wraps to next cycle at 12 seconds', () => {
    const phase = getPhaseForTime(12000);
    expect(phase.key).toBe('inhale');
  });

  it('getCycleNumber returns 1 for start', () => {
    expect(getCycleNumber(0)).toBe(1);
  });

  it('getCycleNumber returns 2 for second cycle', () => {
    expect(getCycleNumber(12000)).toBe(2);
  });

  it('isSessionComplete returns false at start', () => {
    expect(isSessionComplete(0)).toBe(false);
  });

  it('isSessionComplete returns true at end of all cycles', () => {
    // 10 cycles * 12 seconds = 120000ms
    expect(isSessionComplete(120000)).toBe(true);
  });

  it('isSessionComplete returns false before all cycles', () => {
    expect(isSessionComplete(119999)).toBe(false);
  });
});

describe('Mindfulness component', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders intro screen with Begin button', () => {
    const onComplete = vi.fn();
    render(<Mindfulness onComplete={onComplete} />);

    expect(screen.getByText('Guided Breathing')).toBeInTheDocument();
    expect(screen.getByTestId('mindfulness-start')).toBeInTheDocument();
    expect(screen.getByText('Begin')).toBeInTheDocument();
  });

  it('transitions to breathing screen on Begin click', () => {
    const onComplete = vi.fn();
    render(<Mindfulness onComplete={onComplete} />);

    fireEvent.click(screen.getByTestId('mindfulness-start'));

    expect(screen.getByTestId('breathing-cue')).toBeInTheDocument();
    expect(screen.getByTestId('breathing-circle')).toBeInTheDocument();
  });

  it('calls onComplete with result when Finish is clicked', () => {
    const onComplete = vi.fn();
    render(<Mindfulness onComplete={onComplete} />);

    // Start the exercise
    fireEvent.click(screen.getByTestId('mindfulness-start'));

    // Fast-forward past full session duration
    const now = Date.now();
    vi.spyOn(Date, 'now').mockReturnValue(now + 120001);

    // Trigger a tick
    act(() => {
      vi.advanceTimersByTime(100);
    });

    // Should see completion screen
    expect(screen.getByText('Well done')).toBeInTheDocument();

    // Select a rating
    fireEvent.click(screen.getByTestId('rating-3'));

    // Click finish
    fireEvent.click(screen.getByTestId('mindfulness-finish'));

    expect(onComplete).toHaveBeenCalledTimes(1);
    const result = onComplete.mock.calls[0][0];
    expect(result.completed).toBe(true);
    expect(result.feeling_rating).toBe(3);
    expect(result.exercise_type).toBe('mindfulness');
  });

  it('allows finishing without selecting a rating', () => {
    const onComplete = vi.fn();
    render(<Mindfulness onComplete={onComplete} />);

    fireEvent.click(screen.getByTestId('mindfulness-start'));

    const now = Date.now();
    vi.spyOn(Date, 'now').mockReturnValue(now + 120001);
    act(() => {
      vi.advanceTimersByTime(100);
    });

    fireEvent.click(screen.getByTestId('mindfulness-finish'));

    expect(onComplete).toHaveBeenCalledTimes(1);
    const result = onComplete.mock.calls[0][0];
    expect(result.feeling_rating).toBeNull();
  });
});
