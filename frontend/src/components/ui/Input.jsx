import React from 'react';
import '../../styles/components.css';

const Input = ({
  label,
  error,
  className = '',
  ...props
}) => {
  return (
    <div className="input-group">
      {label && <label className="input-label">{label}</label>}
      <input className={`input ${className}`} {...props} />
      {error && <span style={{ color: 'var(--color-error)', fontSize: 'var(--text-body-sm)' }}>{error}</span>}
    </div>
  );
};

export default Input;
