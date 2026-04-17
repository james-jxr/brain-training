import { useState, useCallback } from 'react';
import { sessionAPI } from '../api/client';

export const useSession = () => {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const startSession = useCallback(async (domain_1, domain_2, is_baseline = 0) => {
    try {
      setLoading(true);
      setError(null);
      const response = await sessionAPI.startSession(domain_1, domain_2, is_baseline);
      setSession(response.data);
      return response.data;
    } catch (err) {
      const message = err.response?.data?.detail?.message || 'Failed to start session';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const logExerciseResult = useCallback(async (sessionId, exerciseData) => {
    try {
      setError(null);
      const response = await sessionAPI.logExerciseResult(sessionId, exerciseData);
      return response.data;
    } catch (err) {
      const message = err.response?.data?.detail?.message || 'Failed to log exercise';
      setError(message);
      throw err;
    }
  }, []);

  const completeSession = useCallback(async (sessionId) => {
    try {
      setError(null);
      const response = await sessionAPI.completeSession(sessionId);
      return response.data;
    } catch (err) {
      const message = err.response?.data?.detail?.message || 'Failed to complete session';
      setError(message);
      throw err;
    }
  }, []);

  const planNextSession = useCallback(async () => {
    try {
      setError(null);
      const response = await sessionAPI.planNextSession();
      return response.data;
    } catch (err) {
      const message = err.response?.data?.detail?.message || 'Failed to plan session';
      setError(message);
      throw err;
    }
  }, []);

  return {
    session,
    loading,
    error,
    startSession,
    logExerciseResult,
    completeSession,
    planNextSession,
  };
};
