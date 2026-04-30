/**
 * GoNoGo — Full Go/No-Go Task implementation (build-v0.1, 2026-04-04)
 *
 * Measures: Processing Speed + Inhibitory Control (Attention & Inhibitory Control domain)
 *
 * Mechanic: 20 stimuli per round. Player taps for the Go target (green circle).
 * Player withholds for No-Go stimuli (other shapes/colours). Scored by signal
 * detection logic: hits + correct_rejections − false_alarms − misses.
 *
 * Props:
 *   difficulty   {number} 1–10 — mapped to Easy/Medium/Hard tiers
 *   onComplete   {(payload) => void} — called with result object when round ends
 *
 * Payload shape:
 *   { trials_presented, trials_correct, avg_response_ms, accuracy,
 *     hits, misses, false_alarms, correct_rejections }
 */

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import ProgressBar from '../ui/ProgressBar';

// ─── Difficulty configuration ─────────────────────────────────────────────────

/**
 * Map numeric difficulty prop (1–10) to timing and stimulus parameters.
 */
function getDifficultyConfig(difficulty) {
  if (difficulty <= 3) {
    return { label: 'Easy', displayMs: 1000, noGoCount: 1, goRatio: 0.75 };
  }
  if (difficulty <= 6) {
    return { label: 'Medium', displayMs: 700, noGoCount: 2, goRatio: 0.70 };
  }
  return { label: 'Hard', displayMs: 450, noGoCount: 3, goRatio: 0.65 };
}

// ─── CSS variable resolver ────────────────────────────────────────────────────

function resolveCssVar(varName) {
  return getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
}

// ─── Stimulus definitions ──────────────────────────────────────────────────────

const GO_STIMULUS = {
  shape: 'circle',
  colorVar: '--color-success',
  label: 'green circle',
  isGo: true,
};

// No-Go options in order — Easy uses [0], Medium [0,1], Hard [0,1,2]
const NOGO_STIMULI = [
  { shape: 'circle',   colorVar: '--color-error',    label: 'red circle',      isGo: false },
  { shape: 'square',   colorVar: '--color-primary',  label: 'blue square',     isGo: false },
  { shape: 'triangle', colorVar: '--color-warning',  label: 'orange triangle', isGo: false },
];

// ─── Stimulus generation ───────────────────────────────────────────────────────

/**
 * Build a shuffled sequence of 20 stimuli according to the difficulty config.
 * Exported for unit-testing.
 *
 * @param {object} config  { noGoCount: number, goRatio: number }
 * @returns {Array<object>} stimulus objects with isGo, shape, colorVar, label
 */
export function generateStimuli(config) {
  const total = 20;
  const numGo   = Math.round(total * config.goRatio);
  const numNoGo = total - numGo;

  const noGoVariants = NOGO_STIMULI.slice(0, config.noGoCount);
  const sequence = [];

  for (let i = 0; i < numGo; i++) {
    sequence.push({ ...GO_STIMULUS });
  }
  for (let i = 0; i < numNoGo; i++) {
    // Distribute No-Go variants evenly (cycles through available types)
    sequence.push({ ...noGoVariants[i % noGoVariants.length] });
  }

  // Fisher-Yates shuffle
  for (let i = sequence.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [sequence[i], sequence[j]] = [sequence[j], sequence[i]];
  }

  return sequence;
}

// ─── Scoring ───────────────────────────────────────────────────────────────────

/**
 * Compute the result payload from raw stats.
 * Exported for unit-testing.
 *
 * @param {object} stats { hits, misses, falseAlarms, correctRejections, responseTimes }
 * @returns {object} payload ready for onComplete
 */
export function computeResult(stats) {
  const { hits, misses, falseAlarms, correctRejections, responseTimes } = stats;
  const total = hits + misses + falseAlarms + correctRejections;

  const rawScore      = hits + correctRejections - falseAlarms - misses;
  const accuracy      = total > 0 ? Math.max(0, rawScore) / total : 0;
  const trialsCorrect = hits + correctRejections;
  const avgResponseMs = responseTimes.length > 0
    ? Math.round(responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length)
    : 0;

  return {
    trials_presented:  total,
    trials_correct:    trialsCorrect,
    avg_response_ms:   avgResponseMs,
    accuracy,            // 0.0–1.0 — used by BaselineGameWrapper
    hits,
    misses,
    false_alarms:      falseAlarms,
    correct_rejections: correctRejections,
  };
}

// ─── Shape renderer ────────────────────────────────────────────────────────────

function Shape({ shape, colorVar, size = 140 }) {
  const color = resolveCssVar(colorVar);
  const half = size / 2;

  if (shape === 'circle') {
    return (
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden="true">
        <circle cx={half} cy={half} r={half - 4} fill={color} />
      </svg>
    );
  }

  if (shape === 'square') {
    return (
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden="true">
        <rect x={8} y={8} width={size - 16} height={size - 16} rx={12} fill={color} />
      </svg>
    );
  }

  if (shape === 'triangle') {
    const pts = `${half},${8} ${size - 8},${size - 8} ${8},${size - 8}`;
    return (
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden="true">
        <polygon points={pts} fill={color} />
      </svg>
    );
  }

  return null;
}

// ─── Component ────────────────────────────────────────────────────────────────

const ISI_MS   = 400;  // blank inter-stimulus interval
const TOTAL    = 20;   // stimuli per round

const GoNoGo = ({ difficulty, onComplete }) => {
  const config = useMemo(() => getDifficultyConfig(difficulty), [difficulty]);

  // ── State machine ────────────────────────────────────────────────────────────
  // phase: 'instructions' | 'isi' | 'stimulus' | 'result'
  const [phase, setPhase]             = useState('instructions');
  const [stimuli, setStimuli]         = useState(null);
  const [currentIdx, setCurrentIdx]   = useState(0);
  const [stimulusVisible, setStimulusVisible] = useState(false);
  const [result, setResult]           = useState(null);

  // ── Mutable game state (refs — avoid stale closures inside timers) ───────────
  const respondedRef    = useRef(false);   // has user responded in current window?
  const stimStartRef    = useRef(0);       // performance.now() when stimulus appeared
  const stimTimerRef    = useRef(null);    // ID of the stimulus display timer
  const firstGoSeen     = useRef(false);   // for first-play hint logic
  const hasResponded    = useRef(false);   // has user responded at least once (hint)

  // Mutable running stats — accumulated without re-renders
  const statsRef = useRef({
    hits:              0,
    misses:            0,
    falseAlarms:       0,
    correctRejections: 0,
    responseTimes:     [],
  });

  // ── Generate stimuli on start ────────────────────────────────────────────────
  const start = useCallback(() => {
    const s = generateStimuli(config);
    setStimuli(s);
    setCurrentIdx(0);
    statsRef.current = { hits: 0, misses: 0, falseAlarms: 0, correctRejections: 0, responseTimes: [] };
    respondedRef.current = false;
    firstGoSeen.current  = false;
    hasResponded.current = false;
    setPhase('isi');
  }, [config]);

  // ── Advance to next stimulus or finish ───────────────────────────────────────
  const advance = useCallback((nextIdx) => {
    if (nextIdx >= TOTAL) {
      // Round complete — compute final result and show result screen
      const r = computeResult(statsRef.current);
      setResult(r);
      setPhase('result');
    } else {
      respondedRef.current = false;
      setCurrentIdx(nextIdx);
      setPhase('isi');
    }
  }, []);

  // ── ISI effect — blank screen for ISI_MS, then show stimulus ────────────────
  useEffect(() => {
    if (phase !== 'isi') return;

    setStimulusVisible(false);
    const t = setTimeout(() => {
      stimStartRef.current = performance.now();
      setStimulusVisible(true);
      setPhase('stimulus');
    }, ISI_MS);

    return () => clearTimeout(t);
  }, [phase, currentIdx]); // re-run when we enter ISI for a new stimulus

  // ── Stimulus display timer effect ────────────────────────────────────────────
  useEffect(() => {
    if (phase !== 'stimulus' || !stimuli) return;

    const stim = stimuli[currentIdx];

    // Track whether first Go stimulus has been seen (for hint)
    if (stim.isGo && !firstGoSeen.current) {
      firstGoSeen.current = true;
    }

    stimTimerRef.current = setTimeout(() => {
      // Window expired without a response
      setStimulusVisible(false);
      if (!respondedRef.current) {
        if (stim.isGo) {
          statsRef.current.misses++;
        } else {
          statsRef.current.correctRejections++;
        }
      }
      // Brief blank before advancing to next ISI
      const advTimer = setTimeout(() => advance(currentIdx + 1), 200);
      return () => clearTimeout(advTimer);
    }, config.displayMs);

    return () => clearTimeout(stimTimerRef.current);
  }, [phase, currentIdx, stimuli, config.displayMs, advance]);

  // ── Handle tap / click ───────────────────────────────────────────────────────
  const handleResponse = useCallback(() => {
    if (phase !== 'stimulus' || !stimulusVisible || respondedRef.current || !stimuli) return;

    respondedRef.current = true;
    hasResponded.current = true;
    clearTimeout(stimTimerRef.current);

    const rt   = performance.now() - stimStartRef.current;
    const stim = stimuli[currentIdx];

    if (stim.isGo) {
      statsRef.current.hits++;
      statsRef.current.responseTimes.push(Math.round(rt));
    } else {
      statsRef.current.falseAlarms++;
    }

    setStimulusVisible(false);

    // Brief gap, then advance
    const t = setTimeout(() => advance(currentIdx + 1), 250);
    return () => clearTimeout(t);
  }, [phase, stimulusVisible, stimuli, currentIdx, advance]);

  // ── Keyboard support (spacebar = tap) ────────────────────────────────────────
  useEffect(() => {
    const onKey = (e) => {
      if (e.code === 'Space') {
        const active = document.activeElement;
        const tag = active ? active.tagName : '';
        if (tag === 'INPUT' || tag === 'TEXTAREA' || (active && active.isContentEditable)) return;
        e.preventDefault();
        handleResponse();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [handleResponse]);

  // ── Done: call onComplete ────────────────────────────────────────────────────
  const handleDone = useCallback(() => {
    if (result) onComplete(result);
  }, [result, onComplete]);

  // ─────────────────────────────────────────────────────────────────────────────
  // RENDER: Instructions
  // ─────────────────────────────────────────────────────────────────────────────

  if (phase === 'instructions') {
    const noGoVariants = NOGO_STIMULI.slice(0, config.noGoCount);
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: 'var(--space-4) 0' }}>
          <h2 style={{ marginBottom: 'var(--space-2)' }}>Go / No-Go</h2>
          <p style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--space-6)' }}>
            {config.label} · {TOTAL} stimuli · {config.displayMs}ms window
          </p>

          {/* Go stimulus instruction */}
          <div style={{
            display: 'inline-flex',
            flexDirection: 'column',
            alignItems: 'center',
            background: 'var(--color-success-muted)',
            border: '1px solid var(--color-success)',
            borderRadius: 'var(--radius-lg, 12px)',
            padding: 'var(--space-4) var(--space-6)',
            marginBottom: 'var(--space-4)',
          }}>
            <Shape shape="circle" colorVar="--color-success" size={80} />
            <p style={{
              marginTop: 'var(--space-2)',
              fontWeight: 'var(--weight-bold)',
              color: 'var(--color-success)',
              fontSize: 'var(--text-body-sm)',
            }}>
              Tap for this ✓
            </p>
          </div>

          {/* No-Go stimuli instruction */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            marginBottom: 'var(--space-6)',
          }}>
            <p style={{
              color: 'var(--color-text-secondary)',
              marginBottom: 'var(--space-3)',
              fontSize: 'var(--text-body-sm)',
              textTransform: 'uppercase',
              letterSpacing: 'var(--tracking-wide)',
            }}>
              Ignore everything else
            </p>
            <div style={{ display: 'flex', gap: 'var(--space-3)', justifyContent: 'center' }}>
              {noGoVariants.map((s) => (
                <div key={s.label} style={{ opacity: 0.55 }}>
                  <Shape shape={s.shape} colorVar={s.colorVar} size={52} />
                </div>
              ))}
            </div>
          </div>

          <Button onClick={start} variant="primary" style={{ minWidth: '160px' }}>
            I&apos;m ready
          </Button>
        </div>
      </Card>
    );
  }

  // ─────────────────────────────────────────────────────────────────────────────
  // RENDER: Game (ISI + stimulus phases)
  // ─────────────────────────────────────────────────────────────────────────────

  if (phase === 'isi' || phase === 'stimulus') {
    const stim = stimuli ? stimuli[currentIdx] : null;
    const showHint = stimulusVisible && stim && stim.isGo && firstGoSeen.current && !hasResponded.current;

    return (
      <div>
        {/* Progress */}
        <div style={{ marginBottom: 'var(--space-4)' }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: 'var(--text-body-sm)',
            color: 'var(--color-text-secondary)',
            marginBottom: 'var(--space-1)',
          }}>
            <span>{currentIdx + 1} / {TOTAL}</span>
            <span>{config.label}</span>
          </div>
          <ProgressBar value={currentIdx} max={TOTAL} />
        </div>

        {/* Tap zone — full-width, large enough for mobile */}
        <div
          onClick={handleResponse}
          role="button"
          tabIndex={0}
          aria-label="Tap zone — press for green circle"
          style={{
            minHeight: '340px',
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            borderRadius: 'var(--radius-lg, 12px)',
            background: 'var(--color-bg-raised)',
            border: '1px solid var(--color-border-default)',
            userSelect: 'none',
            WebkitUserSelect: 'none',
            position: 'relative',
          }}
        >
          {/* Stimulus */}
          {stimulusVisible && stim ? (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              animation: 'gng-appear 0.08s ease-out',
            }}>
              <Shape shape={stim.shape} colorVar={stim.colorVar} size={140} />
              {showHint && (
                <p style={{
                  marginTop: 'var(--space-3)',
                  color: 'var(--color-text-secondary)',
                  fontSize: 'var(--text-body-sm)',
                  animation: 'gng-fade 0.3s ease-in',
                }}>
                  tap! ↑
                </p>
              )}
            </div>
          ) : (
            /* ISI dot */
            <div style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: 'var(--color-neutral-500)',
            }} />
          )}
        </div>

        <style>{`
          @keyframes gng-appear {
            from { transform: scale(0.88); opacity: 0; }
            to   { transform: scale(1);    opacity: 1; }
          }
          @keyframes gng-fade {
            from { opacity: 0; }
            to   { opacity: 1; }
          }
        `}</style>
      </div>
    );
  }

  // ─────────────────────────────────────────────────────────────────────────────
  // RENDER: Result
  // ─────────────────────────────────────────────────────────────────────────────

  if (phase === 'result' && result) {
    const accuracyPct = Math.round(result.accuracy * 100);

    const rows = [
      { label: 'Hits',               value: result.hits,               note: 'Go — tapped in time',        good: true  },
      { label: 'Correct rejections', value: result.correct_rejections, note: 'No-Go — correctly withheld', good: true  },
      { label: 'Misses',             value: result.misses,             note: 'Go — not tapped in time',     good: false },
      { label: 'False alarms',       value: result.false_alarms,       note: 'No-Go — tapped by mistake',  good: false },
    ];

    const scoreColor = accuracyPct >= 75 ? 'var(--color-success)'
      : accuracyPct >= 50 ? 'var(--color-warning)'
      : 'var(--color-error)';

    return (
      <Card>
        <div style={{ textAlign: 'center', padding: 'var(--space-2) 0 var(--space-4)' }}>
          <p style={{
            fontSize: 'var(--text-body-sm)',
            color: 'var(--color-text-secondary)',
            textTransform: 'uppercase',
            letterSpacing: 'var(--tracking-wide)',
            marginBottom: 'var(--space-2)',
          }}>
            Round complete
          </p>

          {/* Accuracy */}
          <p style={{
            fontSize: 'clamp(2.5rem, 8vw, 3.5rem)',
            fontWeight: 'var(--weight-bold)',
            color: scoreColor,
            margin: '0 0 var(--space-1)',
            lineHeight: 1,
          }}>
            {accuracyPct}%
          </p>
          <p style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--space-1)' }}>
            accuracy
          </p>

          {/* Avg RT */}
          {result.avg_response_ms > 0 && (
            <p style={{
              color: 'var(--color-text-secondary)',
              fontSize: 'var(--text-body-sm)',
              marginBottom: 'var(--space-5)',
            }}>
              Avg reaction time: <strong style={{ color: 'var(--color-text-primary)' }}>
                {result.avg_response_ms}ms
              </strong>
            </p>
          )}

          {/* Breakdown table */}
          <div style={{
            background: 'var(--color-bg-raised)',
            border: '1px solid var(--color-border-default)',
            borderRadius: 'var(--radius-lg, 12px)',
            overflow: 'hidden',
            marginBottom: 'var(--space-5)',
            textAlign: 'left',
          }}>
            {rows.map((row, i) => (
              <div key={row.label} style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: 'var(--space-3) var(--space-4)',
                borderTop: i > 0 ? '1px solid var(--color-border-default)' : 'none',
              }}>
                <div>
                  <span style={{
                    fontWeight: 'var(--weight-medium)',
                    color: 'var(--color-text-primary)',
                  }}>
                    {row.label}
                  </span>
                  <span style={{
                    display: 'block',
                    fontSize: 'var(--text-caption)',
                    color: 'var(--color-text-tertiary)',
                  }}>
                    {row.note}
                  </span>
                </div>
                <span style={{
                  fontWeight: 'var(--weight-bold)',
                  fontSize: 'var(--text-h3)',
                  color: row.good
                    ? (row.value > 0 ? 'var(--color-success)' : 'var(--color-text-secondary)')
                    : (row.value > 0 ? 'var(--color-error)' : 'var(--color-text-secondary)'),
                }}>
                  {row.value}
                </span>
              </div>
            ))}
          </div>

          <Button onClick={handleDone} variant="primary" style={{ minWidth: '140px' }}>
            Done
          </Button>
        </div>
      </Card>
    );
  }

  return null;
};

export default GoNoGo;
