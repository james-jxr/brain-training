import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Sidebar from '../components/nav/Sidebar';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import PostGameFeedback from '../components/ui/PostGameFeedback';
import { sessionAPI } from '../api/client';
import { calculateScoreFromAccuracy, calculateDigitSpanScore } from '../utils/scoring';
import { Check, X } from 'lucide-react';

const SessionSummary = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [sessionData, setSessionData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showFeedback, setShowFeedback] = useState(true);

  useEffect(() => {
    if (!sessionId) {
      setError('No session ID provided');
      setLoading(false);
      return;
    }

    const loadSession = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await sessionAPI.getSession(sessionId);
        if (!response || !response.data) {
          setError('No data returned from server');
          return;
        }
        const data = response.data;
        if (!data.exercise_attempts || !Array.isArray(data.exercise_attempts)) {
          data.exercise_attempts = [];
        }
        setSessionData(data);
      } catch (err) {
        const message =
          err?.response?.data?.detail ||
          err?.response?.data?.message ||
          err?.message ||
          'Failed to load session';
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    loadSession();
  }, [sessionId]);

  if (loading) {
    return (
      <div style={{ display: 'flex', minHeight: '100vh' }}>
        <Sidebar />
        <main style={{
          flex: 1,
          padding: 'var(--space-6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <div style={{ textAlign: 'center' }}>
            <p style={{ fontSize: 'var(--text-h3)', marginBottom: 'var(--space-4)' }}>
              Loading session summary...
            </p>
          </div>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ display: 'flex', minHeight: '100vh' }}>
        <Sidebar />
        <main style={{
          flex: 1,
          padding: 'var(--space-6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <Card style={{ maxWidth: '500px', textAlign: 'center', padding: 'var(--space-6)' }}>
            <p style={{ color: 'var(--color-error)', marginBottom: 'var(--space-4)' }}>
              Error: {error}
            </p>
            <Button
              onClick={() => navigate('/dashboard')}
              variant="primary"
            >
              Back to Dashboard
            </Button>
          </Card>
        </main>
      </div>
    );
  }

  if (!sessionData) {
    return (
      <div style={{ display: 'flex', minHeight: '100vh' }}>
        <Sidebar />
        <main style={{
          flex: 1,
          padding: 'var(--space-6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <Card style={{ maxWidth: '500px', textAlign: 'center', padding: 'var(--space-6)' }}>
            <p style={{ marginBottom: 'var(--space-4)' }}>No session data available.</p>
            <Button
              onClick={() => navigate('/dashboard')}
              variant="primary"
            >
              Back to Dashboard
            </Button>
          </Card>
        </main>
      </div>
    );
  }

  const exerciseAttempts = sessionData.exercise_attempts || [];
  const totalMoves = exerciseAttempts.reduce((sum, a) => sum + (a.trials_presented || 0), 0);
  const totalAccurateMoves = exerciseAttempts.reduce((sum, a) => sum + (a.trials_correct || 0), 0);
  const overallScore = totalMoves > 0 ? calculateScoreFromAccuracy(totalAccurateMoves, totalMoves) : 0;

  const getAttemptScore = (attempt) => {
    const trialsPresented = attempt.trials_presented || 0;
    const trialsCorrect = attempt.trials_correct || 0;
    if (trialsPresented === 0) return 0;

    if (attempt.exercise_type === 'digit_span' && attempt.max_length_recalled != null) {
      return calculateDigitSpanScore(trialsCorrect, trialsPresented, attempt.max_length_recalled);
    }
    return calculateScoreFromAccuracy(trialsCorrect, trialsPresented);
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      <main style={{
        flex: 1,
        padding: 'var(--space-6)',
        overflowY: 'auto',
      }}>
        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
          <h1 style={{ marginBottom: 'var(--space-8)' }}>Session Summary</h1>

          <Card style={{ marginBottom: 'var(--space-6)' }}>
            <div style={{ textAlign: 'center', marginBottom: 'var(--space-6)' }}>
              <p style={{ fontSize: 'var(--text-body-sm)', color: 'var(--color-text-secondary)' }}>
                Accuracy
              </p>
              <h2 style={{ fontSize: 'var(--text-display)', color: 'var(--color-accent)' }}>
                {overallScore.toFixed(1)}%
              </h2>
              <p style={{
                fontSize: 'var(--text-body-sm)',
                color: 'var(--color-text-tertiary)',
                marginTop: 'var(--space-2)',
              }}>
                {totalAccurateMoves} accurate moves out of {totalMoves} total moves
              </p>
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 'var(--space-4)',
              marginBottom: 'var(--space-6)',
            }}>
              <div>
                <p style={{ fontSize: 'var(--text-body-sm)', color: 'var(--color-text-secondary)' }}>
                  Total Moves
                </p>
                <p style={{ fontSize: 'var(--text-h2)' }}>{totalMoves}</p>
              </div>
              <div>
                <p style={{ fontSize: 'var(--text-body-sm)', color: 'var(--color-text-secondary)' }}>
                  Accurate Moves
                </p>
                <p style={{ fontSize: 'var(--text-h2)', color: 'var(--color-success)' }}>
                  {totalAccurateMoves}
                </p>
              </div>
            </div>

            <Button
              onClick={() => navigate('/dashboard')}
              variant="primary"
              style={{ width: '100%' }}
            >
              Back to Dashboard
            </Button>
          </Card>

          {exerciseAttempts.length > 0 ? (
            <>
              <h2 style={{ marginBottom: 'var(--space-4)' }}>Exercise Results</h2>
              {exerciseAttempts.map((attempt) => {
                const trialsPresented = attempt.trials_presented || 0;
                const trialsCorrect = attempt.trials_correct || 0;
                const score = getAttemptScore(attempt);
                const avgResponseMs = attempt.avg_response_ms || 0;
                const isDigitSpan = attempt.exercise_type === 'digit_span';
                const maxLen = attempt.max_length_recalled || 0;
                return (
                  <Card key={attempt.id} style={{ marginBottom: 'var(--space-4)' }}>
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: 'var(--space-4)',
                    }}>
                      <div>
                        <h3 style={{
                          textTransform: 'capitalize',
                          marginBottom: 'var(--space-2)',
                        }}>
                          {(attempt.exercise_type || 'Unknown').replace('_', ' ')}
                        </h3>
                        <p style={{
                          fontSize: 'var(--text-body-sm)',
                          color: 'var(--color-text-secondary)',
                        }}>
                          {(attempt.domain || 'Unknown').replace('_', ' ')}
                        </p>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <p style={{ fontSize: 'var(--text-h3)', color: 'var(--color-accent)' }}>
                          {score.toFixed(1)}{isDigitSpan ? '' : '%'}
                        </p>
                        <p style={{
                          fontSize: 'var(--text-body-sm)',
                          color: 'var(--color-text-secondary)',
                        }}>
                          {trialsCorrect}/{trialsPresented} accurate
                        </p>
                        {isDigitSpan && (
                          <p style={{
                            fontSize: 'var(--text-body-sm)',
                            color: 'var(--color-text-secondary)',
                          }}>
                            Max length: {maxLen}
                          </p>
                        )}
                      </div>
                    </div>

                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      fontSize: 'var(--text-body-sm)',
                      color: 'var(--color-text-tertiary)',
                    }}>
                      <span>Avg Response: {avgResponseMs.toFixed(0)}ms</span>
                    </div>
                  </Card>
                );
              })}
            </>
          ) : (
            <Card style={{ textAlign: 'center', padding: 'var(--space-6)' }}>
              <p style={{ color: 'var(--color-text-secondary)' }}>
                No exercise results recorded for this session.
              </p>
            </Card>
          )}
        </div>
      </main>

      {showFeedback && (
        <PostGameFeedback
          sessionId={parseInt(sessionId)}
          onDismiss={() => setShowFeedback(false)}
        />
      )}
    </div>
  );
};

export default SessionSummary;
