import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useStreakData } from './useStreakData';
import { progressAPI } from '../api/client';

vi.mock('../api/client', () => ({
  progressAPI: {
    getStreakHistory: vi.fn(),
  },
}));

describe('useStreakData', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('starts with loading=true, streakData=null, error=null', () => {
    progressAPI.getStreakHistory.mockReturnValue(new Promise(() => {}));
    const { result } = renderHook(() => useStreakData());
    expect(result.current.loading).toBe(true);
    expect(result.current.streakData).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('sets streakData from response.data on success', async () => {
    const mockData = { current_streak: 5, longest_streak: 10, history: [] };
    progressAPI.getStreakHistory.mockResolvedValue({ data: mockData });

    const { result } = renderHook(() => useStreakData());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.streakData).toEqual(mockData);
    expect(result.current.error).toBeNull();
  });

  it('sets error from err.response.data.detail if available', async () => {
    const err = { response: { data: { detail: 'Unauthorized' } }, message: 'Request failed' };
    progressAPI.getStreakHistory.mockRejectedValue(err);

    const { result } = renderHook(() => useStreakData());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('Unauthorized');
    expect(result.current.streakData).toBeNull();
  });

  it('falls back to err.message when response detail is absent', async () => {
    const err = new Error('Network error');
    progressAPI.getStreakHistory.mockRejectedValue(err);

    const { result } = renderHook(() => useStreakData());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('Network error');
  });

  it('uses fallback message when both detail and message are absent', async () => {
    progressAPI.getStreakHistory.mockRejectedValue({});

    const { result } = renderHook(() => useStreakData());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('Failed to fetch streak data');
  });

  it('sets loading=false after success', async () => {
    progressAPI.getStreakHistory.mockResolvedValue({ data: {} });

    const { result } = renderHook(() => useStreakData());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.loading).toBe(false);
  });

  it('sets loading=false after error', async () => {
    progressAPI.getStreakHistory.mockRejectedValue(new Error('fail'));

    const { result } = renderHook(() => useStreakData());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.loading).toBe(false);
  });

  it('calls progressAPI.getStreakHistory once on mount', async () => {
    progressAPI.getStreakHistory.mockResolvedValue({ data: {} });

    renderHook(() => useStreakData());

    await waitFor(() => expect(progressAPI.getStreakHistory).toHaveBeenCalledTimes(1));
  });
});
