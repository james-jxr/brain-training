import React from 'react';
import '../../styles/components.css';

const Badge = ({ children, variant = 'default', className = '', ...props }) => {
  const variantClass = variant !== 'default' ? `badge-${variant}` : '';

  return (
    <span className={`badge ${variantClass} ${className}`} {...props}>
      {children}
    </span>
  );
};

export default Badge;
