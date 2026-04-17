import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './hooks/useAuth'
import FeedbackWidget from './components/ui/FeedbackWidget'
import BottomNav from './components/nav/BottomNav'
import Landing from './pages/Landing'
import Register from './pages/Register'
import Login from './pages/Login'
import Onboarding from './pages/Onboarding'
import Dashboard from './pages/Dashboard'
import Session from './pages/Session'
import SessionSummary from './pages/SessionSummary'
import Progress from './pages/Progress'
import LifestyleLog from './pages/LifestyleLog'
import AboutScience from './pages/AboutScience'
import Settings from './pages/Settings'
import BaselineTest from './components/baseline/BaselineTest'
import FreePlay from './pages/FreePlay'

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth()

  if (loading) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading...</div>
  }

  return user ? children : <Navigate to="/login" />
}

const AppRoutes = () => {
  const { user, loading } = useAuth()

  if (loading) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading...</div>
  }

  return (
    <>
      <Routes>
        <Route path="/" element={user ? <Navigate to="/dashboard" /> : <Landing />} />
        <Route path="/register" element={user ? <Navigate to="/dashboard" /> : <Register />} />
        <Route path="/login" element={user ? <Navigate to="/dashboard" /> : <Login />} />
        <Route
          path="/onboarding"
          element={
            <ProtectedRoute>
              <Onboarding />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/session/:sessionId"
          element={
            <ProtectedRoute>
              <Session />
            </ProtectedRoute>
          }
        />
        <Route
          path="/session/:sessionId/summary"
          element={
            <ProtectedRoute>
              <SessionSummary />
            </ProtectedRoute>
          }
        />
        <Route
          path="/progress"
          element={
            <ProtectedRoute>
              <Progress />
            </ProtectedRoute>
          }
        />
        <Route
          path="/lifestyle"
          element={
            <ProtectedRoute>
              <LifestyleLog />
            </ProtectedRoute>
          }
        />
        <Route
          path="/science"
          element={
            <ProtectedRoute>
              <AboutScience />
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <Settings />
            </ProtectedRoute>
          }
        />
        <Route
          path="/baseline"
          element={
            <ProtectedRoute>
              <BaselineTest />
            </ProtectedRoute>
          }
        />
        <Route
          path="/play/:gameKey"
          element={
            <ProtectedRoute>
              <FreePlay />
            </ProtectedRoute>
          }
        />
      </Routes>
      <FeedbackWidget />
      <BottomNav />
    </>
  )
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  )
}

export default App
