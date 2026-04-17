import React from 'react';
import { useNavigate } from 'react-router-dom';
import Card from '../ui/Card';
import Button from '../ui/Button';
import Badge from '../ui/Badge';

const LEVEL_LABELS = { 1: 'Easy', 2: 'Medium', 3: 'Hard' };
const LEVEL_COLORS = {
  1: 'var(--color-success, #22c55e)',
  2: 'var(--color-warning, #f59e0b)',
  3: 'var(--color-error, #ef4444)',
};

/**
 * Final screen shown after all baseline games complete.
 * Displays assessed level per game and a "Save & Return" button.
 *
 * Props:
 *   results     {Array<{gameKey, gameName, assessedLevel}>}
 *   saving      {boolean}  — true while the POST request is in flight
 *   error       {string|null}
 *   onSave      {() => void}
 */
const SkillProfileScreen = ({ results, saving, error, onSave }) => {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '60vh',
      padding: 'var(--space-6)',
    }}>
      <Card style={{ maxWidth: '560px', width: '100%' }}>
        <div style={{ textAlign: 'center', marginBottom: 'var(--space-5)' }}>
          <div style={{ fontSize: '3rem', marginBottom: 'var(--space-2)' }}>🎯</div>
          <h1 style={{ fontSize: 'var(--text-heading-lg)', marginBottom: 'var(--space-2)' }}>
            Your Skill Profile
          </h1>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-body-sm)' }}>
            These levels will set your starting difficulty for each game in future sessions.
          </p>
        </div>

        {/* Results list */}
        <div style={{ marginBottom: 'var(--space-6)' }}>
          {results.map(({ gameKey, gameName, assessedLevel }) => (
            <div
              key={gameKey}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: 'var(--space-3) 0',
                borderBottom: '1px solid var(--color-border, #e5e7eb)',
              }}
            >
              <span style={{ fontWeight: 500 }}>{gameName}</span>
              <span style={{
                fontWeight: 600,
                color: LEVEL_COLORS[assessedLevel] || 'inherit',
                background: 'var(--color-surface-secondary, #f5f5f5)',
                padding: '2px 12px',
                borderRadius: 'var(--radius-full)',
                fontSize: 'var(--text-body-sm)',
              }}>
                {LEVEL_LABELS[assessedLevel] || 'Unknown'}
              </span>
            </div>
          ))}
        </div>

        {error && (
          <div style={{
            marginBottom: 'var(--space-4)',
            padding: 'var(--space-3)',
            background: 'var(--color-error-bg, #fee2e2)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--color-error, #ef4444)',
            fontSize: 'var(--text-body-sm)',
          }}>
            Could not save your results — please try again.
          </div>
        )}

        <Button
          onClick={onSave}
          variant="primary"
          disabled={saving}
          style={{ width: '100%' }}
        >
          {saving ? 'Saving…' : 'Save & Return to Dashboard'}
        </Button>
      </Card>
    </div>
  );
};

export default SkillProfileScreen;
