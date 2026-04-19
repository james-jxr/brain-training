import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, BarChart3, Zap, Settings } from 'lucide-react';
import '../../styles/components.css';

const BottomNav = () => {
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="bottom-nav">
      <Link
        to="/dashboard"
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 'var(--space-1)',
          padding: 'var(--space-2)',
          color: isActive('/dashboard') ? 'var(--color-accent)' : 'var(--color-text-secondary)',
          textDecoration: 'none',
          fontSize: 'var(--text-caption)',
        }}
      >
        <Home size={20} />
        <span>Home</span>
      </Link>
      <Link
        to="/progress"
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 'var(--space-1)',
          padding: 'var(--space-2)',
          color: isActive('/progress') ? 'var(--color-accent)' : 'var(--color-text-secondary)',
          textDecoration: 'none',
          fontSize: 'var(--text-caption)',
        }}
      >
        <BarChart3 size={20} />
        <span>Progress</span>
      </Link>
      <Link
        to="/lifestyle"
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 'var(--space-1)',
          padding: 'var(--space-2)',
          color: isActive('/lifestyle') ? 'var(--color-accent)' : 'var(--color-text-secondary)',
          textDecoration: 'none',
          fontSize: 'var(--text-caption)',
        }}
      >
        <Zap size={20} />
        <span>Lifestyle</span>
      </Link>
      <Link
        to="/settings"
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 'var(--space-1)',
          padding: 'var(--space-2)',
          color: isActive('/settings') ? 'var(--color-accent)' : 'var(--color-text-secondary)',
          textDecoration: 'none',
          fontSize: 'var(--text-caption)',
        }}
      >
        <Settings size={20} />
        <span>Settings</span>
      </Link>
    </nav>
  );
};

export default BottomNav;
