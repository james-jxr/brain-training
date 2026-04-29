import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useGameHistory } from './useGameHistory';
import { progressAPI } from '../api/client';

vi.mock('../api/client', () => ({
  progressAPI: {
    getGameHistory: vi.fn(),
  },
}));

describe('useGameHistory', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('starts with loading=true and gameHistory=null', () => {
    progressAPI.getGameHistory.mockReturnValue(new Promise(() => {}));
    const { result } = renderHook(() => useGameHistory());
    expect(result.current.loading).toBe(true);
    expect(result.current.gameHistory).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('sets gameHistory from response.data.games on success', async () => {
    const mockGames = [
      { game_key: 'nback', score: 80, played_at: '2024-01-01' },
      { game_key: 'stroop', score: 70, played_at: '2024-01-02' },
    ];
    progressAPI.getGameHistory.mockResolvedValue({ data: { games: mockGames } });

    const { result } = renderHook(() => useGameHistory());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.gameHistory).toEqual(mockGames);
    expect(result.current.error).toBeNull();
  });

  it('sets error message on failure', async () => {
    progressAPI.getGameHistory.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useGameHistory());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.gameHistory).toBeNull();
    expect(result.current.error).toBe('Network error');
  });

  it('sets loading=false after success', async () => {
    progressAPI.getGameHistory.mockResolvedValue({ data: { games: [] } });

    const { result } = renderHook(() => useGameHistory());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.loading).toBe(false);
  });

  it('sets loading=false after error', async () => {
    progressAPI.getGameHistory.mockRejectedValue(new Error('fail'));

    const { result } = renderHook(() => useGameHistory());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.loading).toBe(false);
  });

  it('handles empty games array', async () => {
    progressAPI.getGameHistory.mockResolvedValue({ data: { games: [] } });

    const { result } = renderHook(() => useGameHistory());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.gameHistory).toEqual([]);
  });

  it('calls progressAPI.getGameHistory once on mount', async () => {
    progressAPI.getGameHistory.mockResolvedValue({ data: { games: [] } });

    renderHook(() => useGameHistory());

    await waitFor(() => expect(progressAPI.getGameHistory).toHaveBeenCalledTimes(1));
  });
});
