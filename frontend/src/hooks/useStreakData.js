import { useState, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || '';

export function useStreakData() {
  const [streakData, setStreakData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchStreak() {
      try {
        setLoading(true);
        const token = localStorage.getItem('token');
        const headers = {};
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_BASE}/api/progress/streak/history`, { headers });

        if (!response.ok) {
          throw new Error(`Failed to fetch streak data: ${response.status}`);
        }

        const data = await response.json();

        if (!cancelled) {
          setStreakData(data);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
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
