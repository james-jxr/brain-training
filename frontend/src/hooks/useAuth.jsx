import { useState, useEffect, useContext, createContext } from 'react';
import { authAPI } from '../api/client';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

const storeToken = (token) => {
  if (token) {
    sessionStorage.setItem('access_token', token);
  }
};

const clearToken = () => {
  sessionStorage.removeItem('access_token');
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await authAPI.getCurrentUser();
        setUser(response.data);
      } catch (err) {
        setUser(null);
        clearToken();
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const register = async (email, username, password, consentGiven) => {
    try {
      setError(null);
      const response = await authAPI.register(email, username, password, consentGiven);
      storeToken(response.data.access_token);
      setUser(response.data.user);
      return response.data;
    } catch (err) {
      const message = err.response?.data?.detail?.message || 'Registration failed';
      setError(message);
      throw err;
    }
  };

  const login = async (email, password) => {
    try {
      setError(null);
      const response = await authAPI.login(email, password);
      storeToken(response.data.access_token);
      setUser(response.data.user);
      return response.data;
    } catch (err) {
      const message = err.response?.data?.detail?.message || 'Login failed';
      setError(message);
      throw err;
    }
  };

  const logout = async () => {
    try {
      await authAPI.logout();
      clearToken();
      setUser(null);
    } catch (err) {
      clearToken();
      setUser(null);
      setError('Logout failed');
      throw err;
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, error, register, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};