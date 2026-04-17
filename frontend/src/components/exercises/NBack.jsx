// Count Back Match — N-back task
// build-v0.2: self-paced advancement, automatic lead-in, balanced match ratio, accuracy-only scoring
import React, { useState, useEffect, useRef } from 'react';
import Button from '../ui/Button';
import Card from '../ui/Card';
import ProgressBar from '../ui/ProgressBar';

// Derive N-back level from numeric difficulty (1–10)
const getNBackLevel = (difficulty) => {
  if (difficulty <= 3) return 1;
  if (difficulty <= 6) return 2;
  return 3;
};

// Generate a balanced sequence where ~50% of judgeable trials are matches.
// n          — N-back level (1, 2, or 3)
// totalLength — total letters in the sequence (lead-in + judgeable)
const generateBalancedSequence = (n, totalLength) => {
  const letters = 'ABCDEFGHIJKLMNO'.split('');
  const sequence = [];
  const judgeableCount = totalLength - n;
  const targetMatches = Math.round(judgeableCount * 0.5);

  // Lead-in letters: random, unconstrained
  for (let i = 0; i < n; i++) {
    sequence.push(letters[Math.floor(Math.random() * letters.length)]);
  }

  let matchesRemaining = targetMatches;
  let noMatchesRemaining = judgeableCount - targetMatches;

  // Judgeable letters: controlled match/no-match ratio
  for (let i = n; i < totalLength; i++) {
    const total = matchesRemaining + noMatchesRemaining;
    const matchProbability = matchesRemaining / total;
    const shouldMatch = Math.random() < matchProbability;

    if (shouldMatch) {
      // Copy the letter from N positions ago to create a match
      sequence.push(sequence[i - n]);
      matchesRemaining -= 1;
    } else {
      // Pick a letter that is NOT the same as sequence[i - n] (no accidental match)
      const nBackLetter = sequence[i - n];
      const candidates = letters.filter((l) => l !== nBackLetter);
      sequence.push(candidates[Math.floor(Math.random() * candidates.length)]);
      noMatchesRemaining -= 1;
    }
  }

  return sequence;
};

// Determine whether position `index` in the sequence is a match
const isMatch = (sequence, index, n) => {
  if (index < n) return false;
  return sequence[index] === sequence[index - n];
};

// ─── Component ───────────────────────────────────────────────────────────────

const NBack = ({ difficulty, onComplete }) => {
  const n = getNBackLevel(difficulty);
  const SEQUENCE_LENGTH = 15 + n; // n lead-in + 15 judgeable
  const JUDEABLE_COUNT = 15;
  const LEADIN_DELAY_MS = 1500;
  const FEEDBACK_DURATION_MS = 300;

  const [sequence, setSequence] = useState([]);
  // phase: 'idle' | 'leadin' | 'active' | 'done'
  const [phase, setPhase] = useState('idle');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [displayedLetter, setDisplayedLetter] = useState('');
  const [leadInStep, setLeadInStep] = useState(0); // 1-based count of lead-in letters shown
  const [trials, setTrials] = useState(0);
  const [correct, setCorrect] = useState(0);
  const [feedback, setFeedback] = useState(null); // 'correct' | 'incorrect' | null
  const [buttonsDisabled, setButtonsDisabled] = useState(false);

  // Refs to avoid stale closures in timeouts
  const sequenceRef = useRef(sequence);
  const currentIndexRef = useRef(currentIndex);
  const trialsRef = useRef(trials);
  const correctRef = useRef(correct);

  useEffect(() => { sequenceRef.current = sequence; }, [sequence]);
  useEffect(() => { currentIndexRef.current = currentIndex; }, [currentIndex]);
  useEffect(() => { trialsRef.current = trials; }, [trials]);
  useEffect(() => { correctRef.current = correct; }, [correct]);

  // ── Lead-in automation ─────────────────────────────────────────────────────
  useEffect(() => {
    if (phase !== 'leadin') return;

    // currentIndex points to the next letter to display during lead-in (0-based)
    if (currentIndex >= n) {
      // Lead-in complete — transition to active phase with first judgeable letter
      const timer = setTimeout(() => {
        const seq = sequenceRef.current;
        setDisplayedLetter(seq[n]);
        setCurrentIndex(n + 1);
        setPhase('active');
      }, LEADIN_DELAY_MS);
      return () => clearTimeout(timer);
    }

    // Show the next lead-in letter
    const timer = setTimeout(() => {
      const seq = sequenceRef.current;
      setDisplayedLetter(seq[currentIndex]);
      setLeadInStep(currentIndex + 1);
      setCurrentIndex(currentIndex + 1);
    }, LEADIN_DELAY_MS);

    return () => clearTimeout(timer);
  }, [phase, currentIndex, n]);

  // ── Game actions ───────────────────────────────────────────────────────────

  const startGame = () => {
    const seq = generateBalancedSequence(n, SEQUENCE_LENGTH);
    setSequence(seq);
    sequenceRef.current = seq;
    setPhase('leadin');
    setCurrentIndex(0);
    setLeadInStep(0);
    setDisplayedLetter('');
    setTrials(0);
    setCorrect(0);
    setFeedback(null);
    setButtonsDisabled(false);
  };

  // Advance to the next judgeable letter (or finish if sequence is exhausted)
  const advanceLetter = (newCorrect, newTrials) => {
    const seq = sequenceRef.current;
    const nextIndex = currentIndexRef.current;

    if (nextIndex >= seq.length) {
      // Sequence complete
      setPhase('done');
      setDisplayedLetter('');
      onComplete({
        trials_presented: newTrials,
        trials_correct: newCorrect,
        avg_response_ms: 0,
      });
    } else {
      setDisplayedLetter(seq[nextIndex]);
      setCurrentIndex(nextIndex + 1);
    }
  };

  const recordResponse = (playerSaysMatch) => {
    if (phase !== 'active' || buttonsDisabled || !displayedLetter) return;

    setButtonsDisabled(true);

    // currentIndex has already been incremented past the displayed letter, so
    // the displayed letter lives at currentIndex - 1
    const displayedIndex = currentIndexRef.current - 1;
    const shouldMatch = isMatch(sequenceRef.current, displayedIndex, n);
    const wasCorrect = playerSaysMatch === shouldMatch;

    const newTrials = trialsRef.current + 1;
    const newCorrect = correctRef.current + (wasCorrect ? 1 : 0);

    setTrials(newTrials);
    setCorrect(newCorrect);
    trialsRef.current = newTrials;
    correctRef.current = newCorrect;

    setFeedback(wasCorrect ? 'correct' : 'incorrect');

    setTimeout(() => {
      setFeedback(null);
      setButtonsDisabled(false);
      advanceLetter(newCorrect, newTrials);
    }, FEEDBACK_DURATION_MS);
  };

  const handleMatch = () => recordResponse(true);
  const handleNoMatch = () => recordResponse(false);

  // ── Render ─────────────────────────────────────────────────────────────────

  if (phase === 'idle') {
    return (
      <Card>
        <h2 style={{ marginBottom: 'var(--space-3)' }}>{n}-Back Task</h2>
        <p style={{ marginBottom: 'var(--space-2)', fontSize: 'var(--text-body-sm)' }}>
          A sequence of letters will appear one at a time. Press <strong>Match</strong> when
          the current letter is the same as the letter shown <strong>{n} step{n > 1 ? 's' : ''} ago</strong>.
          Press <strong>No Match</strong> if it is different.
        </p>
        <p style={{ marginBottom: 'var(--space-6)', color: 'var(--color-text-secondary)', fontSize: 'var(--text-body-sm)' }}>
          The first {n} letter{n > 1 ? 's' : ''} will appear automatically so you can start building your memory. Buttons appear after that.
        </p>
        <Button onClick={startGame} variant="primary">
          Start
        </Button>
      </Card>
    );
  }

  if (phase === 'done') {
    return (
      <Card>
        <h2>Exercise Complete</h2>
        <p>You got {correct} out of {trials} correct!</p>
      </Card>
    );
  }

  // Lead-in and active phases share the same layout
  const isLeadIn = phase === 'leadin';
  const progressValue = isLeadIn ? 0 : trials;

  return (
    <Card>
      <div style={{ marginBottom: 'var(--space-4)' }}>
        <ProgressBar value={progressValue} max={JUDEABLE_COUNT} />
      </div>

      <div style={{ textAlign: 'center', padding: 'var(--space-8)' }}>
        {/* Instruction line */}
        <p style={{ fontSize: 'var(--text-body-sm)', marginBottom: 'var(--space-4)', color: 'var(--color-text-secondary)' }}>
          {isLeadIn
            ? `Memorising… (${leadInStep} of ${n})`
            : `${n}-Back: press Match if this letter matches the one shown ${n} step${n > 1 ? 's' : ''} ago`}
        </p>

        {/* Large letter display */}
        <div style={{
          fontSize: 'var(--text-display)',
          marginBottom: 'var(--space-6)',
          height: '120px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          {displayedLetter}
        </div>

        {/* Buttons — shown only during active phase */}
        {isLeadIn ? (
          <p style={{
            textAlign: 'center',
            color: 'var(--color-text-secondary)',
            fontSize: 'var(--text-body-sm)',
            marginBottom: 'var(--space-4)',
          }}>
            Watch carefully — buttons will appear shortly
          </p>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 'var(--space-4)',
            marginBottom: 'var(--space-4)',
          }}>
            <Button
              onClick={handleMatch}
              variant="primary"
              disabled={buttonsDisabled || !displayedLetter}
            >
              Match
            </Button>
            <Button
              onClick={handleNoMatch}
              variant="secondary"
              disabled={buttonsDisabled || !displayedLetter}
            >
              No Match
            </Button>
          </div>
        )}

        {/* Per-trial feedback */}
        {feedback && (
          <div className={`answer-feedback ${feedback}`}>
            {feedback === 'correct' ? 'Correct!' : 'Incorrect'}
          </div>
        )}
      </div>
    </Card>
  );
};

export default NBack;
