import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

import BaselineIntro from './BaselineIntro';
import BaselineTransition from './BaselineTransition';
import BaselineRuleSummary from './BaselineRuleSummary';
import BaselineGameWrapper from './BaselineGameWrapper';
import SkillProfileScreen from './SkillProfileScreen';

import NBack from '../exercises/NBack';
import CardMemoryGame from '../exercises/CardMemoryGame';
import DigitSpan from '../exercises/DigitSpan';
import GoNoGo from '../exercises/GoNoGo';
import Stroop from '../exercises/Stroop';
import SymbolMatching from '../exercises/SymbolMatching';
import VisualCategorisation from '../exercises/VisualCategorisation';

import { adaptiveBaselineAPI } from '../../api/client';

import './BaselineTest.css';

// ─── Game sequence ────────────────────────────────────────────────────────────
const BASELINE_GAMES = [
  { gameKey: 'nback',                gameName: 'Count Back Match',     GameComponent: NBack },
  { gameKey: 'go_no_go',             gameName: 'Go / No-Go',           GameComponent: GoNoGo },
  { gameKey: 'card_memory',          gameName: 'Card Memory',          GameComponent: CardMemoryGame },
  { gameKey: 'stroop',               gameName: 'Stroop',               GameComponent: Stroop },
  { gameKey: 'digit_span',           gameName: 'Digit Span',           GameComponent: DigitSpan },
  { gameKey: 'visual_categorisation',gameName: 'Visual Categorisation',GameComponent: VisualCategorisation },
];

// ─── Phase constants ──────────────────────────────────────────────────────────
const PHASE = {
  INTRO:        'intro',
  GAME:         'game',
  RULE_SUMMARY: 'rule_summary',
  TRANSITION:   'transition',
  PROFILE:      'profile',
};

// ─── Component ────────────────────────────────────────────────────────────────
const BaselineTest = () => {
  const navigate = useNavigate();

  const [phase, setPhase]                 = useState(PHASE.INTRO);
  const [currentGameIndex, setCurrentGameIndex] = useState(0);
  const [results, setResults]             = useState([]);
  const [saving, setSaving]               = useState(false);
  const [saveError, setSaveError]         = useState(null);

  // ── Handlers ──────────────────────────────────────────────────────────────

  const handleBegin = useCallback(() => {
    setPhase(PHASE.GAME);
  }, []);

  const handleGameComplete = useCallback((assessedLevel) => {
    const game = BASELINE_GAMES[currentGameIndex];
    const newResult = { gameKey: game.gameKey, gameName: game.gameName, assessedLevel };
    const updatedResults = [...results, newResult];
    setResults(updatedResults);

    setPhase(PHASE.RULE_SUMMARY);
  }, [currentGameIndex, results]);

  const handleRuleSummaryContinue = useCallback(() => {
    const isLastGame = currentGameIndex === BASELINE_GAMES.length - 1;
    if (isLastGame) {
      setPhase(PHASE.PROFILE);
    } else {
      setPhase(PHASE.TRANSITION);
    }
  }, [currentGameIndex]);

  const handleTransitionContinue = useCallback(() => {
    setCurrentGameIndex((i) => i + 1);
    setPhase(PHASE.GAME);
  }, []);

  const handleSave = useCallback(async () => {
    setSaving(true);
    setSaveError(null);
    try {
      const apiPayload = results.map(({ gameKey, assessedLevel }) => ({
        game_key: gameKey,
        assessed_level: assessedLevel,
      }));
      await adaptiveBaselineAPI.complete(apiPayload);
      navigate('/dashboard');
    } catch (err) {
      console.error('Failed to save baseline results:', err);
      setSaveError('Could not save your results — please try again.');
    } finally {
      setSaving(false);
    }
  }, [results, navigate]);

  // ── Render ────────────────────────────────────────────────────────────────

  if (phase === PHASE.INTRO) {
    return (
      <div className="baseline-page">
        <BaselineIntro
          gameCount={BASELINE_GAMES.length}
          onBegin={handleBegin}
        />
      </div>
    );
  }

  if (phase === PHASE.GAME) {
    const { gameKey, gameName, GameComponent } = BASELINE_GAMES[currentGameIndex];
    return (
      <div className="baseline-page">
        <div className="baseline-overall-progress">
          <span className="baseline-overall-progress__label">
            Assessment: game {currentGameIndex + 1} of {BASELINE_GAMES.length}
          </span>
          <div className="baseline-overall-progress__track">
            <div
              className="baseline-overall-progress__fill"
              style={{ width: `${((currentGameIndex) / BASELINE_GAMES.length) * 100}%` }}
            />
          </div>
        </div>

        <BaselineGameWrapper
          key={gameKey}
          gameKey={gameKey}
          gameName={gameName}
          GameComponent={GameComponent}
          onGameComplete={handleGameComplete}
        />
      </div>
    );
  }

  if (phase === PHASE.RULE_SUMMARY) {
    const completedGame = BASELINE_GAMES[currentGameIndex];
    return (
      <div className="baseline-page">
        <BaselineRuleSummary
          gameKey={completedGame.gameKey}
          gameName={completedGame.gameName}
          onContinue={handleRuleSummaryContinue}
        />
      </div>
    );
  }

  if (phase === PHASE.TRANSITION) {
    const completedGame = BASELINE_GAMES[currentGameIndex];
    const nextGame      = BASELINE_GAMES[currentGameIndex + 1];
    return (
      <div className="baseline-page">
        <BaselineTransition
          completedGameName={completedGame.gameName}
          nextGameName={nextGame.gameName}
          gameIndex={currentGameIndex + 1}
          gameCount={BASELINE_GAMES.length}
          onContinue={handleTransitionContinue}
        />
      </div>
    );
  }

  if (phase === PHASE.PROFILE) {
    return (
      <div className="baseline-page">
        <SkillProfileScreen
          results={results}
          saving={saving}
          error={saveError}
          onSave={handleSave}
        />
      </div>
    );
  }

  return null;
};

export default BaselineTest;
