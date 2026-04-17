import React, { useState } from 'react';
import { feedbackAPI } from '../../api/client';
import Button from './Button';
import '../../styles/components.css';

const FeedbackWidget = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [feedbackText, setFeedbackText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [error, setError] = useState('');

  const handleOpen = () => {
    setIsOpen(true);
    setError('');
  };

  const handleClose = () => {
    setIsOpen(false);
    setFeedbackText('');
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!feedbackText.trim()) {
      setError('Please enter some feedback');
      return;
    }

    if (feedbackText.length > 1000) {
      setError('Feedback must be 1000 characters or less');
      return;
    }

    // Derive page_context from current pathname (e.g. "/dashboard" → "dashboard")
    const pageContext = window.location.pathname.replace(/^\//, '').replace(/\/.*$/, '') || 'home';

    setIsSubmitting(true);
    try {
      await feedbackAPI.submitFeedback(pageContext, feedbackText);
      setShowConfirmation(true);
      setFeedbackText('');

      // Auto-dismiss confirmation and close modal after 2 seconds
      setTimeout(() => {
        setShowConfirmation(false);
        handleClose();
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit feedback. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      {/* Floating Button */}
      <button
        onClick={handleOpen}
        className="feedback-widget-button"
        title="Send us your feedback"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
      </button>

      {/* Modal Overlay */}
      {isOpen && (
        <div className="feedback-modal-overlay" onClick={handleClose}>
          <div className="feedback-modal" onClick={(e) => e.stopPropagation()}>
            <div className="feedback-modal-header">
              <h2>Share Your Feedback</h2>
              <button
                onClick={handleClose}
                className="feedback-modal-close"
                type="button"
              >
                ✕
              </button>
            </div>

            {showConfirmation ? (
              <div className="feedback-confirmation">
                <div className="feedback-confirmation-icon">✓</div>
                <p>Thank you for your feedback!</p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="feedback-form">
                <textarea
                  value={feedbackText}
                  onChange={(e) => setFeedbackText(e.target.value)}
                  placeholder="Tell us what you think... (max 1000 characters)"
                  rows="5"
                  maxLength="1000"
                  className="feedback-textarea"
                  disabled={isSubmitting}
                />
                <div className="feedback-char-count">
                  {feedbackText.length} / 1000
                </div>
                {error && <div className="feedback-error">{error}</div>}
                <div className="feedback-form-actions">
                  <Button
                    variant="secondary"
                    onClick={handleClose}
                    disabled={isSubmitting}
                    type="button"
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="primary"
                    onClick={handleSubmit}
                    disabled={isSubmitting || !feedbackText.trim()}
                    type="submit"
                  >
                    {isSubmitting ? 'Submitting...' : 'Submit'}
                  </Button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </>
  );
};

export default FeedbackWidget;
