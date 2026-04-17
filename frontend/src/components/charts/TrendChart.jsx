import React, { useEffect, useState } from 'react';
import Card from '../ui/Card';
import { useDashboard } from '../../hooks/useDashboard';

const TrendChart = ({ domain }) => {
  const { getDomainTrend, loading, error } = useDashboard();
  const [data, setData] = useState([]);

  useEffect(() => {
    const loadTrend = async () => {
      try {
        const trend = await getDomainTrend(domain);
        setData(trend.data);
      } catch (err) {
        console.error('Failed to load trend:', err);
      }
    };

    loadTrend();
  }, [domain, getDomainTrend]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  const avgScore = data.length > 0
    ? (data.reduce((sum, d) => sum + d.score, 0) / data.length)
    : 0;

  return (
    <Card>
      <h3>{domain.replace('_', ' ').toUpperCase()} Trend</h3>
      <div style={{ marginTop: 'var(--space-4)', minHeight: '200px' }}>
        {data.length > 0 ? (
          <div>
            <p>Average Score: {avgScore.toFixed(1)}%</p>
            <p>Total Sessions: {data.length}</p>
            <div style={{ fontSize: 'var(--text-body-sm)', marginTop: 'var(--space-4)' }}>
              {data.slice(-5).map((d, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: 'var(--space-2) 0' }}>
                  <span>{new Date(d.date).toLocaleDateString()}</span>
                  <span>{d.score.toFixed(1)}%</span>
                </div>
              ))}
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
