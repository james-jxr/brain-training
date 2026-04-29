import React, { useState, useEffect, useRef, useCallback } from 'react';
import Button from '../ui/Button';
import Card from '../ui/Card';
import ProgressBar from '../ui/ProgressBar';

const MAX_TRIALS = 8;

/**
 * Pure function: compute the final result from a completed Stroop session.
 * Exported for unit testing.
 */
export function computeStroopResult({ trialsPresented, trialsCorrect, responseTimes }) {
  const avgResponseMs = responseTimes.length > 0
    ? responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length
    : 0;
  return {
    trials_presented: trialsPresented,
    trials_correct: trialsCorrect,
    avg_response_ms: avgResponseMs,
  };
}

const Stroop = ({ difficulty, onComplete }) => {
  const [trials, setTrials] = useState(0);
  const [correct, setCorrect] = useState(0);
  const [started, setStarted] = useState(false);
  const [currentTrial, setCurrentTrial] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [responseTimes, setResponseTimes] = useState([]);
  const [trialStartTime, setTrialStartTime] = useState(null);

  const correctRef = useRef(0);
  const trialsRef = useRef(0);
  const responseTimesRef = useRef([]);

  const allColors = ['red', 'blue', 'green', 'yellow'];
  const colorWordMap = {
    red: 'RED',
    blue: 'BLUE',
    green: 'GREEN',
    yellow: 'YELLOW',
  };
  const colorMap = {
    red: '#D95F5F',
    blue: '#4A90C4',
    green: '#3D9E72',
    yellow: '#F4D35E',
  };

  const generateTrial = () => {
    const numOptions = Math.min(4, 2 + Math.floor(difficulty / 3));
    const shuffled = [...allColors].sort(() => Math.random() - 0.5);
    const availableColors = shuffled.slice(0, numOptions);
    const options = availableColors.slice();

    const inkColor = options[Math.floor(Math.random() * options.length)];

    const incongruentWordColors = allColors.filter(c => c !== inkColor);
    const wordColor = incongruentWordColors[Math.floor(Math.random() * incongruentWordColors.length)];
    const word = colorWordMap[wordColor];

    return {
      word,
      inkColor,
      options,
      correctAnswer: inkColor,
    };
  };

  const startTrial = useCallback(() => {
    if (trialsRef.current >= MAX_TRIALS) {
      onComplete(computeStroopResult({
        trialsPresented: trialsRef.current,
        trialsCorrect: correctRef.current,
        responseTimes: responseTimesRef.current,
      }));
      return;
    }

    const trial = generateTrial();
    trialsRef.current += 1;
    setTrials(trialsRef.current);
    setCurrentTrial(trial);
    setFeedback(null);
    setTrialStartTime(Date.now());
  }, [difficulty, onComplete]);

  const handleColorClick = (color) => {
    if (!currentTrial || feedback) return;

    const responseTime = Date.now() - trialStartTime;
    const isCorrect = color === currentTrial.correctAnswer;

    responseTimesRef.current = [...responseTimesRef.current, responseTime];
    setResponseTimes(responseTimesRef.current);
    setFeedback(isCorrect ? 'correct' : 'incorrect');

    if (isCorrect) {
      correctRef.current += 1;
      setCorrect(correctRef.current);
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
        <h2>Stroop Task</h2>
        <p>Click the colour of the WORD (not the word itself). Level {difficulty}</p>
        <Button onClick={() => setStarted(true)} variant="primary">
          Start
        </Button>
      </Card>
    );
  }

  if (trials === 0) {
    return <div>Loading...</div>;
  }

  if (trials > MAX_TRIALS) {
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
        <ProgressBar value={trials - 1} max={MAX_TRIALS} />
      </div>

      {currentTrial && (
        <div style={{ textAlign: 'center', padding: 'var(--space-6)' }}>
          <p style={{ fontSize: 'var(--text-body-sm)', marginBottom: 'var(--space-4)' }}>
            Click the INK COLOR (not the word)
          </p>

          <div style={{
            fontSize: '4rem',
            fontWeight: 'var(--weight-bold)',
            marginBottom: 'var(--space-8)',
            color: colorMap[currentTrial.inkColor],
            letterSpacing: 'var(--tracking-wide)',
          }}>
            {currentTrial.word}
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: `repeat(${Math.min(2, currentTrial.options.length)}, 1fr)`,
            gap: 'var(--space-4)',
            marginBottom: 'var(--space-4)',
          }}>
            {currentTrial.options.map((color) => (
              <Button
                key={color}
                onClick={() => handleColorClick(color)}
                variant="secondary"
                style={{
                  opacity: feedback && color !== currentTrial.correctAnswer ? 0.5 : 1,
                }}
                disabled={feedback !== null}
              >
                {color.charAt(0).toUpperCase() + color.slice(1)}
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

export default Stroop;
