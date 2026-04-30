import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, BarChart3, Zap, Settings } from 'lucide-react';
import '../../styles/components.css';

const navLinkStyle = (active) => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  gap: 'var(--space-1)',
  padding: 'var(--space-2)',
  color: active ? 'var(--color-accent)' : 'var(--color-text-secondary)',
  textDecoration: 'none',
  fontSize: 'var(--text-caption)',
});

const BottomNav = () => {
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="bottom-nav">
      <Link to="/dashboard" style={navLinkStyle(isActive('/dashboard'))}>
        <Home size={20} />
        <span>Home</span>
      </Link>
      <Link to="/progress" style={navLinkStyle(isActive('/progress'))}>
        <BarChart3 size={20} />
        <span>Progress</span>
      </Link>
      <Link to="/lifestyle" style={navLinkStyle(isActive('/lifestyle'))}>
        <Zap size={20} />
        <span>Lifestyle</span>
      </Link>
      <Link to="/settings" style={navLinkStyle(isActive('/settings'))}>
        <Settings size={20} />
        <span>Settings</span>
      </Link>
    </nav>
  );
};

export default BottomNav;
