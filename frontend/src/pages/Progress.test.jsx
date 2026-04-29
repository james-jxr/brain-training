import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import Progress from './Progress';

// Mock hooks
const mockUseDashboard = vi.fn();
const mockUseStreakData = vi.fn();
const mockUseGameHistory = vi.fn();

vi.mock('../hooks/useDashboard', () => ({
  useDashboard: () => mockUseDashboard(),
}));

vi.mock('../hooks/useStreakData', () => ({
  useStreakData: () => mockUseStreakData(),
}));

vi.mock('../hooks/useGameHistory', () => ({
  useGameHistory: () => mockUseGameHistory(),
}));

// Mock child components
vi.mock('../components/nav/Sidebar', () => ({
  default: () => <nav data-testid="sidebar" />,
}));

vi.mock('../components/ui/Card', () => ({
  default: ({ children, style }) => <div data-testid="card" style={style}>{children}</div>,
}));

vi.mock('../components/charts/TrendChart', () => ({
  default: ({ domain, title, data }) => (
    <div data-testid="trend-chart" data-domain={domain} data-title={title}>
      TrendChart: {title || domain}
    </div>
  ),
}));

vi.mock('../components/charts/DomainScoreCard', () => ({
  default: ({ domain }) => <div data-testid="domain-score-card">{domain}</div>,
}));

vi.mock('../components/progress/StreakTracker', () => ({
  default: ({ streakData }) => <div data-testid="streak-tracker">StreakTracker</div>,
}));

describe('Progress page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseDashboard.mockReturnValue({
      summary: null,
      loading: false,
      error: null,
    });
    mockUseStreakData.mockReturnValue({
      streakData: null,
      loading: false,
      error: null,
    });
    mockUseGameHistory.mockReturnValue({
      gameHistory: null,
      loading: false,
      error: null,
    });
  });

  it('shows loading state when dashboard is loading', () => {
    mockUseDashboard.mockReturnValue({ summary: null, loading: true, error: null });
    render(<Progress />);
    expect(screen.getByText('Loading...')).toBeDefined();
  });

  it('shows error state when dashboard has error', () => {
    mockUseDashboard.mockReturnValue({ summary: null, loading: false, error: 'Something went wrong' });
    render(<Progress />);
    expect(screen.getByText('Error: Something went wrong')).toBeDefined();
  });

  it('renders main heading when loaded successfully', () => {
    render(<Progress />);
    expect(screen.getByText('Progress Tracking')).toBeDefined();
  });

  it('renders sidebar', () => {
    render(<Progress />);
    expect(screen.getByTestId('sidebar')).toBeDefined();
  });

  it('renders domain selection buttons', () => {
    render(<Progress />);
    expect(screen.getByText('processing speed')).toBeDefined();
    expect(screen.getByText('working memory')).toBeDefined();
    expect(screen.getByText('attention')).toBeDefined();
  });

  it('renders TrendChart for selected domain', () => {
    render(<Progress />);
    const charts = screen.getAllByTestId('trend-chart');
    const domainChart = charts.find(c => c.getAttribute('data-domain') === 'processing_speed');
    expect(domainChart).toBeDefined();
  });

  it('changes selected domain when button clicked', () => {
    render(<Progress />);
    fireEvent.click(screen.getByText('working memory'));
    const charts = screen.getAllByTestId('trend-chart');
    const domainChart = charts.find(c => c.getAttribute('data-domain') === 'working_memory');
    expect(domainChart).toBeDefined();
  });

  it('renders DomainScoreCards when summary has domains', () => {
    mockUseDashboard.mockReturnValue({
      summary: {
        domains: [
          { domain: 'processing_speed', current_difficulty: 1, last_score: 80, total_sessions: 5, average_score: 75 },
          { domain: 'working_memory', current_difficulty: 2, last_score: 70, total_sessions: 3, average_score: 65 },
        ],
      },
      loading: false,
      error: null,
    });
    render(<Progress />);
    const cards = screen.getAllByTestId('domain-score-card');
    expect(cards.length).toBe(2);
  });

  it('renders StreakTracker when streak data is available', () => {
    mockUseStreakData.mockReturnValue({
      streakData: { current_streak: 5, longest_streak: 10 },
      loading: false,
      error: null,
    });
    render(<Progress />);
    expect(screen.getByTestId('streak-tracker')).toBeDefined();
  });

  it('does not render StreakTracker when streak is loading', () => {
    mockUseStreakData.mockReturnValue({
      streakData: { current_streak: 5 },
      loading: true,
      error: null,
    });
    render(<Progress />);
    expect(screen.queryByTestId('streak-tracker')).toBeNull();
  });

  it('does not render StreakTracker when streak has error', () => {
    mockUseStreakData.mockReturnValue({
      streakData: null,
      loading: false,
      error: 'streak error',
    });
    render(<Progress />);
    expect(screen.queryByTestId('streak-tracker')).toBeNull();
  });

  it('shows no game results message when game history is empty', () => {
    mockUseGameHistory.mockReturnValue({
      gameHistory: {},
      loading: false,
      error: null,
    });
    render(<Progress />);
    expect(screen.getByText('No game results yet. Complete some exercises to see your progress here.')).toBeDefined();
  });

  it('renders TrendCharts for each game type in history', () => {
    mockUseGameHistory.mockReturnValue({
      gameHistory: {
        'Game A': [{ date: '2024-01-01', score: 80 }],
        'Game B': [{ date: '2024-01-02', score: 70 }],
      },
      loading: false,
      error: null,
    });
    render(<Progress />);
    const charts = screen.getAllByTestId('trend-chart');
    const gameTitles = charts.map(c => c.getAttribute('data-title')).filter(Boolean);
    expect(gameTitles).toContain('Game A');
    expect(gameTitles).toContain('Game B');
  });

  it('shows game loading state', () => {
    mockUseGameHistory.mockReturnValue({
      gameHistory: null,
      loading: true,
      error: null,
    });
    render(<Progress />);
    expect(screen.getByText('Loading game history...')).toBeDefined();
  });

  it('shows game error state', () => {
    mockUseGameHistory.mockReturnValue({
      gameHistory: null,
      loading: false,
      error: 'Failed to fetch',
    });
    render(<Progress />);
    expect(screen.getByText('Error loading game history: Failed to fetch')).toBeDefined();
  });
});
