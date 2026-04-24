import React from 'react';
import { Link } from 'react-router-dom';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import { Zap, TrendingUp, Brain } from 'lucide-react';

const GAMES = [
  { name: 'N-Back', description: 'Working Memory', emoji: '🧠' },
  { name: 'Stroop', description: 'Attention & Inhibition', emoji: '🎨' },
  { name: 'Go/No-Go', description: 'Response Inhibition', emoji: '🚦' },
  { name: 'Digit Span', description: 'Short-Term Memory', emoji: '🔢' },
  { name: 'Card Memory', description: 'Visual Memory', emoji: '🃏' },
  { name: 'Symbol Matching', description: 'Processing Speed', emoji: '⚡' },
  { name: 'Visual Categorisation', description: 'Cognitive Flexibility', emoji: '👁️' },
];

const Landing = () => {
  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: 'var(--color-bg-base)',
      padding: 'var(--space-4)',
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
      }}>
        <header style={{
          textAlign: 'center',
          paddingTop: 'var(--space-16)',
          paddingBottom: 'var(--space-12)',
        }}>
          <h1 style={{ fontSize: 'var(--text-display)', marginBottom: 'var(--space-4)' }}>
            Brain Training
          </h1>
          <p style={{
            fontSize: 'var(--text-body-lg)',
            color: 'var(--color-text-secondary)',
            maxWidth: '600px',
            margin: '0 auto var(--space-8)',
            lineHeight: 'var(--leading-loose)',
          }}>
            Strengthen your cognitive abilities through scientifically-designed exercises. Track your progress and optimize your brain health.
          </p>

          <div style={{ display: 'flex', gap: 'var(--space-4)', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link to="/register">
              <Button variant="primary" size="lg">Get Started</Button>
            </Link>
            <Link to="/login">
              <Button variant="secondary" size="lg">Sign In</Button>
            </Link>
          </div>
        </header>

        <section style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: 'var(--space-6)',
          marginBottom: 'var(--space-16)',
        }}>
          <Card>
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 'var(--space-4)' }}>
              <Zap size={32} color='var(--color-accent)' />
            </div>
            <h3>Adaptive Difficulty</h3>
            <p style={{ fontSize: 'var(--text-body-sm)' }}>
              Exercises automatically adjust to your skill level, targeting the optimal challenge zone for maximum improvement.
            </p>
          </Card>

          <Card>
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 'var(--space-4)' }}>
              <TrendingUp size={32} color='var(--color-accent)' />
            </div>
            <h3>Real Progress</h3>
            <p style={{ fontSize: 'var(--text-body-sm)' }}>
              Track your improvement across processing speed, working memory, and attention with detailed analytics.
            </p>
          </Card>

          <Card>
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 'var(--space-4)' }}>
              <Brain size={32} color='var(--color-accent)' />
            </div>
            <h3>Brain Health Score</h3>
            <p style={{ fontSize: 'var(--text-body-sm)' }}>
              Get a comprehensive brain health assessment combining cognitive performance with lifestyle factors.
            </p>
          </Card>
        </section>

        <section style={{ marginBottom: 'var(--space-16)' }}>
          <h2 style={{
            textAlign: 'center',
            marginBottom: 'var(--space-8)',
            fontSize: 'var(--text-heading-lg)',
          }}>
            Our Exercises
          </h2>
          <div className="landing-games-grid">
            {GAMES.map((game) => (
              <Card key={game.name}>
                <div style={{
                  fontSize: '2.5rem',
                  textAlign: 'center',
                  marginBottom: 'var(--space-3)',
                }}>
                  {game.emoji}
                </div>
                <h3 style={{
                  textAlign: 'center',
                  marginBottom: 'var(--space-2)',
                  fontSize: 'var(--text-body-lg)',
                  fontWeight: 'var(--weight-semibold)',
                }}>
                  {game.name}
                </h3>
                <p style={{
                  textAlign: 'center',
                  fontSize: 'var(--text-body-sm)',
                  color: 'var(--color-text-secondary)',
                  margin: 0,
                }}>
                  {game.description}
                </p>
              </Card>
            ))}
          </div>
        </section>

        <section style={{
          backgroundColor: 'var(--color-bg-raised)',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-8)',
          textAlign: 'center',
        }}>
          <h2 style={{ marginBottom: 'var(--space-4)' }}>Ready to boost your brain?</h2>
          <p style={{
            color: 'var(--color-text-secondary)',
            marginBottom: 'var(--space-6)',
          }}>
            Start your brain training journey today with exercises designed by cognitive scientists.
          </p>
          <Link to="/register">
            <Button variant="primary" size="lg">Create Account</Button>
          </Link>
        </section>
      </div>
    </div>
  );
};

export default Landing;
