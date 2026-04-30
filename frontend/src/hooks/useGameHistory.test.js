import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useGameHistory } from './useGameHistory';

vi.mock('../api/client', () => ({
  progressAPI: {
    getGameHistory: vi.fn(),
  },
}));

import { progressAPI } from '../api/client';

describe('useGameHistory', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('starts with loading=true and null gameHistory', () => {
    progressAPI.getGameHistory.mockReturnValue(new Promise(() => {}));
    const { result } = renderHook(() => useGameHistory());
    expect(result.current.loading).toBe(true);
    expect(result.current.gameHistory).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('sets gameHistory on successful fetch', async () => {
    const mockGames = [
      { game_key: 'nback', score: 80 },
      { game_key: 'stroop', score: 70 },
    ];
    progressAPI.getGameHistory.mockResolvedValueOnce({
      data: { games: mockGames },
    });

    const { result } = renderHook(() => useGameHistory());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.gameHistory).toEqual(mockGames);
    expect(result.current.error).toBeNull();
  });

  it('sets error on failed fetch', async () => {
    progressAPI.getGameHistory.mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => useGameHistory());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.gameHistory).toBeNull();
    expect(result.current.error).toBe('Network error');
  });

  it('sets loading=false after successful fetch', async () => {
    progressAPI.getGameHistory.mockResolvedValueOnce({
      data: { games: [] },
    });

    const { result } = renderHook(() => useGameHistory());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.loading).toBe(false);
  });

  it('handles empty games array', async () => {
    progressAPI.getGameHistory.mockResolvedValueOnce({
      data: { games: [] },
    });

    const { result } = renderHook(() => useGameHistory());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.gameHistory).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it('calls progressAPI.getGameHistory once on mount', async () => {
    progressAPI.getGameHistory.mockResolvedValueOnce({
      data: { games: [] },
    });

    renderHook(() => useGameHistory());

    await waitFor(() => expect(progressAPI.getGameHistory).toHaveBeenCalledTimes(1));
  });
});
