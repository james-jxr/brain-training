import React, { useState, useEffect } from 'react';
import Sidebar from '../components/nav/Sidebar';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import { useDashboard } from '../hooks/useDashboard';
import { lifestyleAPI } from '../api/client';

const LifestyleLog = () => {
  const { logLifestyle } = useDashboard();
  const [exerciseMinutes, setExerciseMinutes] = useState('');
  const [sleepHours, setSleepHours] = useState('');
  const [stressLevel, setStressLevel] = useState('5');
  const [mood, setMood] = useState('5');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    const loadTodayData = async () => {
      try {
        const data = await lifestyleAPI.getTodayLifestyle();
        setExerciseMinutes(data.data.exercise_minutes.toString());
        setSleepHours(data.data.sleep_hours.toString());
        setStressLevel(data.data.stress_level.toString());
        setMood(data.data.mood.toString());
      } catch (err) {
        console.error('Failed to load today lifestyle data:', err);
      }
    };

    loadTodayData();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    try {
      await logLifestyle({
        exercise_minutes: parseFloat(exerciseMinutes) || 0,
        sleep_hours: parseFloat(sleepHours) || 0,
        stress_level: parseInt(stressLevel),
        mood: parseInt(mood),
      });
      setMessage('Lifestyle data saved successfully!');
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      const detail = err.response?.data?.detail;
      const errorMessage =
        (detail && detail.message) ||
        (typeof detail === 'string' ? detail : null) ||
        'Failed to save lifestyle data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      <main style={{
        flex: 1,
        padding: 'var(--space-6)',
        overflowY: 'auto',
      }}>
        <div style={{ maxWidth: '600px', margin: '0 auto' }}>
          <h1 style={{ marginBottom: 'var(--space-8)' }}>Lifestyle Logger</h1>

          {message && (
            <Card style={{
              backgroundColor: 'var(--color-success-muted)',
              color: 'var(--color-success)',
              marginBottom: 'var(--space-4)',
            }}>
              {message}
            </Card>
          )}

          {error && (
            <Card style={{
              backgroundColor: 'var(--color-error-muted)',
              color: 'var(--color-error)',
              marginBottom: 'var(--space-4)',
            }}>
              {error}
            </Card>
          )}

          <Card>
            <form onSubmit={handleSubmit}>
              <Input
                label="Exercise (minutes)"
                type="number"
                value={exerciseMinutes}
                onChange={(e) => setExerciseMinutes(e.target.value)}
                placeholder="30"
              />

              <Input
                label="Sleep (hours)"
                type="number"
                step="0.5"
                value={sleepHours}
                onChange={(e) => setSleepHours(e.target.value)}
                placeholder="7"
              />

              <div className="input-group">
                <label className="input-label">Stress Level (1-10)</label>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={stressLevel}
                  onChange={(e) => setStressLevel(e.target.value)}
                  style={{
                    width: '100%',
                    marginBottom: 'var(--space-2)',
                  }}
                />
                <p style={{
                  textAlign: 'center',
                  color: 'var(--color-text-secondary)',
                  fontSize: 'var(--text-body-sm)',
                }}>
                  Current: {stressLevel}
                </p>
              </div>

              <div className="input-group">
                <label className="input-label">Mood (1-10)</label>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={mood}
                  onChange={(e) => setMood(e.target.value)}
                  style={{
                    width: '100%',
                    marginBottom: 'var(--space-2)',
                  }}
                />
                <p style={{
                  textAlign: 'center',
                  color: 'var(--color-text-secondary)',
                  fontSize: 'var(--text-body-sm)',
                }}>
                  Current: {mood}
                </p>
              </div>

              <Button
                type="submit"
                variant="primary"
                style={{ width: '100%' }}
                disabled={loading}
              >
                {loading ? 'Saving...' : 'Save Today\'s Log'}
              </Button>
            </form>
          </Card>

          <Card style={{ marginTop: 'var(--space-6)' }}>
            <h2 style={{ marginBottom: 'var(--space-4)' }}>Tips for Brain Health</h2>
            <ul style={{ fontSize: 'var(--text-body-sm)', lineHeight: 'var(--leading-loose)', paddingLeft: 'var(--space-6)' }}>
              <li>Aim for at least 30 minutes of physical activity daily</li>
              <li>Get 7-9 hours of quality sleep each night</li>
              <li>Maintain a stress level below 5 for optimal cognitive function</li>
              <li>Cultivate positive mood through social connections and enjoyable activities</li>
            </ul>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default LifestyleLog;
