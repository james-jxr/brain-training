import React from 'react';
import Card from '../ui/Card';
import Button from '../ui/Button';

const RULE_SUMMARIES = {
  nback: 'Remember whether the current item matches the one shown N steps back.',
  go_no_go: 'Respond quickly to "Go" signals, but hold back on "No-Go" signals.',
  card_memory: 'Find all matching pairs of cards by remembering their positions.',
  stroop: 'Identify the ink colour of each word, ignoring what the word says.',
  digit_span: 'Recall the sequence of digits in the correct order.',
  visual_categorisation: 'Group A: Only Blue, Group B: Only Orange — sort items by their visual category.',
  symbol_matching: 'Match symbols to their corresponding pairs as quickly as possible.',
};

const BaselineRuleSummary = ({ gameKey, gameName, onContinue }) => {
  const summary = RULE_SUMMARIES[gameKey] || 'Categorise items based on the rule used in this round.';

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '60vh',
      padding: 'var(--space-6)',
    }}>
      <Card style={{ maxWidth: '480px', width: '100%', textAlign: 'center' }}>
        <div style={{ marginBottom: 'var(--space-3)', fontSize: '2.5rem' }}>📋</div>

        <h2 style={{ marginBottom: 'var(--space-2)', fontSize: 'var(--text-heading-md)' }}>
          Rule Summary
        </h2>

        <p style={{
          marginBottom: 'var(--space-2)',
          color: 'var(--color-text-secondary)',
          fontSize: 'var(--text-body-sm)',
        }}>
          {gameName}
        </p>

        <div style={{
          background: 'var(--color-surface-secondary, #f5f5f5)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-4)',
          marginBottom: 'var(--space-6)',
          textAlign: 'left',
        }}>
          <p style={{
            margin: 0,
            fontWeight: 500,
            fontSize: 'var(--text-body-sm)',
            lineHeight: 1.6,
          }}>
            {summary}
          </p>
        </div>

        <Button onClick={onContinue} variant="primary" style={{ width: '100%' }}>
          Continue
        </Button>
      </Card>
    </div>
  );
};

export default BaselineRuleSummary;
