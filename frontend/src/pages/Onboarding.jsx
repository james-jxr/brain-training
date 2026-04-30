import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import { accountAPI } from '../api/client';

const Onboarding = () => {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const navigate = useNavigate();

  const handleComplete = async () => {
    setSubmitError(null);
    setLoading(true);
    try {
      await accountAPI.markOnboardingComplete();
      navigate('/dashboard');
    } catch (err) {
      console.error('Failed to complete onboarding:', err);
      setSubmitError('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: 'var(--color-bg-base)',
      padding: 'var(--space-4)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}>
      <Card style={{ maxWidth: '600px', width: '100%' }}>
        {step === 1 && (
          <>
            <h1 style={{ marginBottom: 'var(--space-4)', fontWeight: 'var(--weight-medium)' }}>Welcome to Brain Training</h1>
            <p style={{ marginBottom: 'var(--space-4)' }}>
              This app is built on a foundation of academic and scientific research into cognitive training. Studies have shown that targeted brain exercises can improve key mental abilities that matter in everyday life.
            </p>
            <p style={{ marginBottom: 'var(--space-4)' }}>
              Regular brain training has been linked to a range of cognitive benefits, including sharper memory, faster processing speed, and improved attention and focus. These gains can translate into better performance at work, school, and daily tasks.
            </p>
            <p style={{ marginBottom: 'var(--space-6)' }}>
              The key to seeing real results is regular practice. Consistent, short training sessions are more effective than occasional long ones. We recommend training a little every day to maximize your cognitive improvement over time.
            </p>
            <Button
              onClick={() => setStep(2)}
              variant="primary"
              style={{ width: '100%' }}
            >
              Next
            </Button>
          </>
        )}

        {step === 2 && (
          <>
            <h1 style={{ marginBottom: 'var(--space-4)', fontWeight: 'var(--weight-medium)' }}>How It Works</h1>
            <p style={{ marginBottom: 'var(--space-4)' }}>
              Each training session includes exercises from two different cognitive domains. The difficulty automatically adjusts based on your performance to keep you in the optimal learning zone.
            </p>
            <p style={{ marginBottom: 'var(--space-6)' }}>
              Your Brain Health Score combines your cognitive performance with lifestyle factors like sleep, exercise, stress, and mood.
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
              <Button
                onClick={() => setStep(1)}
                variant="secondary"
              >
                Back
              </Button>
              <Button
                onClick={() => setStep(3)}
                variant="primary"
              >
                Next
              </Button>
            </div>
          </>
        )}

        {step === 3 && (
          <>
            <h1 style={{ marginBottom: 'var(--space-4)', fontWeight: 'var(--weight-medium)' }}>Ready to Begin?</h1>
            <p style={{ marginBottom: 'var(--space-6)' }}>
              Start with a baseline assessment to establish your current cognitive level. This helps us customize your training plan. You can retake the baseline every 6 months to measure your overall improvement.
            </p>
            {submitError && (
              <p style={{
                marginBottom: 'var(--space-4)',
                color: 'var(--color-danger)',
                fontSize: 'var(--text-sm)',
              }}>
                {submitError}
              </p>
            )}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
              <Button
                onClick={() => setStep(2)}
                variant="secondary"
              >
                Back
              </Button>
              <Button
                onClick={handleComplete}
                variant="primary"
                disabled={loading}
              >
                {loading ? 'Starting...' : 'Start Training'}
              </Button>
            </div>
          </>
        )}
      </Card>
    </div>
  );
};

export default Onboarding;
