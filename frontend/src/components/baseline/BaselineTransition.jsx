import React from 'react';
import Card from '../ui/Card';
import Button from '../ui/Button';

/**
 * Short transition screen shown between baseline games.
 *
 * Props:
 *   completedGameName {string} — display name of game just completed
 *   nextGameName      {string} — display name of the next game
 *   gameIndex         {number} — 0-based index of the next game
 *   gameCount         {number} — total number of games
 *   onContinue        {() => void} — called when user clicks Continue
 */
const BaselineTransition = ({
  completedGameName,
  nextGameName,
  gameIndex,
  gameCount,
  onContinue,
}) => {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '60vh',
      padding: 'var(--space-6)',
    }}>
      <Card style={{ maxWidth: '480px', width: '100%', textAlign: 'center' }}>
        <div style={{ marginBottom: 'var(--space-3)', fontSize: '2.5rem' }}>✅</div>

        <h2 style={{ marginBottom: 'var(--space-2)', fontSize: 'var(--text-heading-md)' }}>
          {completedGameName} complete
        </h2>

        <p style={{
          marginBottom: 'var(--space-5)',
          color: 'var(--color-text-secondary)',
          fontSize: 'var(--text-body-sm)',
        }}>
          Game {gameIndex} of {gameCount} done
        </p>

        <div style={{
          background: 'var(--color-surface-secondary, #f5f5f5)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-3)',
          marginBottom: 'var(--space-6)',
        }}>
          <p style={{ margin: 0, fontWeight: 600 }}>Next up:</p>
          <p style={{ margin: 0, color: 'var(--color-text-secondary)' }}>{nextGameName}</p>
        </div>

        <Button onClick={onContinue} variant="primary" style={{ width: '100%' }}>
          Continue
        </Button>
      </Card>
    </div>
  );
};

export default BaselineTransition;
