import React from 'react';
import Card from '../ui/Card';
import Button from '../ui/Button';

/**
 * Intro screen shown before the baseline test begins.
 * Displays an overview of what to expect and a "Begin" CTA.
 *
 * Props:
 *   gameCount {number} — total number of games in the sequence
 *   onBegin   {() => void} — called when the user clicks Begin
 */
const BaselineIntro = ({ gameCount, onBegin }) => {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '60vh',
      padding: 'var(--space-6)',
    }}>
      <Card style={{ maxWidth: '560px', width: '100%', textAlign: 'center' }}>
        <div style={{ marginBottom: 'var(--space-4)' }}>
          <span style={{ fontSize: '3rem' }}>🧠</span>
        </div>

        <h1 style={{ marginBottom: 'var(--space-3)', fontSize: 'var(--text-heading-lg)' }}>
          Skill Assessment
        </h1>

        <p style={{ marginBottom: 'var(--space-4)', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
          We'll run you through <strong>{gameCount} games</strong> to find your current
          skill level. Each game adapts to your answers as you go, so you'll be challenged
          at just the right level.
        </p>

        <p style={{ marginBottom: 'var(--space-4)', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
          This takes about <strong>5 minutes</strong>. Your results set the starting
          difficulty for future training sessions.
        </p>

        <div style={{
          background: 'var(--color-surface-secondary, #f5f5f5)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-3)',
          marginBottom: 'var(--space-6)',
          fontSize: 'var(--text-body-sm)',
          color: 'var(--color-text-secondary)',
        }}>
          <strong>Note:</strong> This assessment establishes your baseline Brain Health Score.
          It won't count as a regular training session, but your results will determine your
          initial score and starting difficulty.
        </div>

        <Button onClick={onBegin} variant="primary" style={{ width: '100%', padding: 'var(--space-3)' }}>
          Begin Assessment
        </Button>
      </Card>
    </div>
  );
};

export default BaselineIntro;
