import React, { useState, useCallback } from 'react';
import Card from '../ui/Card';
import ProgressBar from '../ui/ProgressBar';
import { BASELINE_LEVEL_TO_DIFFICULTY, MAX_ROUNDS, INITIAL_LEVEL } from '../../constants/gameConstants';

// ─── Difficulty mapping ───────────────────────────────────────────────────────
// Internal levels: 1 = Easy, 2 = Medium, 3 = Hard
// Maps to the numeric difficulty prop accepted by all exercise components.
const LEVEL_LABELS = { 1: 'Easy', 2: 'Medium', 3: 'Hard' };

// ─── 2-up / 1-down algorithm ─────────────────────────────────────────────────
/**
 * Given current algorithm state and the result of one round, return the new state.
 *
 * @param {object} state  { level, consecutiveCorrect }
 * @param {boolean} correct
 * @returns {object}      new { level, consecutiveCorrect }
 */
export function applyAdaptiveStep(state, correct) {
  let { level, consecutiveCorrect } = state;

  if (correct) {
    consecutiveCorrect += 1;
    if (consecutiveCorrect >= 2) {
      level = Math.min(3, level + 1);
      consecutiveCorrect = 0;
    }
  } else {
    level = Math.max(1, level - 1);
    consecutiveCorrect = 0;
  }

  return { level, consecutiveCorrect };
}

// ─── Correctness extractors ───────────────────────────────────────────────────
/**
 * Determine whether a game round was "correct" based on the game key and the
 * payload returned by the game's onComplete callback.
 */
function isRoundCorrect(gameKey, payload) {
  if (!payload) return false;

  switch (gameKey) {
    case 'nback': {
      // NBack reports: { trials_presented, trials_correct, avg_response_ms }
      const { trials_presented, trials_correct } = payload;
      if (!trials_presented || trials_presented === 0) return false;
      return trials_correct / trials_presented >= 0.6;
    }
    case 'card_memory': {
      // CardMemoryGame reports: { correct, ... }
      return payload.correct === true;
    }
    case 'digit_span':
    case 'stroop':
    case 'visual_categorisation': {
      // These games report trials_presented / trials_correct but not accuracy
      if (payload.accuracy != null) return payload.accuracy >= 0.6;
      if (payload.correct != null) return payload.correct === true;
      if (payload.trials_presented > 0) return payload.trials_correct / payload.trials_presented >= 0.6;
      return false;
    }
    case 'go_no_go': {
      // GoNoGo computes and reports accuracy directly
      if (payload.accuracy != null) return payload.accuracy >= 0.6;
      if (payload.trials_presented > 0) return payload.trials_correct / payload.trials_presented >= 0.6;
      return false;
    }
    case 'symbol_matching': {
      if (payload.accuracy != null) return payload.accuracy >= 0.6;
      if (payload.correct != null) return payload.correct === true;
      if (payload.trials_presented > 0) return payload.trials_correct / payload.trials_presented >= 0.6;
      return false;
    }
    default:
      return true;
  }
}

/**
 * Determine if the adaptive staircase has stabilized and can terminate early.
 * We stop early if:
 *  - At least 4 rounds have been played, AND
 *  - The level has been the same for the last 2 rounds (no change after the
 *    adaptive step), indicating convergence.
 */
function shouldTerminateEarly(roundHistory) {
  if (roundHistory.length < 4) return false;
  const last = roundHistory[roundHistory.length - 1];
  const prev = roundHistory[roundHistory.length - 2];
  const prevPrev = roundHistory[roundHistory.length - 3];
  return last === prev && prev === prevPrev;
}

// ─── Component ────────────────────────────────────────────────────────────────

/**
 * Wraps any existing game component and runs it for up to MAX_ROUNDS rounds using
 * the 2-up/1-down adaptive algorithm. May terminate early once the level stabilizes.
 * Calls onGameComplete when done, passing the final assessed level (1–3).
 *
 * Props:
 *   gameKey       {string}               — canonical game identifier
 *   gameName      {string}               — display name
 *   GameComponent {React.ComponentType}  — the exercise component to render
 *   onGameComplete {(assessedLevel: number) => void}
 */
const BaselineGameWrapper = ({ gameKey, gameName, GameComponent, onGameComplete }) => {
  const [round, setRound] = useState(1); // 1-based
  const [algoState, setAlgoState] = useState({ level: INITIAL_LEVEL, consecutiveCorrect: 0 });
  const [roundKey, setRoundKey] = useState(0); // incremented to force re-mount of game
  const [levelHistory, setLevelHistory] = useState([INITIAL_LEVEL]);

  const handleRoundComplete = useCallback((payload) => {
    const correct = isRoundCorrect(gameKey, payload);
    const newState = applyAdaptiveStep(algoState, correct);
    const newHistory = [...levelHistory, newState.level];

    const reachedMaxRounds = round >= MAX_ROUNDS;
    const earlyStop = shouldTerminateEarly(newHistory);

    if (reachedMaxRounds || earlyStop) {
      onGameComplete(newState.level);
    } else {
      setAlgoState(newState);
      setLevelHistory(newHistory);
      setRound((r) => r + 1);
      setRoundKey((k) => k + 1);
    }
  }, [algoState, round, gameKey, onGameComplete, levelHistory]);

  const currentDifficulty = BASELINE_LEVEL_TO_DIFFICULTY[algoState.level];
  const difficultyLabel = LEVEL_LABELS[algoState.level];

  return (
    <div style={{ maxWidth: '720px', margin: '0 auto', padding: 'var(--space-4)' }}>
      {/* Header bar */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 'var(--space-3)',
      }}>
        <h2 style={{ margin: 0, fontSize: 'var(--text-heading-md)' }}>{gameName}</h2>
        <span style={{
          fontSize: 'var(--text-body-sm)',
          color: 'var(--color-text-secondary)',
          background: 'var(--color-surface-secondary, #f5f5f5)',
          padding: '2px 10px',
          borderRadius: 'var(--radius-full)',
        }}>
          {difficultyLabel}
        </span>
      </div>

      {/* Round progress */}
      <div style={{ marginBottom: 'var(--space-4)' }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: 'var(--text-body-sm)',
          color: 'var(--color-text-secondary)',
          marginBottom: 'var(--space-1)',
        }}>
          <span>Round {round} of {MAX_ROUNDS}</span>
          <span>Assessment in progress</span>
        </div>
        <ProgressBar value={round - 1} max={MAX_ROUNDS} />
      </div>

      {/* Game component — re-mounted each round via key */}
      <GameComponent
        key={roundKey}
        difficulty={currentDifficulty}
        onComplete={handleRoundComplete}
      />
    </div>
  );
};

export default BaselineGameWrapper;
