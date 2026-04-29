import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import BaselineTransition from './BaselineTransition';

describe('BaselineTransition', () => {
  const defaultProps = {
    completedGameName: 'Stroop Task',
    nextGameName: 'Digit Span',
    gameIndex: 1,
    gameCount: 3,
    onContinue: vi.fn(),
  };

  it('shows completed game name', () => {
    render(<BaselineTransition {...defaultProps} />);
    expect(screen.getByText(/Stroop Task complete/i)).toBeTruthy();
  });

  it('shows progress text with gameIndex and gameCount', () => {
    render(<BaselineTransition {...defaultProps} />);
    expect(screen.getByText(/Game 1 of 3 done/i)).toBeTruthy();
  });

  it('shows next game name', () => {
    render(<BaselineTransition {...defaultProps} />);
    expect(screen.getByText('Digit Span')).toBeTruthy();
  });

  it('shows "Next up:" label', () => {
    render(<BaselineTransition {...defaultProps} />);
    expect(screen.getByText('Next up:')).toBeTruthy();
  });

  it('calls onContinue when Continue button clicked', () => {
    const onContinue = vi.fn();
    render(<BaselineTransition {...defaultProps} onContinue={onContinue} />);
    fireEvent.click(screen.getByRole('button', { name: /continue/i }));
    expect(onContinue).toHaveBeenCalledOnce();
  });

  it('renders checkmark emoji', () => {
    render(<BaselineTransition {...defaultProps} />);
    expect(screen.getByText('✅')).toBeTruthy();
  });

  it('renders with gameIndex=0 without crashing', () => {
    render(<BaselineTransition {...defaultProps} gameIndex={0} gameCount={2} />);
    expect(screen.getByText(/Game 0 of 2 done/i)).toBeTruthy();
  });
});
