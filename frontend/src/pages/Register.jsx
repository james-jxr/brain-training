import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Card from '../components/ui/Card';
import { useAuth } from '../hooks/useAuth';

const Register = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [consentGiven, setConsentGiven] = useState(false);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const newErrors = {};

    if (!email) newErrors.email = 'Email required';
    if (!password) newErrors.password = 'Password required';
    if (password !== confirmPassword) newErrors.confirmPassword = 'Passwords do not match';
    if (!consentGiven) newErrors.consent = 'You must accept the terms to register';

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setLoading(true);
    try {
      const derivedUsername = email.split('@')[0].replace(/[^a-zA-Z0-9_]/g, '_').slice(0, 30);
      await register(email, derivedUsername, password, consentGiven);
      navigate('/onboarding');
    } catch (err) {
      setErrors({ submit: err.response?.data?.detail?.message || 'Registration failed' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: 'var(--color-bg-base)',
      padding: 'var(--space-4)',
    }}>
      <Card style={{ maxWidth: '400px', width: '100%' }}>
        <h1 style={{ marginBottom: 'var(--space-6)', textAlign: 'center' }}>Create Account</h1>

        <form onSubmit={handleSubmit}>
          <Input
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={errors.email}
            placeholder="you@example.com"
          />

          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={errors.password}
            placeholder="At least 8 characters"
          />

          <Input
            label="Confirm Password"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            error={errors.confirmPassword}
            placeholder="Confirm your password"
          />

          <div style={{ marginBottom: 'var(--space-4)' }}>
            <label style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 'var(--space-3)',
              cursor: 'pointer',
              fontSize: 'var(--text-body-sm)',
              color: 'var(--color-text-secondary)',
            }}>
              <input
                type="checkbox"
                checked={consentGiven}
                onChange={(e) => setConsentGiven(e.target.checked)}
                style={{ marginTop: '2px', flexShrink: 0 }}
              />
              I agree to the collection and processing of my personal data for the purpose of cognitive training and progress tracking.
            </label>
            {errors.consent && (
              <p style={{ color: 'var(--color-error)', fontSize: 'var(--text-body-sm)', marginTop: 'var(--space-2)' }}>
                {errors.consent}
              </p>
            )}
          </div>

          {errors.submit && (
            <div style={{
              padding: 'var(--space-3)',
              backgroundColor: 'var(--color-error-muted)',
              color: 'var(--color-error)',
              borderRadius: 'var(--radius-md)',
              marginBottom: 'var(--space-4)',
            }}>
              {errors.submit}
            </div>
          )}

          <Button
            type="submit"
            variant="primary"
            style={{ width: '100%', marginBottom: 'var(--space-4)' }}
            disabled={loading}
          >
            {loading ? 'Creating account...' : 'Create Account'}
          </Button>
        </form>

        <p style={{ textAlign: 'center', fontSize: 'var(--text-body-sm)' }}>
          Already have an account?{' '}
          <Link to="/login" style={{ color: 'var(--color-accent)' }}>
            Sign in
          </Link>
        </p>
      </Card>
    </div>
  );
};

export default Register;
