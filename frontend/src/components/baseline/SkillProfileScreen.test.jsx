import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import SkillProfileScreen from './SkillProfileScreen';

const defaultResults = [
  { gameKey: 'stroop', gameName: 'Stroop Task', assessedLevel: 1 },
  { gameKey: 'digit_span', gameName: 'Digit Span', assessedLevel: 2 },
  { gameKey: 'nback', gameName: 'Count Back Match', assessedLevel: 3 },
];

describe('SkillProfileScreen', () => {
  it('renders heading', () => {
    render(<SkillProfileScreen results={defaultResults} saving={false} error={null} onSave={vi.fn()} />);
    expect(screen.getByText('Your Skill Profile')).toBeTruthy();
  });

  it('renders all game names', () => {
    render(<SkillProfileScreen results={defaultResults} saving={false} error={null} onSave={vi.fn()} />);
    expect(screen.getByText('Stroop Task')).toBeTruthy();
    expect(screen.getByText('Digit Span')).toBeTruthy();
    expect(screen.getByText('Count Back Match')).toBeTruthy();
  });

  it('renders level labels correctly', () => {
    render(<SkillProfileScreen results={defaultResults} saving={false} error={null} onSave={vi.fn()} />);
    expect(screen.getByText('Easy')).toBeTruthy();
    expect(screen.getByText('Medium')).toBeTruthy();
    expect(screen.getByText('Hard')).toBeTruthy();
  });

  it('renders "Unknown" for unrecognised level', () => {
    const results = [{ gameKey: 'x', gameName: 'X Game', assessedLevel: 99 }];
    render(<SkillProfileScreen results={results} saving={false} error={null} onSave={vi.fn()} />);
    expect(screen.getByText('Unknown')).toBeTruthy();
  });

  it('shows Save button when not saving', () => {
    render(<SkillProfileScreen results={defaultResults} saving={false} error={null} onSave={vi.fn()} />);
    expect(screen.getByRole('button', { name: /save & return/i })).toBeTruthy();
  });

  it('shows Saving... when saving=true', () => {
    render(<SkillProfileScreen results={defaultResults} saving={true} error={null} onSave={vi.fn()} />);
    expect(screen.getByRole('button', { name: /saving/i })).toBeTruthy();
  });

  it('disables button when saving', () => {
    render(<SkillProfileScreen results={defaultResults} saving={true} error={null} onSave={vi.fn()} />);
    const btn = screen.getByRole('button', { name: /saving/i });
    expect(btn.disabled).toBe(true);
  });

  it('calls onSave when Save button is clicked', () => {
    const onSave = vi.fn();
    render(<SkillProfileScreen results={defaultResults} saving={false} error={null} onSave={onSave} />);
    fireEvent.click(screen.getByRole('button', { name: /save & return/i }));
    expect(onSave).toHaveBeenCalledOnce();
  });

  it('shows error message when error is provided', () => {
    render(<SkillProfileScreen results={defaultResults} saving={false} error="network error" onSave={vi.fn()} />);
    expect(screen.getByText(/could not save your results/i)).toBeTruthy();
  });

  it('does not show error message when error is null', () => {
    render(<SkillProfileScreen results={defaultResults} saving={false} error={null} onSave={vi.fn()} />);
    expect(screen.queryByText(/could not save your results/i)).toBeNull();
  });

  it('renders empty results without crashing', () => {
    render(<SkillProfileScreen results={[]} saving={false} error={null} onSave={vi.fn()} />);
    expect(screen.getByText('Your Skill Profile')).toBeTruthy();
  });

  it('renders target emoji', () => {
    render(<SkillProfileScreen results={defaultResults} saving={false} error={null} onSave={vi.fn()} />);
    expect(screen.getByText('🎯')).toBeTruthy();
  });
});
