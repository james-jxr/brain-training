import React from 'react';
import '../../styles/components.css';

const ProgressBar = ({ value = 0, max = 100, label = '', className = '' }) => {
  const percentage = (value / max) * 100;

  return (
    <div className={`progress-bar-container ${className}`} style={{ marginBottom: 'var(--space-2)' }}>
      {label && <div style={{ fontSize: 'var(--text-body-sm)', marginBottom: 'var(--space-2)' }}>{label}</div>}
      <div className="progress-bar">
        <div className="progress-bar-fill" style={{ width: `${percentage}%` }} />
      </div>
      <div style={{ fontSize: 'var(--text-caption)', marginTop: 'var(--space-1)', textAlign: 'right' }}>
        {value}/{max}
      </div>
    </div>
  );
};

export default ProgressBar;
