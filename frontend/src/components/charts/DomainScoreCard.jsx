import React from 'react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import ProgressBar from '../ui/ProgressBar';

const DomainScoreCard = ({ domain, difficulty, lastScore, totalSessions, averageScore }) => {
  const getDifficultyColor = () => {
    if (difficulty <= 3) return '#3D9E72';
    if (difficulty <= 6) return '#C9973A';
    return '#D95F5F';
  };

  const getDifficultyLabel = () => {
    if (difficulty <= 3) return 'Beginner';
    if (difficulty <= 6) return 'Intermediate';
    return 'Advanced';
  };

  return (
    <Card style={{ marginBottom: 'var(--space-4)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
        <h3 style={{ textTransform: 'capitalize' }}>{domain.replace('_', ' ')}</h3>
        <Badge variant={difficulty <= 3 ? 'default' : 'success'}>
          Level {difficulty}
        </Badge>
      </div>

      <ProgressBar value={difficulty} max={10} label="Difficulty" />

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)', marginTop: 'var(--space-4)' }}>
        <div>
          <p style={{ fontSize: 'var(--text-body-sm)', color: 'var(--color-text-secondary)' }}>Average Score</p>
          <p style={{ fontSize: 'var(--text-h4)', marginTop: 'var(--space-2)' }}>{averageScore.toFixed(1)}%</p>
        </div>
        <div>
          <p style={{ fontSize: 'var(--text-body-sm)', color: 'var(--color-text-secondary)' }}>Sessions</p>
          <p style={{ fontSize: 'var(--text-h4)', marginTop: 'var(--space-2)' }}>{totalSessions}</p>
        </div>
      </div>

      {lastScore !== null && (
        <div style={{ marginTop: 'var(--space-4)', padding: 'var(--space-3)', backgroundColor: 'var(--color-bg-overlay)', borderRadius: 'var(--radius-md)' }}>
          <p style={{ fontSize: 'var(--text-body-sm)' }}>Last Session: {lastScore.toFixed(1)}%</p>
        </div>
      )}
    </Card>
  );
};

export default DomainScoreCard;
