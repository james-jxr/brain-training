import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/components.css';
import Sidebar from '../components/nav/Sidebar';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import BrainHealthGauge from '../components/charts/BrainHealthGauge';
import DomainScoreCard from '../components/charts/DomainScoreCard';
import BaselinePrompt from '../components/baseline/BaselinePrompt';
import { useDashboard } from '../hooks/useDashboard';
import { useSession } from '../hooks/useSession';
import { adaptiveBaselineAPI } from '../api/client';
import { Flame } from 'lucide-react';

const isTextInputFocused = () => {
  const el = document.activeElement;
  if (!el) return false;
  const tag = el.tagName.toLowerCase();
  if (tag === 'textarea') return true;
  if (tag === 'input') {
    const type = (el.getAttribute('type') || 'text').toLowerCase();
    const textTypes = ['text', 'search', 'url', 'tel', 'password', 'email', 'number'];
    return textTypes.includes(type);
  }
  if (el.isContentEditable) return true;
  return false;
};

const DecorativeSVG = () => (
  <svg
    className="dashboard-hero-decoration"
    width="320"
    height="320"
    viewBox="0 0 320 320"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
  >
    <circle cx="160" cy="160" r="120" stroke="currentColor" strokeWidth="0.5" />
    <circle cx="160" cy="160" r="80" stroke="currentColor" strokeWidth="0.5" />
    <circle cx="160" cy="160" r="40" stroke="currentColor" strokeWidth="0.5" />
    <circle cx="160" cy="80" r="6" fill="currentColor" />
    <circle cx="220" cy="120" r="4" fill="currentColor" />
    <circle cx="240" cy="180" r="5" fill="currentColor" />
    <circle cx="200" cy="240" r="4" fill="currentColor" />
    <circle cx="120" cy="240" r="5" fill="currentColor" />
    <circle cx="80" cy="180" r="4" fill="currentColor" />
    <circle cx="100" cy="120" r="6" fill="currentColor" />
    <circle cx="160" cy="160" r="5" fill="currentColor" />
    <line x1="160" y1="80" x2="220" y2="120" stroke="currentColor" strokeWidth="0.5" />
    <line x1="220" y1="120" x2="240" y2="180" stroke="currentColor" strokeWidth="0.5" />
    <line x1="240" y1="180" x2="200" y2="240" stroke="currentColor" strokeWidth="0.5" />
    <line x1="200" y1="240" x2="120" y2="240" stroke="currentColor" strokeWidth="0.5" />
    <line x1="120" y1="240" x2="80" y2="180" stroke="currentColor" strokeWidth="0.5" />
    <line x1="80" y1="180" x2="100" y2="120" stroke="currentColor" strokeWidth="0.5" />
    <line x1="100" y1="120" x2="160" y2="80" stroke="currentColor" strokeWidth="0.5" />
    <line x1="160" y1="80" x2="160" y2="160" stroke="currentColor" strokeWidth="0.5" />
    <line x1="220" y1="120" x2="160" y2="160" stroke="currentColor" strokeWidth="0.5" />
    <line x1="240" y1="180" x2="160" y2="160" stroke="currentColor" strokeWidth="0.5" />
    <line x1="200" y1="240" x2="160" y2="160" stroke="currentColor" strokeWidth="0.5" />
    <line x1="120" y1="240" x2="160" y2="160" stroke="currentColor" strokeWidth="0.5" />
    <line x1="80" y1="180" x2="160" y2="160" stroke="currentColor" strokeWidth="0.5" />
    <line x1="100" y1="120" x2="160" y2="160" stroke="currentColor" strokeWidth="0.5" />
    <circle cx="260" cy="60" r="3" fill="currentColor" />
    <circle cx="280" cy="100" r="2" fill="currentColor" />
    <circle cx="60" cy="260" r="3" fill="currentColor" />
    <circle cx="40" cy="220" r="2" fill="currentColor" />
    <circle cx="290" cy="250" r="2" fill="currentColor" />
    <circle cx="50" cy="80" r="2" fill="currentColor" />
  </svg>
);

const Dashboard = () => {
  const navigate = useNavigate();
  const { summary, brainHealth, streak, loading, error } = useDashboard();
  const { startSession } = useSession();
  const [sessionLoading, setSessionLoading] = useState(false);

  // Baseline prompt state
  const [hasCompletedBaseline, setHasCompletedBaseline] = useState(true); // default true to avoid flash
  const [baselinePromptDismissed, setBaselinePromptDismissed] = useState(false);
  const [baselineStatusLoaded, setBaselineStatusLoaded] = useState(false);

  useEffect(() => {
    const checkBaseline = async () => {
      try {
        const res = await adaptiveBaselineAPI.getStatus();
        setHasCompletedBaseline(res.data.has_completed);
      } catch (err) {
        // If the check fails, don't show the prompt — avoid blocking the dashboard
        setHasCompletedBaseline(true);
      } finally {
        setBaselineStatusLoaded(true);
      }
    };
    checkBaseline();
  }, []);

  // Global keydown guard: allow default behaviour when a text input is focused
  useEffect(() => {
    const handler = (e) => {
      if (e.code === 'Space' && isTextInputFocused()) {
        e.stopPropagation();
      }
    };
    window.addEventListener('keydown', handler, true);
    return () => window.removeEventListener('keydown', handler, true);
  }, []);

  const handleStartSession = async () => {
    setSessionLoading(true);
    try {
      const response = await startSession('processing_speed', 'working_memory');
      navigate(`/session/${response.id}`);
    } catch (err) {
      console.error('Failed to start session:', err);
    } finally {
      setSessionLoading(false);
    }
  };

  if (loading) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading...</div>;
  }

  if (error) {
    return <div style={{ padding: 'var(--space-4)', color: 'var(--color-error)' }}>Error: {error}</div>;
  }

  const showBaselinePrompt =
    baselineStatusLoaded && !hasCompletedBaseline && !baselinePromptDismissed;

  return (
    <div className="dashboard-layout">
      <Sidebar />
      <main className="dashboard-main dashboard-main--decorated">
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div className="dashboard-hero-area">
            <DecorativeSVG />
            <div className="dashboard-header">
              <h1>Dashboard</h1>
              {streak && (
                <div className="streak-badge">
                  <Flame size={20} />
                  <span>{streak.current_streak} day streak</span>
                </div>
              )}
            </div>

            {/* Baseline prompt — shown on first login until dismissed or completed */}
            {showBaselinePrompt && (
              <BaselinePrompt onDismiss={() => setBaselinePromptDismissed(true)} />
            )}

            <div className="dashboard-grid-cards">
              <Card style={{ gridColumn: 'span 1' }} className="card--primary">
                <h2 style={{ marginBottom: 'var(--space-4)' }}>Ready to Train?</h2>
                <p style={{ marginBottom: 'var(--space-4)', color: 'var(--color-text-secondary)' }}>
                  Start a new session to exercise your cognitive abilities.
                </p>
                <Button
                  onClick={handleStartSession}
                  variant="primary"
                  disabled={sessionLoading}
                  style={{ width: '100%' }}
                >
                  {sessionLoading ? 'Starting...' : 'Start Session'}
                </Button>
              </Card>

              {brainHealth && (
                <BrainHealthGauge
                  score={brainHealth.brain_health_score}
                  domainAverage={brainHealth.domain_average}
                  lifestyleScore={brainHealth.lifestyle_score}
                />
              )}
            </div>
          </div>

          {/* Practice Games */}
          <div style={{ marginBottom: 'var(--space-8)' }}>
            <h2 style={{ marginBottom: 'var(--space-4)' }}>Practice</h2>
            <div className="dashboard-practice-grid">
              {[
                { key: 'visual_categorisation', label: 'Visual Categorisation' },
                { key: 'n_back',                label: 'Count Back' },
                { key: 'digit_span',            label: 'Digit Span' },
                { key: 'go_no_go',              label: 'Go / No-Go' },
                { key: 'stroop',                label: 'Stroop' },
                { key: 'card_memory',           label: 'Card Memory' },
              ].map(({ key, label }) => (
                <button
                  key={key}
                  onClick={() => navigate(`/play/${key}`)}
                  style={{
                    background: 'var(--color-bg-card)',
                    border: '1px solid var(--color-border-default)',
                    borderRadius: 'var(--radius-md)',
                    padding: 'var(--space-3) var(--space-4)',
                    fontSize: 'var(--text-body-sm)',
                    color: 'var(--color-text-primary)',
                    cursor: 'pointer',
                    textAlign: 'center',
                    transition: 'border-color 0.15s',
                  }}
                  onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--color-accent)'}
                  onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--color-border-default)'}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {summary && summary.domains && (
            <div className="dashboard-grid-domains">
              {summary.domains.map((domain) => (
                <DomainScoreCard
                  key={domain.domain}
                  domain={domain.domain}
                  difficulty={domain.current_difficulty}
                  lastScore={domain.last_score}
                  totalSessions={domain.total_sessions}
                  averageScore={domain.average_score}
                />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
