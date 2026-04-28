import React, { useState, useCallback, useRef } from 'react';
import Button from '../ui/Button';
import Card from '../ui/Card';
import ProgressBar from '../ui/ProgressBar';

// ─── Shape properties ─────────────────────────────────────────────────────────
const SHAPES = ['circle', 'triangle', 'square', 'diamond'];
const COLORS  = ['#E07B39', '#3B82F6']; // orange, blue
const SIZES   = ['large', 'small'];
const FILLS   = ['solid', 'outline'];

const STUDY_PER_GROUP = 3;
const TOTAL_TRIALS    = 12;
const NUM_ROUNDS      = 3;
const TRIALS_PER_ROUND = Math.round(TOTAL_TRIALS / NUM_ROUNDS);

// ─── Classification rules ────────────────────────────────────────────────────
const RULES = {
  easy: [
    { id: 'color',  fn: s => s.color === COLORS[0] ? 'A' : 'B' },
    { id: 'size',   fn: s => s.size  === 'large'   ? 'A' : 'B' },
    { id: 'round',  fn: s => s.shape === 'circle'  ? 'A' : 'B' },
  ],
  medium: [
    { id: 'color+size',  fn: s => (s.color === COLORS[0]) === (s.size === 'large')  ? 'A' : 'B' },
    { id: 'fill+color',  fn: s => s.fill === 'solid' && s.color === COLORS[0]       ? 'A' : 'B' },
    { id: 'shape+size',  fn: s => ['circle', 'diamond'].includes(s.shape) && s.size === 'large' ? 'A' : 'B' },
  ],
  hard: [
    { id: 'xor-color-round', fn: s => ((s.color === COLORS[0]) !== (s.shape === 'circle'))       ? 'A' : 'B' },
    { id: 'xor-size-fill',   fn: s => ((s.size === 'large')     !== (s.fill === 'solid'))         ? 'A' : 'B' },
    { id: 'three-prop',      fn: s => s.size === 'large' && s.fill === 'solid' && s.color === COLORS[0] ? 'A' : 'B' },
  ],
};

// ─── Helpers ──────────────────────────────────────────────────────────────────
function pickRandom(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

function makeShape() {
  return { shape: pickRandom(SHAPES), color: pickRandom(COLORS), size: pickRandom(SIZES), fill: pickRandom(FILLS) };
}

function makeShapes(classifyFn, group, count) {
  const result = [];
  let attempts = 0;
  while (result.length < count && attempts < 500) {
    attempts++;
    const s = makeShape();
    if (classifyFn(s) !== group) continue;
    const dupe = result.some(e =>
      e.shape === s.shape && e.color === s.color && e.size === s.size && e.fill === s.fill
    );
    if (!dupe) result.push(s);
  }
  return result;
}

function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function buildRoundTrials(ruleFn, trialsPerRound) {
  const half = Math.ceil(trialsPerRound / 2);
  const rest = trialsPerRound - half;
  const as = makeShapes(ruleFn, 'A', half);
  const bs = makeShapes(ruleFn, 'B', rest);
  return shuffle([...as, ...bs]);
}

// ─── SVG shape renderer ───────────────────────────────────────────────────────
function ShapeIcon({ shape, color, size, fill }) {
  const dim  = size === 'large' ? 52 : 32;
  const half = dim / 2;
  const sw   = 3;
  const fillColor = fill === 'solid' ? color : 'none';

  const props = { width: dim, height: dim, viewBox: `0 0 ${dim} ${dim}`, style: { display: 'block' } };

  if (shape === 'circle') return (
    <svg {...props}><circle cx={half} cy={half} r={half - sw} fill={fillColor} stroke={color} strokeWidth={sw} /></svg>
  );
  if (shape === 'square') return (
    <svg {...props}><rect x={sw} y={sw} width={dim - sw * 2} height={dim - sw * 2} fill={fillColor} stroke={color} strokeWidth={sw} /></svg>
  );
  if (shape === 'triangle') {
    const pts = `${half},${sw} ${dim - sw},${dim - sw} ${sw},${dim - sw}`;
    return <svg {...props}><polygon points={pts} fill={fillColor} stroke={color} strokeWidth={sw} /></svg>;
  }
  if (shape === 'diamond') {
    const pts = `${half},${sw} ${dim - sw},${half} ${half},${dim - sw} ${sw},${half}`;
    return <svg {...props}><polygon points={pts} fill={fillColor} stroke={color} strokeWidth={sw} /></svg>;
  }
  return null;
}

// ─── Component ────────────────────────────────────────────────────────────────
const VisualCategorisation = ({ difficulty, onComplete }) => {
  const tier = difficulty <= 3 ? 'easy' : difficulty <= 6 ? 'medium' : 'hard';

  const [rule] = useState(() => pickRandom(RULES[tier]));

  const [allRoundTrials] = useState(() => {
    const rounds = [];
    for (let r = 0; r < NUM_ROUNDS; r++) {
      rounds.push(buildRoundTrials(rule.fn, TRIALS_PER_ROUND));
    }
    return rounds;
  });

  const [examplesA] = useState(() => makeShapes(rule.fn, 'A', STUDY_PER_GROUP));
  const [examplesB] = useState(() => makeShapes(rule.fn, 'B', STUDY_PER_GROUP));

  // phase: 'study' | 'sort' | 'interstitial'
  const [phase,    setPhase]    = useState('study');
  const [round,    setRound]    = useState(0); // 0-indexed current round
  const [idx,      setIdx]      = useState(0); // trial index within current round
  const [feedback, setFeedback] = useState(null);

  const correctRef  = useRef(0);
  const totalTrialsRef = useRef(0);
  const startRef    = useRef(null);
  const timesRef    = useRef([]);

  const handleStart = () => {
    startRef.current = Date.now();
    setPhase('sort');
  };

  const handleContinueRound = () => {
    startRef.current = Date.now();
    setPhase('sort');
  };

  const handleAnswer = useCallback((group) => {
    if (feedback) return;

    const rt = Date.now() - startRef.current;
    timesRef.current.push(rt);
    startRef.current = Date.now();

    const currentTrials = allRoundTrials[round];
    const shape    = currentTrials[idx];
    const expected = rule.fn(shape);
    const ok       = group === expected;

    if (ok) correctRef.current += 1;
    totalTrialsRef.current += 1;
    setFeedback(ok ? 'correct' : 'wrong');

    setTimeout(() => {
      setFeedback(null);
      const isLastTrialInRound = idx + 1 >= currentTrials.length;

      if (isLastTrialInRound) {
        const isLastRound = round + 1 >= NUM_ROUNDS;
        if (isLastRound) {
          const avgMs = timesRef.current.length
            ? Math.round(timesRef.current.reduce((a, b) => a + b, 0) / timesRef.current.length)
            : 0;
          onComplete({
            trials_presented: totalTrialsRef.current,
            trials_correct:   correctRef.current,
            avg_response_ms:  avgMs,
          });
        } else {
          setRound(r => r + 1);
          setIdx(0);
          setPhase('interstitial');
        }
      } else {
        setIdx(i => i + 1);
      }
    }, 500);
  }, [feedback, idx, round, allRoundTrials, rule, onComplete]);

  // ── Study phase ──────────────────────────────────────────────────────────────
  if (phase === 'study') {
    return (
      <Card>
        <div style={{ textAlign: 'center', marginBottom: 'var(--space-5)' }}>
          <h2 style={{ marginBottom: 'var(--space-2)' }}>Shape Sort</h2>
          <p style={{ fontSize: 'var(--text-body-sm)', color: 'var(--color-text-secondary)' }}>
            Study the two groups — work out the rule — then sort the new shapes.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)', marginBottom: 'var(--space-6)' }}>
          {[{ label: 'Group A', examples: examplesA }, { label: 'Group B', examples: examplesB }].map(({ label, examples }) => (
            <div key={label} style={{
              border: '2px solid var(--color-border-default)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-4)',
              textAlign: 'center',
            }}>
              <p style={{ fontWeight: 600, fontSize: 'var(--text-body-sm)', marginBottom: 'var(--space-3)' }}>{label}</p>
              <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 'var(--space-3)', flexWrap: 'wrap', minHeight: 60 }}>
                {examples.map((s, i) => <ShapeIcon key={i} {...s} />)}
              </div>
            </div>
          ))}
        </div>

        <Button onClick={handleStart} variant="primary" style={{ width: '100%' }}>
          Start Sorting
        </Button>
      </Card>
    );
  }

  // ── Interstitial phase ───────────────────────────────────────────────────────
  if (phase === 'interstitial') {
    return (
      <Card>
        <div style={{
          textAlign: 'center',
          padding: 'var(--space-8) 0',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 'var(--space-4)',
        }}>
          <p style={{
            fontSize: 'var(--text-body-sm)',
            color: 'var(--color-text-secondary)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            fontWeight: 600,
          }}>
            Round complete
          </p>
          <h2 style={{ margin: 0 }}>
            Round {round + 1} of {NUM_ROUNDS}
          </h2>
          <p style={{
            fontSize: 'var(--text-body-sm)',
            color: 'var(--color-text-secondary)',
          }}>
            {correctRef.current} correct so far
          </p>
          <Button onClick={handleContinueRound} variant="primary" style={{ marginTop: 'var(--space-4)', minWidth: 160 }}>
            Continue
          </Button>
        </div>
      </Card>
    );
  }

  // ── Sort phase ───────────────────────────────────────────────────────────────
  const currentTrials = allRoundTrials[round];
  const current = currentTrials[idx];

  return (
    <Card>
      <div style={{ marginBottom: 'var(--space-4)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2)' }}>
          <p style={{
            fontSize: 'var(--text-body-sm)',
            color: 'var(--color-text-secondary)',
            fontWeight: 600,
            margin: 0,
          }}>
            Round {round + 1}/{NUM_ROUNDS}
          </p>
          <p style={{ fontSize: 'var(--text-body-sm)', color: 'var(--color-text-secondary)', margin: 0 }}>
            {idx + 1} / {currentTrials.length}
          </p>
        </div>
        <ProgressBar value={idx} max={currentTrials.length} />
      </div>

      <div style={{ textAlign: 'center', padding: 'var(--space-6) 0' }}>
        <p style={{ fontSize: 'var(--text-body-sm)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-6)' }}>
          Which group does this belong to?
        </p>

        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: 100,
          height: 100,
          borderRadius: 'var(--radius-lg)',
          background: 'var(--color-bg-subtle, #f9fafb)',
          border: `2px solid ${feedback === 'correct' ? 'var(--color-success)' : feedback === 'wrong' ? 'var(--color-error)' : 'transparent'}`,
          marginBottom: 'var(--space-8)',
          transition: 'border-color 0.15s',
        }}>
          {current && <ShapeIcon {...current} />}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
          <Button onClick={() => handleAnswer('A')} variant="secondary" disabled={!!feedback}>Group A</Button>
          <Button onClick={() => handleAnswer('B')} variant="secondary" disabled={!!feedback}>Group B</Button>
        </div>
      </div>
    </Card>
  );
};

export default VisualCategorisation;
