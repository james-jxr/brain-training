import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, BarChart3, Zap, Settings, LogOut } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import '../../styles/components.css';

const Sidebar = () => {
  const location = useLocation();
  const { logout } = useAuth();

  const handleLogout = async () => {
    try {
      await logout();
      window.location.href = '/login';
    } catch (err) {
      console.error('Logout failed:', err);
    }
  };

  const isActive = (path) => location.pathname === path;

  return (
    <aside className="dashboard-sidebar" style={{
      width: '250px',
      backgroundColor: 'var(--color-bg-raised)',
      borderRight: 'var(--border-default)',
      padding: 'var(--space-4)',
      display: 'flex',
      flexDirection: 'column',
      gap: 'var(--space-2)',
      minHeight: '100vh',
    }}>
      <h1 style={{ fontSize: 'var(--text-h3)', marginBottom: 'var(--space-6)' }}>Brain Training</h1>

      <nav style={{ flex: 1 }}>
        <Link to="/dashboard" className={`nav-item ${isActive('/dashboard') ? 'active' : ''}`}>
          <Home size={20} />
          <span>Dashboard</span>
        </Link>
        <Link to="/progress" className={`nav-item ${isActive('/progress') ? 'active' : ''}`}>
          <BarChart3 size={20} />
          <span>Progress</span>
        </Link>
        <Link to="/lifestyle" className={`nav-item ${isActive('/lifestyle') ? 'active' : ''}`}>
          <Zap size={20} />
          <span>Lifestyle</span>
        </Link>
        <Link to="/settings" className={`nav-item ${isActive('/settings') ? 'active' : ''}`}>
          <Settings size={20} />
          <span>Settings</span>
        </Link>
      </nav>

      <button
        onClick={handleLogout}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-3)',
          padding: 'var(--space-3) var(--space-4)',
          backgroundColor: 'transparent',
          color: 'var(--color-error)',
          border: 'none',
          borderRadius: 'var(--radius-md)',
          cursor: 'pointer',
          fontSize: 'var(--text-body)',
          transition: 'var(--transition-default)',
        }}
        onMouseEnter={(e) => e.target.style.backgroundColor = 'var(--color-error-muted)'}
        onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
      >
        <LogOut size={20} />
        <span>Logout</span>
      </button>
    </aside>
  );
};

export default Sidebar;
