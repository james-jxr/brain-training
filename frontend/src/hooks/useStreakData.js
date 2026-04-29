import { useState, useEffect } from 'react';
import { progressAPI } from '../api/client';

export function useStreakData() {
  const [streakData, setStreakData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchStreak() {
      try {
        setLoading(true);
        const response = await progressAPI.getStreakHistory();

        if (!cancelled) {
          setStreakData(response.data);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.response?.data?.detail || err.message || 'Failed to fetch streak data');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchStreak();

    return () => {
      cancelled = true;
    };
  }, []);

  return { streakData, loading, error };
}
