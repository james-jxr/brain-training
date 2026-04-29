import React, { useEffect, useState } from 'react';
import Card from '../ui/Card';
import { useDashboard } from '../../hooks/useDashboard';

const TrendChart = ({ domain, title, data: externalData }) => {
  const { getDomainTrend, loading: dashLoading, error: dashError } = useDashboard();
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (externalData) {
      setData(externalData);
      return;
    }

    if (!domain) {
      return;
    }

    const loadTrend = async () => {
      setLoading(true);
      setError(null);
      try {
        const trend = await getDomainTrend(domain);
        setData(trend.data);
      } catch (err) {
        setError('Failed to load trend');
        console.error('Failed to load trend:', err);
      } finally {
        setLoading(false);
      }
    };

    loadTrend();
  }, [domain, getDomainTrend, externalData]);

  const isLoading = externalData ? false : (loading || dashLoading);
  const displayError = externalData ? null : (error || dashError);

  if (isLoading) return <div>Loading...</div>;
  if (displayError) return <div>Error: {displayError}</div>;

  const chartTitle = title
    || (domain ? domain.replace('_', ' ').toUpperCase() + ' Trend' : 'Trend');

  const avgScore = data.length > 0
    ? (data.reduce((sum, d) => sum + d.score, 0) / data.length)
    : 0;

  const maxScore = data.length > 0 ? Math.max(...data.map(d => d.score)) : 0;

  return (
    <Card>
      <h3>{chartTitle}</h3>
      <div style={{ marginTop: 'var(--space-4)', minHeight: '200px' }}>
        {data.length > 0 ? (
          <div>
            <div style={{ display: 'flex', gap: 'var(--space-6)', marginBottom: 'var(--space-4)' }}>
              <p style={{ margin: 0 }}>Average: <strong>{avgScore.toFixed(1)}%</strong></p>
              <p style={{ margin: 0 }}>Sessions: <strong>{data.length}</strong></p>
            </div>
            <div style={{
              display: 'flex',
              alignItems: 'flex-end',
              gap: '2px',
              height: '120px',
              padding: 'var(--space-2) 0',
            }}>
              {data.map((d, i) => {
                const barHeight = maxScore > 0 ? (d.score / maxScore) * 100 : 0;
                return (
                  <div
                    key={i}
                    title={`${new Date(d.date).toLocaleDateString()}: ${d.score.toFixed(1)}%`}
                    style={{
                      flex: 1,
                      minWidth: '4px',
                      height: `${Math.max(barHeight, 2)}%`,
                      backgroundColor: 'var(--color-accent)',
                      borderRadius: 'var(--radius-sm) var(--radius-sm) 0 0',
                      transition: 'var(--transition-default)',
                    }}
                  />
                );
              })}
            </div>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: 'var(--text-body-sm)',
              color: 'var(--color-text-secondary)',
              marginTop: 'var(--space-2)',
            }}>
              {data.length > 0 && (
                <>
                  <span>{new Date(data[0].date).toLocaleDateString()}</span>
                  <span>{new Date(data[data.length - 1].date).toLocaleDateString()}</span>
                </>
              )}
            </div>
          </div>
        ) : (
          <p>No data available</p>
        )}
      </div>
    </Card>
  );
};

export default TrendChart;
