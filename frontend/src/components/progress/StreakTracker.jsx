import React, { useState, useEffect } from 'react';
import Card from '../ui/Card';

const DAY_LABELS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

function formatDateLabel(dateStr) {
  const d = new Date(dateStr + 'T00:00:00');
  return DAY_LABELS[d.getDay()];
}

function formatMonthDay(dateStr) {
  const d = new Date(dateStr + 'T00:00:00');
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

const StreakTracker = ({ streakData }) => {
  const currentStreak = streakData ? streakData.current_streak : 0;
  const longestStreak = streakData ? streakData.longest_streak : 0;
  const days = streakData && streakData.days ? streakData.days : [];

  return (
    <Card style={{ marginBottom: 'var(--space-6)' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 'var(--space-4)' }}>
        <h2 style={{ margin: 0 }}>Consistency</h2>
        <div style={{ display: 'flex', gap: 'var(--space-4)', alignItems: 'baseline' }}>
          <span style={{
            fontSize: '2rem',
            fontWeight: 700,
            color: 'var(--color-accent)',
            lineHeight: 1,
          }}>
            {currentStreak}
          </span>
          <span style={{
            fontSize: '0.875rem',
            color: 'var(--color-text-secondary)',
          }}>
            day streak
          </span>
        </div>
      </div>

      <div style={{
        display: 'flex',
        gap: 'var(--space-2)',
        justifyContent: 'space-between',
        overflowX: 'auto',
        paddingBottom: 'var(--space-2)',
      }}>
        {days.map((day) => {
          const isActive = day.completed;
          const isToday = day.is_today;

          return (
            <div
              key={day.date}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 'var(--space-1)',
                minWidth: '36px',
              }}
            >
              <span style={{
                fontSize: '0.625rem',
                color: 'var(--color-text-secondary)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}>
                {formatDateLabel(day.date)}
              </span>
              <div
                style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '50%',
                  backgroundColor: isActive ? 'var(--color-accent)' : 'transparent',
                  border: isToday && !isActive
                    ? '2px solid var(--color-accent)'
                    : isActive
                      ? '2px solid var(--color-accent)'
                      : '2px solid var(--color-border)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'var(--transition-default)',
                }}
              >
                {isActive && (
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 14 14"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M3 7L6 10L11 4"
                      stroke="var(--color-text-inverse)"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                )}
              </div>
              <span style={{
                fontSize: '0.625rem',
                color: isToday ? 'var(--color-accent)' : 'var(--color-text-secondary)',
                fontWeight: isToday ? 600 : 400,
              }}>
                {formatMonthDay(day.date)}
              </span>
            </div>
          );
        })}
      </div>

      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        marginTop: 'var(--space-4)',
        paddingTop: 'var(--space-4)',
        borderTop: '1px solid var(--color-border)',
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            fontSize: '1.25rem',
            fontWeight: 600,
            color: 'var(--color-text-primary)',
          }}>
            {currentStreak}
          </div>
          <div style={{
            fontSize: '0.75rem',
            color: 'var(--color-text-secondary)',
          }}>
            Current
          </div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            fontSize: '1.25rem',
            fontWeight: 600,
            color: 'var(--color-text-primary)',
          }}>
            {longestStreak}
          </div>
          <div style={{
            fontSize: '0.75rem',
            color: 'var(--color-text-secondary)',
          }}>
            Longest
          </div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            fontSize: '1.25rem',
            fontWeight: 600,
            color: 'var(--color-text-primary)',
          }}>
            {days.filter((d) => d.completed).length}/{days.length}
          </div>
          <div style={{
            fontSize: '0.75rem',
            color: 'var(--color-text-secondary)',
          }}>
            Last 14 days
          </div>
        </div>
      </div>
    </Card>
  );
};

export default StreakTracker;
