import React, { useState, useEffect } from 'react';
import Button from '../ui/Button';
import Card from '../ui/Card';
import Input from '../ui/Input';
import ProgressBar from '../ui/ProgressBar';

const MAX_TRIALS = 8;

const DigitSpan = ({ difficulty, onComplete }) => {
  const [trials, setTrials] = useState(0);
  const [correct, setCorrect] = useState(0);
  const [started, setStarted] = useState(false);
  const [phase, setPhase] = useState('waiting');
  const [currentDigits, setCurrentDigits] = useState([]);
  const [userInput, setUserInput] = useState('');
  const [feedback, setFeedback] = useState(null);
  const [responseTimes, setResponseTimes] = useState([]);
  const [trialStartTime, setTrialStartTime] = useState(null);
  const [maxLengthRecalled, setMaxLengthRecalled] = useState(0);

  const generateDigits = () => {
    const base = 2 + Math.floor(difficulty * 0.8);
    const minLength = Math.max(2, base - 1);
    const maxLength = Math.min(10, base + 1);
    const length = Math.floor(Math.random() * (maxLength - minLength + 1)) + minLength;
    return Array.from({ length }, () => Math.floor(Math.random() * 10).toString());
  };

  const startTrial = () => {
    if (trials >= MAX_TRIALS) {
      const avgResponseTime = responseTimes.length > 0
        ? responseTimes.reduce((a, b) => a + b) / responseTimes.length
        : 0;

      onComplete({
        trials_presented: trials,
        trials_correct: correct,
        max_length_recalled: maxLengthRecalled,
        avg_response_ms: avgResponseTime,
      });
      return;
    }

    const digits = generateDigits();
    setCurrentDigits(digits);
    setUserInput('');
    setFeedback(null);
    setPhase('showing');
    setTrials(trials + 1);
    setTrialStartTime(Date.now());
  };

  useEffect(() => {
    if (!started) return;
    if (trials === 0) {
      startTrial();
      return;
    }
  }, [started]);

  useEffect(() => {
    if (phase !== 'showing') return;

    const displayTime = 2000;
    const timer = setTimeout(() => {
      setPhase('input');
    }, displayTime);

    return () => clearTimeout(timer);
  }, [phase]);

  const handleSubmit = () => {
    if (phase !== 'input') return;

    const responseTime = Date.now() - trialStartTime;
    const expected = currentDigits.join('');
    const isCorrect = userInput === expected;

    setResponseTimes([...responseTimes, responseTime]);
    setFeedback(isCorrect ? 'correct' : 'incorrect');

    if (isCorrect) {
      setCorrect(correct + 1);
      if (currentDigits.length > maxLengthRecalled) {
        setMaxLengthRecalled(currentDigits.length);
      }
    }

    setTimeout(() => {
      startTrial();
    }, 1500);
  };

  if (!started) {
    return (
      <Card>
        <h2>Digit Span</h2>
        <p>Memorise the digit sequence shown, then type it back. Level {difficulty}</p>
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
        <p>Max sequence length recalled: {maxLengthRecalled}</p>
      </Card>
    );
  }

  return (
    <Card>
      <div style={{ marginBottom: 'var(--space-4)' }}>
        <ProgressBar value={trials - 1} max={MAX_TRIALS} />
      </div>

      {phase === 'showing' && (
        <div style={{ textAlign: 'center', padding: 'var(--space-8)' }}>
          <p style={{ fontSize: 'var(--text-body-sm)', marginBottom: 'var(--space-4)' }}>
            Remember this sequence:
          </p>
          <div style={{ fontSize: 'var(--text-display)', letterSpacing: 'var(--tracking-wide)' }}>
            {currentDigits.join(' ')}
          </div>
        </div>
      )}

      {phase === 'input' && (
        <div style={{ padding: 'var(--space-6)' }}>
          <p style={{ fontSize: 'var(--text-body-sm)', marginBottom: 'var(--space-4)' }}>
            Type the sequence you saw:
          </p>
          <Input
            type="text"
            inputMode="numeric"
            value={userInput}
            onChange={(e) => setUserInput(e.target.value.replace(/\D/g, '').slice(0, 12))}
            onKeyDown={(e) => { if (e.key === 'Enter') handleSubmit(); }}
            placeholder="Type digits here"
            autoFocus
          />
          <Button
            onClick={handleSubmit}
            variant="primary"
            style={{ width: '100%', marginTop: 'var(--space-4)' }}
          >
            Submit
          </Button>

          {feedback && (
            <div className={`answer-feedback ${feedback}`} style={{ marginTop: 'var(--space-4)' }}>
              {feedback === 'correct' ? 'Correct!' : 'Incorrect'}
            </div>
          )}
        </div>
      )}
    </Card>
  );
};

export default DigitSpan;
