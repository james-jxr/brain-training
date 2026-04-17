/**
 * RETIRED — superseded by the full Go/No-Go implementation in GoNoGo.jsx (2026-04-04).
 *
 * This was the original minimal implementation used as the Attention & Inhibitory Control
 * exercise prior to the Go/No-Go feature build. It is kept here for reference only.
 * Do not import or use this component in new features.
 *
 * Why retired:
 * - Showed "DO NOT PRESS" text on No-Go stimuli, removing the inhibition challenge
 * - Used timing formula (1500ms - difficulty*100) not aligned with validated paradigms
 * - Only red/green circles — no shape variety
 * - Scored accuracy only, no false-alarm penalty
 * - No result breakdown screen
 */

import React, { useState, useEffect } from 'react';
import Button from '../ui/Button';
import Card from '../ui/Card';
import ProgressBar from '../ui/ProgressBar';

const GoNoGoLegacy = ({ difficulty, onComplete }) => {
  const [trials, setTrials] = useState(0);
  const [correct, setCorrect] = useState(0);
  const [started, setStarted] = useState(false);
  const [stimuli, setStimuli] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [currentStimulus, setCurrentStimulus] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [responseTimes, setResponseTimes] = useState([]);
  const [stimulusStartTime, setStimulusStartTime] = useState(null);

  const generateStimuli = () => {
    const goRatio = Math.max(0.4, 1.0 - difficulty * 0.05);
    const numGo = Math.floor(15 * goRatio);
    const numNoGo = 15 - numGo;

    const sequence = [];
    for (let i = 0; i < numGo; i++) sequence.push('go');
    for (let i = 0; i < numNoGo; i++) sequence.push('no_go');

    return sequence.sort(() => Math.random() - 0.5);
  };

  const startTrial = () => {
    if (currentIndex >= stimuli.length) {
      const avgResponseTime = responseTimes.length > 0
        ? responseTimes.reduce((a, b) => a + b) / responseTimes.length
        : 0;

      onComplete({
        trials_presented: trials,
        trials_correct: correct,
        avg_response_ms: avgResponseTime,
      });
      return;
    }

    const stimulus = stimuli[currentIndex];
    setCurrentStimulus(stimulus);
    setStimulusStartTime(Date.now());
    setFeedback(null);
    setTrials(trials + 1);

    const displayTime = 1500 - difficulty * 100;
    const timer = setTimeout(() => {
      if (stimulus === 'go') {
        setFeedback('missed');
      }
      setCurrentStimulus(null);
      setTimeout(() => {
        setCurrentIndex(currentIndex + 1);
      }, 500);
    }, displayTime);

    return () => clearTimeout(timer);
  };

  const handleResponse = () => {
    if (!currentStimulus) return;

    const responseTime = Date.now() - stimulusStartTime;

    if (currentStimulus === 'go') {
      setFeedback('correct');
      setCorrect(correct + 1);
    } else {
      setFeedback('incorrect');
    }

    setResponseTimes([...responseTimes, responseTime]);
    setCurrentStimulus(null);

    setTimeout(() => {
      setCurrentIndex(currentIndex + 1);
    }, 500);
  };

  useEffect(() => {
    if (!started) return;
    if (stimuli.length === 0) {
      const newStimuli = generateStimuli();
      setStimuli(newStimuli);
      setCurrentIndex(0);
      return;
    }
    startTrial();
  }, [started, currentIndex, stimuli]);

  if (!started) {
    return (
      <Card>
        <h2>Go/No-Go Task</h2>
        <p>Press the button when you see a green circle (GO). Do NOT press when you see a red circle (NO-GO). Level {difficulty}</p>
        <Button onClick={() => setStarted(true)} variant="primary">
          Start
        </Button>
      </Card>
    );
  }

  if (stimuli.length === 0) {
    return <div>Loading...</div>;
  }

  if (currentIndex >= stimuli.length) {
    return (
      <Card>
        <h2>Exercise Complete</h2>
        <p>You got {correct} out of {trials} correct!</p>
      </Card>
    );
  }

  return (
    <Card>
      <div style={{ marginBottom: 'var(--space-4)' }}>
        <ProgressBar value={currentIndex} max={stimuli.length} />
      </div>

      <div style={{
        textAlign: 'center',
        padding: 'var(--space-8)',
        minHeight: '400px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        {currentStimulus && (
          <>
            <div style={{
              width: '200px',
              height: '200px',
              borderRadius: '50%',
              backgroundColor: currentStimulus === 'go' ? '#3D9E72' : '#D95F5F',
              marginBottom: 'var(--space-6)',
              animation: 'pulse 0.3s ease-in-out',
            }} />
            {currentStimulus === 'go' && (
              <Button
                onClick={handleResponse}
                variant="primary"
                size="lg"
              >
                GO - Press!
              </Button>
            )}
            {currentStimulus === 'no_go' && (
              <p style={{ fontSize: 'var(--text-h3)', fontWeight: 'var(--weight-bold)' }}>
                DO NOT PRESS
              </p>
            )}
          </>
        )}

        {feedback && (
          <div className={`answer-feedback ${feedback}`} style={{ marginTop: 'var(--space-4)' }}>
            {feedback === 'correct' ? 'Correct!' : feedback === 'incorrect' ? 'Incorrect!' : 'Missed!'}
          </div>
        )}
      </div>

      <style>{`
        @keyframes pulse {
          0% { transform: scale(1); }
          50% { transform: scale(1.05); }
          100% { transform: scale(1); }
        }
      `}</style>
    </Card>
  );
};

export default GoNoGoLegacy;
