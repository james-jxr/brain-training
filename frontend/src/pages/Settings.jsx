import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../components/nav/Sidebar';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import { useAuth } from '../hooks/useAuth';
import { accountAPI } from '../api/client';

const Settings = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [profile, setProfile] = useState(null);
  const [onboardingStatus, setOnboardingStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadSettings = async () => {
      try {
        const [profileRes, statusRes] = await Promise.all([
          accountAPI.getProfile(),
          accountAPI.getOnboardingStatus(),
        ]);
        setProfile(profileRes.data);
        setOnboardingStatus(statusRes.data);
      } catch (err) {
        console.error('Failed to load settings:', err);
      } finally {
        setLoading(false);
      }
    };

    loadSettings();
  }, []);

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (err) {
      console.error('Logout failed:', err);
    }
  };

  if (loading) {
    return <div>Loading settings...</div>;
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      <main style={{
        flex: 1,
        padding: 'var(--space-6)',
        overflowY: 'auto',
      }}>
        <div style={{ maxWidth: '600px', margin: '0 auto' }}>
          <h1 style={{ marginBottom: 'var(--space-8)' }}>Settings</h1>

          <Card style={{ marginBottom: 'var(--space-6)' }}>
            <h2 style={{ marginBottom: 'var(--space-4)' }}>Account</h2>
            {profile && (
              <div style={{ marginBottom: 'var(--space-6)' }}>
                <div style={{ marginBottom: 'var(--space-4)' }}>
                  <p style={{ fontSize: 'var(--text-body-sm)', color: 'var(--color-text-secondary)' }}>
                    Email
                  </p>
                  <p style={{ fontSize: 'var(--text-body)' }}>{profile.email}</p>
                </div>
                <div style={{ marginBottom: 'var(--space-4)' }}>
                  <p style={{ fontSize: 'var(--text-body-sm)', color: 'var(--color-text-secondary)' }}>
                    Username
                  </p>
                  <p style={{ fontSize: 'var(--text-body)' }}>{profile.username}</p>
                </div>
                {onboardingStatus && (
                  <div>
                    <p style={{ fontSize: 'var(--text-body-sm)', color: 'var(--color-text-secondary)' }}>
                      Status
                    </p>
                    <p style={{ fontSize: 'var(--text-body)' }}>
                      {onboardingStatus.onboarding_completed ? 'Onboarding Complete' : 'Onboarding Pending'}
                    </p>
                  </div>
                )}
              </div>
            )}
          </Card>

          <Card style={{ marginBottom: 'var(--space-6)' }}>
            <h2 style={{ marginBottom: 'var(--space-4)' }}>Preferences</h2>
            <p style={{
              color: 'var(--color-text-secondary)',
              marginBottom: 'var(--space-4)',
              fontSize: 'var(--text-body-sm)',
            }}>
              Theme and notification preferences coming soon.
            </p>
          </Card>

          <Card style={{ marginBottom: 'var(--space-6)' }}>
            <h2 style={{ marginBottom: 'var(--space-4)' }}>Privacy & Security</h2>
            <p style={{
              color: 'var(--color-text-secondary)',
              marginBottom: 'var(--space-4)',
              fontSize: 'var(--text-body-sm)',
            }}>
              Your data is encrypted and secure. We never share your information with third parties.
            </p>
            <a href="#privacy" style={{ color: 'var(--color-accent)', fontSize: 'var(--text-body-sm)' }}>
              View Privacy Policy
            </a>
          </Card>

          <Card>
            <h2 style={{ marginBottom: 'var(--space-4)' }}>Log Out</h2>
            <p style={{
              color: 'var(--color-text-secondary)',
              marginBottom: 'var(--space-6)',
              fontSize: 'var(--text-body-sm)',
            }}>
              Log out of your account. You'll need to sign in again to access Brain Training.
            </p>
            <Button
              onClick={handleLogout}
              variant="secondary"
              style={{
                width: '100%',
                color: 'var(--color-error)',
                borderColor: 'var(--color-error)',
              }}
            >
              Logout
            </Button>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default Settings;
