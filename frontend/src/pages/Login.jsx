import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Card from '../components/ui/Card';
import { useAuth } from '../hooks/useAuth';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const newErrors = {};

    if (!email) newErrors.email = 'Email required';
    if (!password) newErrors.password = 'Password required';

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setLoading(true);
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      setErrors({ submit: err.response?.data?.detail?.message || 'Login failed' });
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
        <h1 style={{ marginBottom: 'var(--space-6)', textAlign: 'center' }}>Sign In</h1>

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
            placeholder="Your password"
          />

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
            {loading ? 'Signing in...' : 'Sign In'}
          </Button>
        </form>

        <p style={{ textAlign: 'center', fontSize: 'var(--text-body-sm)' }}>
          Don't have an account?{' '}
          <Link to="/register" style={{ color: 'var(--color-accent)' }}>
            Create one
          </Link>
        </p>
      </Card>
    </div>
  );
};

export default Login;
