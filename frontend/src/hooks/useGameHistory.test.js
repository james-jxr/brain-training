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
    sessionStorage.clear();
  });

  afterEach(() => {
    sessionStorage.clear();
  });

  it('starts with loading=true and gameHistory=null', () => {
    progressAPI.getGameHistory.mockReturnValue(new Promise(() => {}));
    const { result } = renderHook(() => useGameHistory());
    expect(result.current.loading).toBe(true);
    expect(result.current.gameHistory).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('sets gameHistory from API response on success', async () => {
    const mockGames = [
      { id: 1, domain: 'attention', score: 80 },
      { id: 2, domain: 'working_memory', score: 70 },
    ];
    progressAPI.getGameHistory.mockResolvedValue({
      data: { games: mockGames },
    });

    const { result } = renderHook(() => useGameHistory());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.gameHistory).toEqual(mockGames);
    expect(result.current.error).toBeNull();
  });

  it('passes the access_token from sessionStorage to the API', async () => {
    sessionStorage.setItem('access_token', 'test-token-123');
    progressAPI.getGameHistory.mockResolvedValue({
      data: { games: [] },
    });

    const { result } = renderHook(() => useGameHistory());
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(progressAPI.getGameHistory).toHaveBeenCalledWith('test-token-123');
  });

  it('passes null token when sessionStorage has no access_token', async () => {
    progressAPI.getGameHistory.mockResolvedValue({
      data: { games: [] },
    });

    const { result } = renderHook(() => useGameHistory());
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(progressAPI.getGameHistory).toHaveBeenCalledWith(null);
  });

  it('sets error and leaves gameHistory null on API failure', async () => {
    progressAPI.getGameHistory.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useGameHistory());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('Network error');
    expect(result.current.gameHistory).toBeNull();
  });

  it('sets loading=false after success', async () => {
    progressAPI.getGameHistory.mockResolvedValue({
      data: { games: [] },
    });

    const { result } = renderHook(() => useGameHistory());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.loading).toBe(false);
  });

  it('sets loading=false after failure', async () => {
    progressAPI.getGameHistory.mockRejectedValue(new Error('fail'));

    const { result } = renderHook(() => useGameHistory());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.loading).toBe(false);
  });

  it('returns empty array when API returns empty games list', async () => {
    progressAPI.getGameHistory.mockResolvedValue({
      data: { games: [] },
    });

    const { result } = renderHook(() => useGameHistory());
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.gameHistory).toEqual([]);
  });
});
