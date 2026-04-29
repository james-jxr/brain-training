import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import BaselineTransition from './BaselineTransition';

describe('BaselineTransition', () => {
  const defaultProps = {
    completedGameName: 'Count Back Match',
    nextGameName: 'Stroop Challenge',
    gameIndex: 2,
    gameCount: 7,
    onContinue: vi.fn(),
  };

  it('renders the completed game name', () => {
    render(<BaselineTransition {...defaultProps} />);
    expect(screen.getByText('Count Back Match complete')).toBeTruthy();
  });

  it('renders the next game name', () => {
    render(<BaselineTransition {...defaultProps} />);
    expect(screen.getByText('Stroop Challenge')).toBeTruthy();
  });

  it('renders game progress indicator', () => {
    render(<BaselineTransition {...defaultProps} />);
    expect(screen.getByText('Game 2 of 7 done')).toBeTruthy();
  });

  it('renders the checkmark emoji', () => {
    render(<BaselineTransition {...defaultProps} />);
    expect(screen.getByText('✅')).toBeTruthy();
  });

  it('renders Next up label', () => {
    render(<BaselineTransition {...defaultProps} />);
    expect(screen.getByText('Next up:')).toBeTruthy();
  });

  it('renders Continue button', () => {
    render(<BaselineTransition {...defaultProps} />);
    expect(screen.getByText('Continue')).toBeTruthy();
  });

  it('calls onContinue when Continue button is clicked', () => {
    const onContinue = vi.fn();
    render(<BaselineTransition {...defaultProps} onContinue={onContinue} />);
    fireEvent.click(screen.getByText('Continue'));
    expect(onContinue).toHaveBeenCalledTimes(1);
  });

  it('displays correct gameIndex and gameCount', () => {
    render(
      <BaselineTransition
        {...defaultProps}
        gameIndex={5}
        gameCount={7}
      />
    );
    expect(screen.getByText('Game 5 of 7 done')).toBeTruthy();
  });

  it('displays different completedGameName', () => {
    render(
      <BaselineTransition
        {...defaultProps}
        completedGameName="Stroop Challenge"
      />
    );
    expect(screen.getByText('Stroop Challenge complete')).toBeTruthy();
  });
});
