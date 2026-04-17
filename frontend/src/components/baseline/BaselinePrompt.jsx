import React from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../ui/Button';

/**
 * First-login banner/modal prompting the user to take the baseline test.
 * Appears on the Dashboard when `has_completed_baseline` is false.
 * "Skip for now" dismisses it for the current session only (parent manages
 * dismissed state in React state — not persisted to the backend).
 *
 * Props:
 *   onDismiss {() => void} — called when user clicks "Skip for now"
 */
const BaselinePrompt = ({ onDismiss }) => {
  const navigate = useNavigate();

  return (
    <div style={{
      background: 'linear-gradient(135deg, var(--color-primary, #6366f1) 0%, #8b5cf6 100%)',
      borderRadius: 'var(--radius-lg)',
      padding: 'var(--space-5)',
      color: '#fff',
      marginBottom: 'var(--space-6)',
      display: 'flex',
      flexDirection: 'column',
      gap: 'var(--space-3)',
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--space-3)' }}>
        <span style={{ fontSize: '2rem', flexShrink: 0 }}>🧠</span>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: '0 0 var(--space-1)', color: '#fff', fontSize: 'var(--text-heading-md)' }}>
            Personalise your experience
          </h2>
          <p style={{ margin: 0, opacity: 0.9, lineHeight: 1.5, fontSize: 'var(--text-body-sm)' }}>
            Take a quick 5-minute Skill Assessment to set your starting difficulty.
            The app will adapt each game to exactly your level.
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
        <Button
          onClick={() => navigate('/baseline')}
          variant="primary"
          style={{
            background: '#fff',
            color: 'var(--color-primary, #6366f1)',
            border: 'none',
            fontWeight: 700,
          }}
        >
          Take Baseline Test
        </Button>
        <Button
          onClick={onDismiss}
          variant="secondary"
          style={{
            background: 'transparent',
            color: '#fff',
            border: '1px solid rgba(255,255,255,0.5)',
          }}
        >
          Skip for now
        </Button>
      </div>
    </div>
  );
};

export default BaselinePrompt;
