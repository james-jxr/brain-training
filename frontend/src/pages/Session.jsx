import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
import { BASELINE_LEVEL_TO_DIFFICULTY } from '../constants/gameConstants';

// Exercise type → baseline game_key mapping
// Used to look up the user's assessed starting difficulty.
const EXERCISE_TYPE_TO_GAME_KEY = {
  n_back:               'nback',
  card_memory:          'card_memory',
  digit_span:           'digit_span',
  go_no_go:             'go_no_go',
  stroop:               'stroop',
  symbol_matching:      'symbol_matching',
  visual_categorisation:'visual_categorisation',
};

const isTextInputFocused = () => {
  const el = document.activeElement;
  if (!el) return false;
  const tag = el.tagName.toLowerCase();
  if (tag === 'textarea') return true;
  if (tag === 'input') {
    const type = (el.getAttribute('type') || 'text').toLowerCase();
    const textTypes = ['text', 'search', 'url', 'tel', 'password', 'email', 'number'];
    return textTypes.includes(type);
  }
  if (el.isContentEditable) return true;
  return false;
};

const Session = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { session, logExerciseResult, completeSession, loading, error } = useSession();
  const [currentExerciseIndex, setCurrentExerciseIndex] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [difficulty, setDifficulty] = useState(1);
  const [initialDifficultyLoaded, setInitialDifficultyLoaded] = useState(false);

  // Skill profile fetched once on mount: game_key → assessed_level (1|2|3)
  const [skillProfile, setSkillProfile] = useState({});

  const exercises = [
    { domain: 'processing_speed', type: 'visual_categorisation', component: VisualCategorisation },
    { domain: 'working_memory',   type: 'n_back',                component: NBack },
    { domain: 'working_memory',   type: 'digit_span',            component: DigitSpan },
    { domain: 'attention',        type: 'go_no_go',              component: GoNoGo },
    { domain: 'attention',        type: 'stroop',                component: Stroop },
    { domain: 'episodic_memory',  type: 'card_memory',           component: CardMemoryGame },
    { domain: 'mindfulness',      type: 'mindfulness',           component: Mindfulness, noScoring: true },
  ];

  // Fetch the user's baseline skill profile once when the session starts.
  useEffect(() => {
    const loadSkillProfile = async () => {
      try {
        const res = await adaptiveBaselineAPI.getStatus();
        if (res.data.has_completed && res.data.profile) {
          const map = {};
          for (const entry of res.data.profile) {
            map[entry.game_key] = entry.assessed_level;
          }
          setSkillProfile(map);
        }
      } catch {
        // If the profile fetch fails, fall through to domain-progress difficulty below
      }
    };
    loadSkillProfile();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Global keydown guard: allow default behaviour when a text input is focused
  useEffect(() => {
    const handler = (e) => {
      if (e.code === 'Space' && isTextInputFocused()) {
        e.stopPropagation();
      }
    };
    window.addEventListener('keydown', handler, true);
    return () => window.removeEventListener('keydown', handler, true);
  }, []);

  // Load difficulty for the FIRST exercise only (index 0) or when no adaptive
  // difficulty has been received yet from the backend.
  // Subsequent exercises use the adjusted_difficulty returned by the backend.
  useEffect(() => {
    if (initialDifficultyLoaded && currentExerciseIndex > 0) {
      return;
    }

    const exercise = exercises[currentExerciseIndex];

    // Mindfulness doesn't need difficulty
    if (exercise.noScoring) {
      setInitialDifficultyLoaded(true);
      return;
    }

    const loadDifficulty = async () => {
      const gameKey = EXERCISE_TYPE_TO_GAME_KEY[exercise.type];

      // 1. Try baseline assessed level first
      if (gameKey && skillProfile[gameKey] != null) {
        const baselineDifficulty = BASELINE_LEVEL_TO_DIFFICULTY[skillProfile[gameKey]];
        if (baselineDifficulty != null) {
          setDifficulty(baselineDifficulty);
          setInitialDifficultyLoaded(true);
          return;
        }
      }

      // 2. Fall back to domain adaptive difficulty
      try {
        const progress = await progressAPI.getDomainProgress(exercise.domain);
        setDifficulty(progress.data.current_difficulty);
      } catch {
        setDifficulty(1);
      }
      setInitialDifficultyLoaded(true);
    };

    loadDifficulty();
  }, [currentExerciseIndex, skillProfile]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleExerciseComplete = async (result) => {
    const exercise = exercises[currentExerciseIndex];

    // Mindfulness: no scoring, just advance
    if (exercise.noScoring) {
      if (currentExerciseIndex < exercises.length - 1) {
        setCurrentExerciseIndex(currentExerciseIndex + 1);
      } else {
        await completeSession(sessionId);
        navigate(`/session/${sessionId}/summary`);
      }
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        domain: exercise.domain,
        exercise_type: exercise.type,
      };

      if (exercise.type === 'card_memory') {
        payload.difficulty = String(difficulty);
        payload.card_count = result.card_count || 4;
        payload.correct = result.correct;
        payload.response_time_ms = result.response_time_ms;
        payload.score = result.score;
        payload.trials_presented = result.total_rounds || result.rounds?.length || 1;
        payload.trials_correct = result.rounds_correct != null ? result.rounds_correct : (result.correct ? 1 : 0);
        payload.avg_response_ms = result.response_time_ms;
      } else {
        payload.trials_presented = result.trials_presented;
        payload.trials_correct = result.trials_correct;
        payload.avg_response_ms = result.avg_response_ms;
        payload.difficulty = String(difficulty);
      }

      const responseData = await logExerciseResult(sessionId, payload);

      // Use the backend's adjusted_difficulty for the next exercise
      if (responseData && responseData.adjusted_difficulty != null) {
        setDifficulty(responseData.adjusted_difficulty);
      }

      if (currentExerciseIndex < exercises.length - 1) {
        setCurrentExerciseIndex(currentExerciseIndex + 1);
      } else {
        await completeSession(sessionId);
        navigate(`/session/${sessionId}/summary`);
      }
    } catch (err) {
      console.error('Failed to log exercise:', err);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <Card>Loading session...</Card>;
  }

  if (error) {
    return <Card style={{ color: 'var(--color-error)' }}>Error: {error}</Card>;
  }

  if (currentExerciseIndex >= exercises.length) {
    return <Card>Session complete!</Card>;
  }

  const currentExercise = exercises[currentExerciseIndex];
  const CurrentExercise = currentExercise.component;
  const exerciseLabel = currentExercise.type.replace('_', ' ').toUpperCase();

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: 'var(--color-bg-base)',
      padding: 'var(--space-6)',
    }}>
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        <div style={{
          marginBottom: 'var(--space-6)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div>
            <h1>{exerciseLabel}</h1>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-body-sm)' }}>
              Exercise {currentExerciseIndex + 1} of {exercises.length}
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
            {!currentExercise.noScoring && (
              <div style={{ fontSize: 'var(--text-body-sm)', color: 'var(--color-text-secondary)' }}>
                Difficulty: <strong>{difficulty}</strong>/10
              </div>
            )}
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
        </div>

        {!submitting ? (
          currentExercise.noScoring ? (
            <CurrentExercise
              onComplete={handleExerciseComplete}
            />
          ) : (
            <CurrentExercise
              difficulty={difficulty}
              onComplete={handleExerciseComplete}
            />
          )
        ) : (
          <Card>
            <p>Saving results...</p>
          </Card>
        )}
      </div>
    </div>
  );
};

export default Session;
