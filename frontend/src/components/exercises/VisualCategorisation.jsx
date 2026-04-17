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

// ─── Classification rules ────────────────────────────────────────────────────
// Each rule defines which shapes go in Group A vs B.
// The user has to infer the rule from examples.
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
function pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

function makeShape() {
  return { shape: pick(SHAPES), color: pick(COLORS), size: pick(SIZES), fill: pick(FILLS) };
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

  const [rule]      = useState(() => pick(RULES[tier]));
  const [trialList] = useState(() => {
    const half = TOTAL_TRIALS / 2;
    const as   = makeShapes(rule.fn, 'A', half);
    const bs   = makeShapes(rule.fn, 'B', half);
    return shuffle([...as, ...bs]);
  });

  // Re-derive study examples using the SAME rule as trials
  const [examplesA] = useState(() => makeShapes(rule.fn, 'A', STUDY_PER_GROUP));
  const [examplesB] = useState(() => makeShapes(rule.fn, 'B', STUDY_PER_GROUP));

  const [phase,    setPhase]    = useState('study'); // 'study' | 'sort'
  const [idx,      setIdx]      = useState(0);
  const [feedback, setFeedback] = useState(null);    // null | 'correct' | 'wrong'

  const correctRef  = useRef(0);
  const startRef    = useRef(null);
  const timesRef    = useRef([]);

  const handleStart = () => {
    startRef.current = Date.now();
    setPhase('sort');
  };

  const handleAnswer = useCallback((group) => {
    if (feedback) return;

    const rt = Date.now() - startRef.current;
    timesRef.current.push(rt);
    startRef.current = Date.now();

    const shape    = trialList[idx];
    const expected = rule.fn(shape);
    const ok       = group === expected;

    if (ok) correctRef.current += 1;
    setFeedback(ok ? 'correct' : 'wrong');

    setTimeout(() => {
      setFeedback(null);
      if (idx + 1 >= trialList.length) {
        const avgMs = timesRef.current.length
          ? Math.round(timesRef.current.reduce((a, b) => a + b, 0) / timesRef.current.length)
          : 0;
        onComplete({
          trials_presented: trialList.length,
          trials_correct:   correctRef.current,
          avg_response_ms:  avgMs,
        });
      } else {
        setIdx(i => i + 1);
      }
    }, 500);
  }, [feedback, idx, trialList, rule, onComplete]);

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

  // ── Sort phase ───────────────────────────────────────────────────────────────
  const current = trialList[idx];

  return (
    <Card>
      <div style={{ marginBottom: 'var(--space-4)' }}>
        <ProgressBar value={idx} max={trialList.length} />
        <p style={{ fontSize: 'var(--text-body-sm)', color: 'var(--color-text-secondary)', marginTop: 'var(--space-1)', textAlign: 'right' }}>
          {idx + 1} / {trialList.length}
        </p>
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
