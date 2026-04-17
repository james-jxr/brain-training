import React, { useState, useEffect } from 'react';
import Button from '../ui/Button';
import Card from '../ui/Card';
import ProgressBar from '../ui/ProgressBar';

const SymbolMatching = ({ difficulty, onComplete }) => {
  const [trials, setTrials] = useState(0);
  const [correct, setCorrect] = useState(0);
  const [started, setStarted] = useState(false);
  const [currentTrial, setCurrentTrial] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [responseTimes, setResponseTimes] = useState([]);
  const [trialStartTime, setTrialStartTime] = useState(null);
  const [displayTime, setDisplayTime] = useState(3000 - difficulty * 200);

  const symbols = ['◯', '□', '△', '◇', '★', '♡', '▪', '●', '✕', '⬡'];

  const generateTrial = () => {
    const targetIdx = Math.floor(Math.random() * symbols.length);
    const target = symbols[targetIdx];

    const numDistractors = Math.min(3, Math.floor(difficulty / 3) + 2);
    const distractors = symbols.filter((_, i) => i !== targetIdx);
    const selectedDistractors = distractors.sort(() => Math.random() - 0.5).slice(0, numDistractors);
    const options = [target, ...selectedDistractors].sort(() => Math.random() - 0.5);

    return {
      target,
      options,
      correctIndex: options.indexOf(target),
    };
  };

  const startTrial = () => {
    if (trials >= 8) {
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

    const trial = generateTrial();
    setCurrentTrial(trial);
    setFeedback(null);
    setTrialStartTime(Date.now());
    setTrials(trials + 1);
  };

  const handleOptionClick = (index) => {
    if (!currentTrial || feedback) return;

    const responseTime = Date.now() - trialStartTime;
    const isCorrect = index === currentTrial.correctIndex;

    setResponseTimes([...responseTimes, responseTime]);
    setFeedback(isCorrect ? 'correct' : 'incorrect');

    if (isCorrect) {
      setCorrect(correct + 1);
    }

    setTimeout(() => {
      startTrial();
    }, 1000);
  };

  useEffect(() => {
    if (!started) return;
    startTrial();
  }, [started]);

  if (!started) {
    return (
      <Card>
        <h2>Symbol Matching</h2>
        <p>Match the target symbol to one of the options. Level {difficulty}</p>
        <Button onClick={() => setStarted(true)} variant="primary">
          Start
        </Button>
      </Card>
    );
  }

  if (trials === 0) {
    return <div>Loading...</div>;
  }

  if (trials > 8) {
    return (
      <Card>
        <h2>Exercise Complete</h2>
        <p>You got {correct} out of {trials - 1} correct!</p>
      </Card>
    );
  }

  return (
    <Card>
      <div style={{ marginBottom: 'var(--space-4)' }}>
        <ProgressBar value={trials - 1} max={8} />
      </div>

      {currentTrial && (
        <div style={{ textAlign: 'center', padding: 'var(--space-6)' }}>
          <p style={{ fontSize: 'var(--text-body-sm)', marginBottom: 'var(--space-2)' }}>Find the match:</p>
          <p style={{ fontSize: '4rem', marginBottom: 'var(--space-6)' }}>{currentTrial.target}</p>

          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 'var(--space-4)',
            marginBottom: 'var(--space-4)',
          }}>
            {currentTrial.options.map((symbol, index) => (
              <Button
                key={index}
                onClick={() => handleOptionClick(index)}
                variant={feedback ? 'secondary' : 'primary'}
                style={{
                  fontSize: '2.5rem',
                  height: '100px',
                  opacity: feedback && index !== currentTrial.correctIndex ? 0.5 : 1,
                }}
                disabled={feedback !== null}
              >
                {symbol}
              </Button>
            ))}
          </div>

          {feedback && (
            <div className={`answer-feedback ${feedback}`}>
              {feedback === 'correct' ? 'Correct!' : 'Incorrect'}
            </div>
          )}
        </div>
      )}
    </Card>
  );
};

export default SymbolMatching;
