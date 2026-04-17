import React from 'react';
import { useAuth } from '../../hooks/useAuth';
import '../../styles/components.css';

const TopNav = () => {
  const { user } = useAuth();

  return (
    <nav className="nav" style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
    }}>
      <h1 style={{ fontSize: 'var(--text-h3)' }}>Brain Training</h1>
      {user && (
        <div style={{ color: 'var(--color-text-secondary)' }}>
          Welcome, {user.username}
        </div>
      )}
    </nav>
  );
};

export default TopNav;
