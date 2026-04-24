import React, { useState, useEffect, useRef, useCallback } from 'react';
import Card from '../ui/Card';
import './Mindfulness.css';

const PHASE_DURATION = 4000;
const PHASES = [
  { key: 'inhale', label: 'Breathe in...', duration: PHASE_DURATION },
  { key: 'hold', label: 'Hold...', duration: PHASE_DURATION },
  { key: 'exhale', label: 'Breathe out...', duration: PHASE_DURATION },
];
const CYCLE_DURATION = PHASES.reduce((sum, p) => sum + p.duration, 0);
const SESSION_DURATION = 120000;
const TOTAL_CYCLES = Math.round(SESSION_DURATION / CYCLE_DURATION);

export function getPhaseForTime(elapsedMs) {
  const cycleMs = elapsedMs % CYCLE_DURATION;
  let accumulated = 0;
  for (const phase of PHASES) {
    accumulated += phase.duration;
    if (cycleMs < accumulated) {
      return phase;
    }
  }
  return PHASES[PHASES.length - 1];
}

export function getCycleNumber(elapsedMs) {
  return Math.floor(elapsedMs / CYCLE_DURATION) + 1;
}

export function isSessionComplete(elapsedMs) {
  return elapsedMs >= TOTAL_CYCLES * CYCLE_DURATION;
}

const Mindfulness = ({ onComplete }) => {
  const [state, setState] = useState('intro');
  const [elapsedMs, setElapsedMs] = useState(0);
  const [feelingRating, setFeelingRating] = useState(null);
  const animFrameRef = useRef(null);
  const startTimeRef = useRef(null);

  const tick = useCallback(() => {
    if (!startTimeRef.current) return;
    const now = Date.now();
    const elapsed = now - startTimeRef.current;

    if (isSessionComplete(elapsed)) {
      setElapsedMs(TOTAL_CYCLES * CYCLE_DURATION);
      setState('complete');
      return;
    }

    setElapsedMs(elapsed);
    animFrameRef.current = requestAnimationFrame(tick);
  }, []);

  const startSession = useCallback(() => {
    setState('breathing');
    startTimeRef.current = Date.now();
    animFrameRef.current = requestAnimationFrame(tick);
  }, [tick]);

  useEffect(() => {
    return () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
  }, []);

  const handleFinish = useCallback(() => {
    if (onComplete) {
      onComplete({
        exercise_type: 'mindfulness',
        completed: true,
        feeling_rating: feelingRating,
        duration_ms: TOTAL_CYCLES * CYCLE_DURATION,
      });
    }
  }, [onComplete, feelingRating]);

  if (state === 'intro') {
    return (
      <Card>
        <div className="mindfulness-intro">
          <div className="mindfulness-intro-icon" aria-hidden="true">
            <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
              <circle cx="32" cy="32" r="28" stroke="var(--color-accent)" strokeWidth="2" fill="var(--color-accent-muted)" />
              <path d="M32 18 C32 18 20 28 20 36 C20 42.627 25.373 48 32 48 C38.627 48 44 42.627 44 36 C44 28 32 18 32 18Z" fill="var(--color-accent)" opacity="0.6" />
            </svg>
          </div>
          <h2 style={{ margin: '0 0 var(--space-3) 0', color: 'var(--color-text-primary)' }}>
            Guided Breathing
          </h2>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-body)', margin: '0 0 var(--space-4) 0', textAlign: 'center', maxWidth: '360px' }}>
            Take 2 minutes to relax with a guided breathing exercise. Follow the circle as it expands and contracts.
          </p>
          <p style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--text-body-sm)', margin: '0 0 var(--space-6) 0' }}>
            {TOTAL_CYCLES} breath cycles · {SESSION_DURATION / 1000 / 60} minutes
          </p>
          <button
            className="button button-primary button-lg"
            onClick={startSession}
            data-testid="mindfulness-start"
          >
            Begin
          </button>
        </div>
      </Card>
    );
  }

  if (state === 'breathing') {
    const currentPhase = getPhaseForTime(elapsedMs);
    const cycleNum = getCycleNumber(elapsedMs);
    const progress = Math.min(elapsedMs / (TOTAL_CYCLES * CYCLE_DURATION), 1);

    const circleClass = `mindfulness-circle mindfulness-circle--${currentPhase.key}`;

    return (
      <Card>
        <div className="mindfulness-breathing">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', marginBottom: 'var(--space-4)' }}>
            <span style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--text-body-sm)' }}>
              Cycle {cycleNum} of {TOTAL_CYCLES}
            </span>
            <span style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--text-body-sm)' }}>
              {Math.ceil((TOTAL_CYCLES * CYCLE_DURATION - elapsedMs) / 1000)}s remaining
            </span>
          </div>

          <div className="progress-bar" style={{ marginBottom: 'var(--space-6)' }}>
            <div
              className="progress-bar-fill"
              style={{ width: `${progress * 100}%` }}
            />
          </div>

          <div className="mindfulness-circle-container">
            <div className={circleClass} data-testid="breathing-circle" data-phase={currentPhase.key}>
              <span className="mindfulness-circle-inner" />
            </div>
          </div>

          <p
            className="mindfulness-cue"
            data-testid="breathing-cue"
            role="status"
            aria-live="polite"
          >
            {currentPhase.label}
          </p>
        </div>
      </Card>
    );
  }

  if (state === 'complete') {
    return (
      <Card>
        <div className="mindfulness-complete">
          <div className="mindfulness-complete-icon" aria-hidden="true">
            ✓
          </div>
          <h2 style={{ margin: '0 0 var(--space-3) 0', color: 'var(--color-text-primary)' }}>
            Well done
          </h2>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-body)', margin: '0 0 var(--space-6) 0', textAlign: 'center', maxWidth: '360px' }}>
            You completed your mindfulness session. Taking a moment to breathe can make a real difference.
          </p>

          <div className="mindfulness-rating" data-testid="feeling-rating">
            <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-body-sm)', margin: '0 0 var(--space-3) 0' }}>
              How do you feel? (optional)
            </p>
            <div className="mindfulness-rating-buttons">
              {[1, 2, 3, 4, 5].map((val) => (
                <button
                  key={val}
                  className={`mindfulness-rating-btn ${feelingRating === val ? 'mindfulness-rating-btn--selected' : ''}`}
                  onClick={() => setFeelingRating(val)}
                  data-testid={`rating-${val}`}
                  aria-label={`Rating ${val} of 5`}
                >
                  {val}
                </button>
              ))}
            </div>
            <div className="mindfulness-rating-labels">
              <span style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--text-caption)' }}>Not great</span>
              <span style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--text-caption)' }}>Great</span>
            </div>
          </div>

          <button
            className="button button-primary button-lg"
            onClick={handleFinish}
            data-testid="mindfulness-finish"
            style={{ marginTop: 'var(--space-6)' }}
          >
            Finish
          </button>
        </div>
      </Card>
    );
  }

  return null;
};

export default Mindfulness;
