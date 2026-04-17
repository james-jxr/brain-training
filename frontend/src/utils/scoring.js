export const calculateScore = (correctSelects, correctLeaves, totalMoves) => {
  if (totalMoves === 0) return 0;
  return ((correctSelects + correctLeaves) / totalMoves) * 100;
};

export const calculateScoreFromAccuracy = (accurateMoves, totalMoves) => {
  if (totalMoves === 0) return 0;
  return (accurateMoves / totalMoves) * 100;
};

export const calculateDigitSpanScore = (trialsCorrect, trialsPresented, maxLengthRecalled) => {
  if (trialsPresented === 0) return 0;
  const accuracyPct = (trialsCorrect / trialsPresented) * 100;
  const composite = (accuracyPct * 0.5) + (maxLengthRecalled * 5);
  return Math.min(100, composite);
};

export const formatScore = (score) => {
  return Math.round(score * 10) / 10;
};

export const getScoreFeedback = (score) => {
  if (score >= 80) return { status: 'excellent', message: 'Excellent!' };
  if (score >= 70) return { status: 'good', message: 'Good job!' };
  if (score >= 50) return { status: 'fair', message: 'Keep practicing!' };
  return { status: 'poor', message: 'Try again!' };
};

export const getAverageScore = (scores) => {
  if (scores.length === 0) return 0;
  const sum = scores.reduce((a, b) => a + b, 0);
  return sum / scores.length;
};

export const getDifficultyColor = (difficulty) => {
  if (difficulty <= 3) return 'var(--color-success)';
  if (difficulty <= 6) return 'var(--color-warning)';
  return 'var(--color-error)';
};

export const calculateBrainHealthScore = (domainScores, lifestyleScore) => {
  return Math.round(domainScores * 0.6 + lifestyleScore * 0.4);
};
