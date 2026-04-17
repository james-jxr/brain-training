import React from 'react';
import '../../styles/components.css';

const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  onClick,
  className = '',
  ...props
}) => {
  const baseClass = 'button';
  const variantClass = `button-${variant}`;
  const sizeClass = size !== 'md' ? `button-${size}` : '';

  return (
    <button
      className={`${baseClass} ${variantClass} ${sizeClass} ${className}`}
      disabled={disabled}
      onClick={onClick}
      {...props}
    >
      {children}
    </button>
  );
};

export default Button;
