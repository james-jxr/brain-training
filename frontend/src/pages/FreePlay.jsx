import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import Card from '../components/ui/Card';
import VisualCategorisation from '../components/exercises/VisualCategorisation';
import NBack from '../components/exercises/NBack';
import DigitSpan from '../components/exercises/DigitSpan';
import GoNoGo from '../components/exercises/GoNoGo';
import Stroop from '../components/exercises/Stroop';
import CardMemoryGame from '../components/exercises/CardMemoryGame';
import Mindfulness from '../components/exercises/Mindfulness';
import { useSession } from '../hooks/useSession';
import { progressAPI, adaptiveBaselineAPI } from '../api/client';
import { BASELINE_LEVEL_TO_DIFFICULTY } from '../utils/difficulty';

const GAME_CONFIG = {
  visual_categorisation: { label: 'Visual Categorisation',  domain: 'processing_speed', component: VisualCategorisation },
  n_back:                { label: 'Count Back',             domain: 'working_memory',   component: NBack },
  digit_span:            { label: 'Digit Span',             domain: 'working_memory',   component: DigitSpan },
  go_no_go:              { label: 'Go / No-Go',             domain: 'attention',        component: GoNoGo },
  stroop:                { label: 'Stroop',                 domain: 'attention',        component: Stroop },
  card_memory:           { label: 'Card Memory',            domain: 'episodic_memory',  component: CardMemoryGame },
  mindfulness:           { label: 'Guided Breathing',       domain: 'mindfulness',      component: Mindfulness, noScoring: true },
};

const GAME_KEY_MAP = {
  visual_categorisation: 'visual_categorisation',
  n_back: 'nback',
  digit_span: 'digit_span',
  go_no_go: 'go_no_go',
  stroop: 'stroop',
  card_memory: 'card_memory',
};

const FreePlay = () => {
  const { gameKey } = useParams();
  const navigate = useNavigate();
  const { logExerciseResult, completeSession } = useSession();

  const [sessionId, setSessionId] = useState(null);
  const [difficulty, setDifficulty] = useState(1);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const config = GAME_CONFIG[gameKey];

  const init = useCallback(async () => {
    if (!config) return;

    // Mindfulness doesn't need session/difficulty setup
    if (config.noScoring) {
      setReady(true);
      return;
    }

    setError(false);

    let newSessionId;
    try {
      // Start a session for this domain
      const { sessionAPI } = await import('../api/client');
      const res = await sessionAPI.startSession(config.domain, config.domain);
      newSessionId = res.data.id;
      setSessionId(newSessionId);
    } catch {
      setError(true);
      return;
    }

    // Resolve difficulty: baseline level first, then domain progress, then default 1
    try {
      const baselineRes = await adaptiveBaselineAPI.getStatus();
      if (baselineRes.data.has_completed) {
        const entry = baselineRes.data.profile.find(
          (p) => p.game_key === GAME_KEY_MAP[gameKey]
        );
        if (entry) {
          setDifficulty(BASELINE_LEVEL_TO_DIFFICULTY[entry.assessed_level] ?? 1);
          setReady(true);
          return;
        }
      }
    } catch { /* fall through */ }

    try {
      const progressRes = await progressAPI.getDomainProgress(config.domain);
      setDifficulty(progressRes.data.current_difficulty);
    } catch { /* use default 1 */ }

    setReady(true);
  }, [gameKey]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!config) return;
    init();
  }, [gameKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleRetry = () => {
    setError(false);
    init();
  };

  const handleComplete = async (result) => {
    // Mindfulness: no scoring needed, just navigate back
    if (config && config.noScoring) {
      navigate('/dashboard');
      return;
    }

    if (!sessionId) return;
    setSubmitting(true);
    try {
      const payload = {
        domain: config.domain,
        exercise_type: gameKey,
      };

      if (gameKey === 'card_memory') {
        payload.difficulty = result.difficulty;
        payload.card_count = result.card_count || 4;
        payload.correct = result.correct;
        payload.response_time_ms = result.response_time_ms;
        payload.score = result.score;
        payload.trials_presented = 1;
        payload.trials_correct = result.correct ? 1 : 0;
        payload.avg_response_ms = result.response_time_ms;
      } else {
        payload.trials_presented = result.trials_presented;
        payload.trials_correct = result.trials_correct;
        payload.avg_response_ms = result.avg_response_ms;
      }

      await logExerciseResult(sessionId, payload);
      await completeSession(sessionId);
      navigate(`/session/${sessionId}/summary`);
    } catch (err) {
      console.error('Failed to save result:', err);
    } finally {
      setSubmitting(false);
    }
  };

  if (!config) {
    return <Card>Unknown game.</Card>;
  }

  if (error) {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: 'var(--color-bg-base)', padding: 'var(--space-6)' }}>
        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
          <Card>
            <div style={{ textAlign: 'center', padding: 'var(--space-6) 0' }}>
              <p style={{ marginBottom: 'var(--space-4)', color: 'var(--color-text-primary)', fontSize: 'var(--text-body-md)' }}>
                Something went wrong starting your session. Please try again.
              </p>
              <div style={{ display: 'flex', gap: 'var(--space-3)', justifyContent: 'center', alignItems: 'center', flexWrap: 'wrap' }}>
                <button
                  onClick={handleRetry}
                  style={{
                    background: 'var(--color-primary)',
                    border: 'none',
                    borderRadius: 'var(--radius-md)',
                    padding: 'var(--space-2) var(--space-4)',
                    fontSize: 'var(--text-body-sm)',
                    color: '#fff',
                    cursor: 'pointer',
                  }}
                >
                  Retry
                </button>
                <Link
                  to="/dashboard"
                  style={{
                    fontSize: 'var(--text-body-sm)',
                    color: 'var(--color-text-secondary)',
                    textDecoration: 'underline',
                  }}
                >
                  Back to Dashboard
                </Link>
              </div>
            </div>
          </Card>
        </div>
      </div>
    );
  }

  if (!ready) {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: 'var(--color-bg-base)', padding: 'var(--space-6)' }}>
        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
          <Card>Loading...</Card>
        </div>
      </div>
    );
  }

  const GameComponent = config.component;

  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--color-bg-base)', padding: 'var(--space-6)' }}>
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        <div style={{
          marginBottom: 'var(--space-6)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div>
            <h1>{config.label}</h1>
            {config.noScoring ? (
              <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-body-sm)' }}>
                Free play · Mindfulness
              </p>
            ) : (
              <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-body-sm)' }}>
                Free play · Difficulty {difficulty}/10
              </p>
            )}
          </div>
          <button
            onClick={() => navigate('/dashboard')}
            style={{
              background: 'none',
              border: '1px solid var(--color-border-default)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-2) var(--space-3)',
              fontSize: 'var(--text-body-sm)',
              color: 'var(--color-text-secondary)',
              cursor: 'pointer',
            }}
          >
            ✕ Quit
          </button>
        </div>

        {submitting ? (
          <Card><p>Saving results...</p></Card>
        ) : config.noScoring ? (
          <GameComponent onComplete={handleComplete} />
        ) : (
          <GameComponent difficulty={difficulty} onComplete={handleComplete} />
        )}
      </div>
    </div>
  );
};

export default FreePlay;
