import { useState, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || '';

export function useGameHistory() {
  const [gameHistory, setGameHistory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchGameHistory = async () => {
      try {
        setLoading(true);
        setError(null);
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE}/api/progress/game-history`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch game history: ${response.status}`);
        }

        const data = await response.json();
        setGameHistory(data.games);
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
