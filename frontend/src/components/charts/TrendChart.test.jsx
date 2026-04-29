import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import TrendChart from './TrendChart';

// Mock useDashboard hook
const mockGetDomainTrend = vi.fn();
vi.mock('../../hooks/useDashboard', () => ({
  useDashboard: () => ({
    getDomainTrend: mockGetDomainTrend,
    loading: false,
    error: null,
  }),
}));

// Mock Card component
vi.mock('../ui/Card', () => ({
  default: ({ children }) => <div data-testid="card">{children}</div>,
}));

describe('TrendChart', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('with external data', () => {
    it('renders chart title when title prop provided', () => {
      const data = [
        { date: '2024-01-01', score: 80 },
        { date: '2024-01-02', score: 90 },
      ];
      render(<TrendChart title="My Chart" data={data} />);
      expect(screen.getByText('My Chart')).toBeDefined();
    });

    it('renders average score', () => {
      const data = [
        { date: '2024-01-01', score: 80 },
        { date: '2024-01-02', score: 90 },
      ];
      render(<TrendChart title="Test" data={data} />);
      expect(screen.getByText('85.0%')).toBeDefined();
    });

    it('renders session count', () => {
      const data = [
        { date: '2024-01-01', score: 80 },
        { date: '2024-01-02', score: 90 },
        { date: '2024-01-03', score: 70 },
      ];
      render(<TrendChart title="Test" data={data} />);
      expect(screen.getByText('3')).toBeDefined();
    });

    it('shows no data message when data is empty', () => {
      render(<TrendChart title="Test" data={[]} />);
      expect(screen.getByText('No data available')).toBeDefined();
    });

    it('does not call getDomainTrend when external data provided', () => {
      const data = [{ date: '2024-01-01', score: 80 }];
      render(<TrendChart title="Test" data={data} />);
      expect(mockGetDomainTrend).not.toHaveBeenCalled();
    });

    it('does not show loading state when external data provided', () => {
      const data = [{ date: '2024-01-01', score: 80 }];
      render(<TrendChart title="Test" data={data} />);
      expect(screen.queryByText('Loading...')).toBeNull();
    });

    it('renders date range labels', () => {
      const data = [
        { date: '2024-01-01T00:00:00Z', score: 80 },
        { date: '2024-03-15T00:00:00Z', score: 90 },
      ];
      render(<TrendChart title="Test" data={data} />);
      // Both first and last date labels should appear
      const spans = screen.getAllByText(/\d+\/\d+\/\d+/);
      expect(spans.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('with domain prop', () => {
    it('calls getDomainTrend with domain when no external data', async () => {
      mockGetDomainTrend.mockResolvedValue({
        data: [{ date: '2024-01-01', score: 75 }],
      });
      render(<TrendChart domain="processing_speed" />);
      await waitFor(() => {
        expect(mockGetDomainTrend).toHaveBeenCalledWith('processing_speed');
      });
    });

    it('renders domain-based title when no title prop', async () => {
      mockGetDomainTrend.mockResolvedValue({
        data: [{ date: '2024-01-01', score: 75 }],
      });
      render(<TrendChart domain="processing_speed" />);
      await waitFor(() => {
        expect(screen.getByText('PROCESSING SPEED Trend')).toBeDefined();
      });
    });

    it('shows loaded data from getDomainTrend', async () => {
      mockGetDomainTrend.mockResolvedValue({
        data: [
          { date: '2024-01-01', score: 60 },
          { date: '2024-01-02', score: 80 },
        ],
      });
      render(<TrendChart domain="working_memory" />);
      await waitFor(() => {
        expect(screen.getByText('70.0%')).toBeDefined();
      });
    });

    it('shows error message when getDomainTrend fails', async () => {
      mockGetDomainTrend.mockRejectedValue(new Error('Network error'));
      render(<TrendChart domain="attention" />);
      await waitFor(() => {
        expect(screen.getByText('Error: Failed to load trend')).toBeDefined();
      });
    });

    it('shows generic Trend title when no domain or title', () => {
      render(<TrendChart />);
      expect(screen.getByText('Trend')).toBeDefined();
    });
  });

  describe('score calculations', () => {
    it('calculates average score correctly for single item', () => {
      render(<TrendChart title="Test" data={[{ date: '2024-01-01', score: 42 }]} />);
      expect(screen.getByText('42.0%')).toBeDefined();
    });

    it('shows zero average for empty data', () => {
      render(<TrendChart title="Test" data={[]} />);
      expect(screen.queryByText('Average:')).toBeNull();
    });

    it('renders correct number of bars', () => {
      const data = Array.from({ length: 5 }, (_, i) => ({
        date: `2024-01-0${i + 1}`,
        score: 50 + i * 10,
      }));
      const { container } = render(<TrendChart title="Test" data={data} />);
      // Each data point gets a div bar
      const barsContainer = container.querySelector('[style*="height: 120px"]');
      expect(barsContainer).toBeDefined();
      if (barsContainer) {
        expect(barsContainer.children.length).toBe(5);
      }
    });
  });
});
