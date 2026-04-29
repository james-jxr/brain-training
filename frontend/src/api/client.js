import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

client.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    const isAuthCheck = error.config?.url?.includes('/api/auth/me');
    const isPublicPage = ['/', '/login', '/register'].includes(window.location.pathname);
    if (error.response?.status === 401 && !isAuthCheck && !isPublicPage) {
      sessionStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  register: (email, username, password, consentGiven) =>
    client.post('/api/auth/register', { email, username, password, consent_given: consentGiven }),
  login: (email, password) =>
    client.post('/api/auth/login', { email, password }),
  logout: () => client.post('/api/auth/logout'),
  getCurrentUser: () => client.get('/api/auth/me'),
};

export const sessionAPI = {
  startSession: (domain_1, domain_2, is_baseline = 0) =>
    client.post('/api/sessions/start', { domain_1, domain_2, is_baseline }),
  logExerciseResult: (sessionId, data) =>
    client.post(`/api/sessions/${sessionId}/exercise-result`, data),
  completeSession: (sessionId) =>
    client.post(`/api/sessions/${sessionId}/complete`),
  getSession: (sessionId) =>
    client.get(`/api/sessions/${sessionId}`),
  listSessions: () =>
    client.get('/api/sessions'),
  planNextSession: () =>
    client.post('/api/sessions/plan-next'),
};

export const progressAPI = {
  getDomainProgress: (domain) =>
    client.get(`/api/progress/domain/${domain}`),
  getProgressSummary: () =>
    client.get('/api/progress/summary'),
  getBrainHealthScore: () =>
    client.get('/api/progress/brain-health'),
  getStreak: () =>
    client.get('/api/progress/streak'),
  getDomainTrend: (domain) =>
    client.get(`/api/progress/trend/${domain}`),
  getGameHistory: () =>
    client.get('/api/progress/game-history'),
  getStreakHistory: () =>
    client.get('/api/progress/streak/history'),
};

export const lifestyleAPI = {
  logLifestyle: (data) =>
    client.post('/api/lifestyle/log', data),
  getTodayLifestyle: () =>
    client.get('/api/lifestyle/today'),
  getLifestyleHistory: () =>
    client.get('/api/lifestyle/history'),
};

export const accountAPI = {
  getProfile: () =>
    client.get('/api/account/profile'),
  markOnboardingComplete: () =>
    client.post('/api/account/onboarding-complete'),
  getOnboardingStatus: () =>
    client.get('/api/account/onboarding-status'),
};

export const baselineAPI = {
  startBaseline: () =>
    client.post('/api/baseline/start'),
  getNextEligibleDate: () =>
    client.get('/api/baseline/next-eligible-date'),
};

export const adaptiveBaselineAPI = {
  getStatus: () =>
    client.get('/api/adaptive-baseline/status'),
  complete: (results) =>
    client.post('/api/adaptive-baseline/complete', { results }),
};

export const feedbackAPI = {
  submitFeedback: (pageContext, feedbackText, sessionId = null) => {
    const body = { page_context: pageContext, feedback_text: feedbackText };
    if (sessionId) {
      body.session_id = sessionId;
    }
    return client.post('/api/feedback', body);
  },
  exportFeedback: (fromDate = null, toDate = null) => {
    let url = '/api/feedback';
    const params = new URLSearchParams();
    if (fromDate) params.append('from_date', fromDate);
    if (toDate) params.append('to_date', toDate);
    if (params.toString()) {
      url += '?' + params.toString();
    }
    return client.get(url);
  },
};

export default client;
