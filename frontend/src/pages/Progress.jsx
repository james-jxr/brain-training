import React, { useState, useEffect } from 'react';
import Sidebar from '../components/nav/Sidebar';
import Card from '../components/ui/Card';
import TrendChart from '../components/charts/TrendChart';
import DomainScoreCard from '../components/charts/DomainScoreCard';
import StreakTracker from '../components/progress/StreakTracker';
import { useDashboard } from '../hooks/useDashboard';
import { useStreakData } from '../hooks/useStreakData';
import { useGameHistory } from '../hooks/useGameHistory';

const GAME_TYPE_LABELS = {
  NBack: 'N-Back',
  Stroop: 'Stroop',
  GoNoGo: 'Go / No-Go',
  DigitSpan: 'Digit Span',
  CardMemory: 'Card Memory',
  SymbolMatching: 'Symbol Matching',
  VisualCategorisation: 'Visual Categorisation',
};

const Progress = () => {
  const { summary, loading, error } = useDashboard();
  const { streakData, loading: streakLoading, error: streakError } = useStreakData();
  const { gameHistory, loading: gameLoading, error: gameError } = useGameHistory();
  const [selectedDomain, setSelectedDomain] = useState('processing_speed');

  if (loading) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading...</div>;
  }

  if (error) {
    return <div style={{ padding: 'var(--space-4)', color: 'var(--color-error)' }}>Error: {error}</div>;
  }

  const gameTypes = gameHistory ? Object.keys(gameHistory) : [];

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      <main style={{
        flex: 1,
        padding: 'var(--space-6)',
        overflowY: 'auto',
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <h1 style={{ marginBottom: 'var(--space-8)' }}>Progress Tracking</h1>

          {!streakLoading && !streakError && streakData && (
            <StreakTracker streakData={streakData} />
          )}

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 'var(--space-6)', marginBottom: 'var(--space-8)' }}>
            {summary && summary.domains && summary.domains.map((domain) => (
              <DomainScoreCard
                key={domain.domain}
                domain={domain.domain}
                difficulty={domain.current_difficulty}
                lastScore={domain.last_score}
                totalSessions={domain.total_sessions}
                averageScore={domain.average_score}
              />
            ))}
          </div>

          <Card style={{ marginBottom: 'var(--space-6)' }}>
            <h2>Domain Selection</h2>
            <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-4)' }}>
              {['processing_speed', 'working_memory', 'attention'].map((domain) => (
                <button
                  key={domain}
                  onClick={() => setSelectedDomain(domain)}
                  style={{
                    padding: 'var(--space-3) var(--space-4)',
                    backgroundColor: selectedDomain === domain ? 'var(--color-accent)' : 'var(--color-bg-overlay)',
                    color: selectedDomain === domain ? 'var(--color-text-inverse)' : 'var(--color-text-primary)',
                    border: 'none',
                    borderRadius: 'var(--radius-md)',
                    cursor: 'pointer',
                    transition: 'var(--transition-default)',
                    textTransform: 'capitalize',
                  }}
                >
                  {domain.replace('_', ' ')}
                </button>
              ))}
            </div>
          </Card>

          <TrendChart domain={selectedDomain} />

          <div style={{ marginTop: 'var(--space-8)' }}>
            <h2 style={{ marginBottom: 'var(--space-6)' }}>Game Results</h2>
            {gameLoading && (
              <div style={{ padding: 'var(--space-4)' }}>Loading game history...</div>
            )}
            {gameError && (
              <div style={{ padding: 'var(--space-4)', color: 'var(--color-error)' }}>Error loading game history: {gameError}</div>
            )}
            {!gameLoading && !gameError && gameTypes.length === 0 && (
              <Card>
                <p>No game results yet. Complete some exercises to see your progress here.</p>
              </Card>
            )}
            {!gameLoading && !gameError && gameTypes.length > 0 && (
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                gap: 'var(--space-6)',
              }}>
                {gameTypes.map((gameType) => (
                  <TrendChart
                    key={gameType}
                    title={GAME_TYPE_LABELS[gameType] || gameType}
                    data={gameHistory[gameType]}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Progress;
