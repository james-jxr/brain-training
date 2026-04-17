import { useState, useEffect, useCallback } from 'react';
import { progressAPI, lifestyleAPI } from '../api/client';

export const useDashboard = () => {
  const [summary, setSummary] = useState(null);
  const [brainHealth, setBrainHealth] = useState(null);
  const [streak, setStreak] = useState(null);
  const [lifestyle, setLifestyle] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [summaryRes, healthRes, streakRes, lifestyleRes] = await Promise.all([
        progressAPI.getProgressSummary(),
        progressAPI.getBrainHealthScore(),
        progressAPI.getStreak(),
        lifestyleAPI.getTodayLifestyle().catch(() => null),
      ]);

      setSummary(summaryRes.data);
      setBrainHealth(healthRes.data);
      setStreak(streakRes.data);
      if (lifestyleRes) {
        setLifestyle(lifestyleRes.data);
      }
    } catch (err) {
      const message = err.response?.data?.detail?.message || 'Failed to load dashboard';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  const getDomainTrend = useCallback(async (domain) => {
    try {
      setError(null);
      const response = await progressAPI.getDomainTrend(domain);
      return response.data;
    } catch (err) {
      const message = err.response?.data?.detail?.message || 'Failed to load trend';
      setError(message);
      throw err;
    }
  }, []);

  const logLifestyle = useCallback(async (data) => {
    try {
      setError(null);
      const response = await lifestyleAPI.logLifestyle(data);
      setLifestyle(response.data);
      return response.data;
    } catch (err) {
      const message = err.response?.data?.detail?.message || 'Failed to log lifestyle';
      setError(message);
      throw err;
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  return {
    summary,
    brainHealth,
    streak,
    lifestyle,
    loading,
    error,
    loadDashboard,
    getDomainTrend,
    logLifestyle,
  };
};
