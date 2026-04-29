import { useState, useEffect } from 'react';
import { progressAPI } from '../api/client';

export function useGameHistory() {
  const [gameHistory, setGameHistory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchGameHistory = async () => {
      try {
        setLoading(true);
        setError(null);
        const gameHistoryResponse = await progressAPI.getGameHistory();
        setGameHistory(gameHistoryResponse.data.games);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchGameHistory();
  }, []);

  return { gameHistory, loading, error };
}
