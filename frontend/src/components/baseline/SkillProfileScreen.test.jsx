import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import SkillProfileScreen from './SkillProfileScreen';

describe('SkillProfileScreen', () => {
  const sampleResults = [
    { gameKey: 'nback', gameName: 'Count Back Match', assessedLevel: 1 },
    { gameKey: 'stroop', gameName: 'Stroop Challenge', assessedLevel: 2 },
    { gameKey: 'go_no_go', gameName: 'Go / No-Go', assessedLevel: 3 },
  ];

  const defaultProps = {
    results: sampleResults,
    saving: false,
    error: null,
    onSave: vi.fn(),
  };

  it('renders the heading', () => {
    render(<SkillProfileScreen {...defaultProps} />);
    expect(screen.getByText('Your Skill Profile')).toBeTruthy();
  });

  it('renders the target emoji', () => {
    render(<SkillProfileScreen {...defaultProps} />);
    expect(screen.getByText('🎯')).toBeTruthy();
  });

  it('renders all game names', () => {
    render(<SkillProfileScreen {...defaultProps} />);
    expect(screen.getByText('Count Back Match')).toBeTruthy();
    expect(screen.getByText('Stroop Challenge')).toBeTruthy();
    expect(screen.getByText('Go / No-Go')).toBeTruthy();
  });

  it('renders level 1 as Easy', () => {
    render(<SkillProfileScreen {...defaultProps} />);
    expect(screen.getByText('Easy')).toBeTruthy();
  });

  it('renders level 2 as Medium', () => {
    render(<SkillProfileScreen {...defaultProps} />);
    expect(screen.getByText('Medium')).toBeTruthy();
  });

  it('renders level 3 as Hard', () => {
    render(<SkillProfileScreen {...defaultProps} />);
    expect(screen.getByText('Hard')).toBeTruthy();
  });

  it('renders unknown level as Unknown', () => {
    const results = [
      { gameKey: 'nback', gameName: 'Count Back Match', assessedLevel: 99 },
    ];
    render(<SkillProfileScreen {...defaultProps} results={results} />);
    expect(screen.getByText('Unknown')).toBeTruthy();
  });

  it('renders Save & Return to Dashboard button when not saving', () => {
    render(<SkillProfileScreen {...defaultProps} />);
    expect(screen.getByText('Save & Return to Dashboard')).toBeTruthy();
  });

  it('renders Saving… text when saving is true', () => {
    render(<SkillProfileScreen {...defaultProps} saving={true} />);
    expect(screen.getByText('Saving\u2026')).toBeTruthy();
  });

  it('disables the button when saving is true', () => {
    render(<SkillProfileScreen {...defaultProps} saving={true} />);
    const button = screen.getByRole('button');
    expect(button.disabled).toBe(true);
  });

  it('calls onSave when button is clicked', () => {
    const onSave = vi.fn();
    render(<SkillProfileScreen {...defaultProps} onSave={onSave} />);
    fireEvent.click(screen.getByText('Save & Return to Dashboard'));
    expect(onSave).toHaveBeenCalledTimes(1);
  });

  it('does not show error message when error is null', () => {
    render(<SkillProfileScreen {...defaultProps} error={null} />);
    expect(screen.queryByText(/could not save/i)).toBeNull();
  });

  it('shows error message when error is provided', () => {
    render(<SkillProfileScreen {...defaultProps} error="Some error" />);
    expect(screen.getByText(/could not save your results/i)).toBeTruthy();
  });

  it('renders empty results list', () => {
    render(<SkillProfileScreen {...defaultProps} results={[]} />);
    expect(screen.getByText('Your Skill Profile')).toBeTruthy();
    expect(screen.queryByText('Easy')).toBeNull();
    expect(screen.queryByText('Medium')).toBeNull();
    expect(screen.queryByText('Hard')).toBeNull();
  });

  it('renders description text', () => {
    render(<SkillProfileScreen {...defaultProps} />);
    expect(screen.getByText(/these levels will set your starting difficulty/i)).toBeTruthy();
  });
});
