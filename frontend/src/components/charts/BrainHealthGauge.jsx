import React from 'react';
import Card from '../ui/Card';

function resolveCssVar(varName) {
  return getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
}

const BrainHealthGauge = ({ score = 0, domainAverage = 0, lifestyleScore = 0 }) => {
  const getGaugeColor = (s) => {
    if (s >= 80) return resolveCssVar('--color-success');
    if (s >= 60) return resolveCssVar('--color-warning');
    return resolveCssVar('--color-error');
  };

  const getGaugeLabel = (s) => {
    if (s >= 80) return 'Excellent';
    if (s >= 60) return 'Good';
    if (s >= 40) return 'Fair';
    return 'Needs Work';
  };

  return (
    <Card>
      <h3>Brain Health Score</h3>
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        padding: 'var(--space-6)',
        gap: 'var(--space-4)',
      }}>
        <div style={{
          width: '150px',
          height: '150px',
          borderRadius: '50%',
          background: `conic-gradient(${getGaugeColor(score)} 0deg ${(score / 100) * 360}deg, var(--color-bg-overlay) ${(score / 100) * 360}deg)`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 'var(--text-h2)',
          fontWeight: 'var(--weight-bold)',
          color: getGaugeColor(score),
        }}>
          {score}
        </div>

        <p style={{ fontSize: 'var(--text-body-lg)', fontWeight: 'var(--weight-semibold)' }}>
          {getGaugeLabel(score)}
        </p>

        <div style={{
          width: '100%',
          padding: 'var(--space-4)',
          backgroundColor: 'var(--color-bg-overlay)',
          borderRadius: 'var(--radius-md)',
          fontSize: 'var(--text-body-sm)',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
            <span>Cognitive: {domainAverage.toFixed(1)}%</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Lifestyle: {lifestyleScore.toFixed(1)}%</span>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default BrainHealthGauge;
