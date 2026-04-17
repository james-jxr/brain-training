import React, { useState } from 'react';
import { feedbackAPI } from '../../api/client';
import Button from './Button';
import '../../styles/components.css';

const PostGameFeedback = ({ sessionId, onDismiss }) => {
  const [feedbackText, setFeedbackText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [error, setError] = useState('');

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

    setIsSubmitting(true);
    try {
      await feedbackAPI.submitFeedback('session_summary', feedbackText, sessionId);
      setShowConfirmation(true);
      setFeedbackText('');

      // Auto-dismiss confirmation and modal after 2 seconds
      setTimeout(() => {
        setShowConfirmation(false);
        onDismiss();
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit feedback. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSkip = () => {
    onDismiss();
  };

  return (
    <div className="post-game-feedback-overlay">
      <div className="post-game-feedback-modal">
        <div className="post-game-feedback-header">
          <h3>How was this session?</h3>
          <button
            onClick={handleSkip}
            className="post-game-feedback-close"
            type="button"
            title="Skip"
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
          <form onSubmit={handleSubmit} className="post-game-feedback-form">
            <p className="post-game-feedback-prompt">
              Your feedback helps us improve. (optional)
            </p>
            <textarea
              value={feedbackText}
              onChange={(e) => setFeedbackText(e.target.value)}
              placeholder="What did you think of this session?"
              rows="4"
              maxLength="1000"
              className="feedback-textarea"
              disabled={isSubmitting}
            />
            <div className="feedback-char-count">
              {feedbackText.length} / 1000
            </div>
            {error && <div className="feedback-error">{error}</div>}
            <div className="post-game-feedback-actions">
              <Button
                variant="secondary"
                onClick={handleSkip}
                disabled={isSubmitting}
                type="button"
                className="post-game-feedback-skip"
              >
                Skip
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
  );
};

export default PostGameFeedback;
