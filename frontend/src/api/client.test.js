import { describe, it, expect } from 'vitest';
import { authAPI, sessionAPI, progressAPI, lifestyleAPI, accountAPI, baselineAPI, adaptiveBaselineAPI, feedbackAPI } from './client';

describe('API client exports', () => {
  describe('authAPI', () => {
    it('exports register function', () => expect(typeof authAPI.register).toBe('function'));
    it('exports login function', () => expect(typeof authAPI.login).toBe('function'));
    it('exports logout function', () => expect(typeof authAPI.logout).toBe('function'));
    it('exports getCurrentUser function', () => expect(typeof authAPI.getCurrentUser).toBe('function'));
  });

  describe('sessionAPI', () => {
    it('exports startSession function', () => expect(typeof sessionAPI.startSession).toBe('function'));
    it('exports logExerciseResult function', () => expect(typeof sessionAPI.logExerciseResult).toBe('function'));
    it('exports completeSession function', () => expect(typeof sessionAPI.completeSession).toBe('function'));
    it('exports getSession function', () => expect(typeof sessionAPI.getSession).toBe('function'));
    it('exports listSessions function', () => expect(typeof sessionAPI.listSessions).toBe('function'));
    it('exports planNextSession function', () => expect(typeof sessionAPI.planNextSession).toBe('function'));
  });

  describe('progressAPI', () => {
    it('exports getDomainProgress function', () => expect(typeof progressAPI.getDomainProgress).toBe('function'));
    it('exports getProgressSummary function', () => expect(typeof progressAPI.getProgressSummary).toBe('function'));
    it('exports getBrainHealthScore function', () => expect(typeof progressAPI.getBrainHealthScore).toBe('function'));
    it('exports getStreak function', () => expect(typeof progressAPI.getStreak).toBe('function'));
    it('exports getDomainTrend function', () => expect(typeof progressAPI.getDomainTrend).toBe('function'));
    it('exports getGameHistory function', () => expect(typeof progressAPI.getGameHistory).toBe('function'));
    it('exports getStreakHistory function', () => expect(typeof progressAPI.getStreakHistory).toBe('function'));
  });

  describe('lifestyleAPI', () => {
    it('exports logLifestyle function', () => expect(typeof lifestyleAPI.logLifestyle).toBe('function'));
    it('exports getTodayLifestyle function', () => expect(typeof lifestyleAPI.getTodayLifestyle).toBe('function'));
    it('exports getLifestyleHistory function', () => expect(typeof lifestyleAPI.getLifestyleHistory).toBe('function'));
  });

  describe('accountAPI', () => {
    it('exports getProfile function', () => expect(typeof accountAPI.getProfile).toBe('function'));
    it('exports markOnboardingComplete function', () => expect(typeof accountAPI.markOnboardingComplete).toBe('function'));
    it('exports getOnboardingStatus function', () => expect(typeof accountAPI.getOnboardingStatus).toBe('function'));
  });

  describe('baselineAPI', () => {
    it('exports startBaseline function', () => expect(typeof baselineAPI.startBaseline).toBe('function'));
    it('exports getNextEligibleDate function', () => expect(typeof baselineAPI.getNextEligibleDate).toBe('function'));
  });

  describe('adaptiveBaselineAPI', () => {
    it('exports getStatus function', () => expect(typeof adaptiveBaselineAPI.getStatus).toBe('function'));
    it('exports complete function', () => expect(typeof adaptiveBaselineAPI.complete).toBe('function'));
  });

  describe('feedbackAPI', () => {
    it('exports submitFeedback function', () => expect(typeof feedbackAPI.submitFeedback).toBe('function'));
    it('exports exportFeedback function', () => expect(typeof feedbackAPI.exportFeedback).toBe('function'));
  });
});
