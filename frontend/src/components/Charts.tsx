import React from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Trade } from '../api';
import '../styles/Charts.css';

interface ChartsProps {
  trades: Trade[];
}

interface CumulativePnL {
  index: number;
  pnl: number;
  cumulativePnL: number;
  date: string;
}

interface DailyMetrics {
  date: string;
  wins: number;
  losses: number;
  pnl: number;
}

export const Charts: React.FC<ChartsProps> = ({ trades }) => {
  const generatePnLData = (): CumulativePnL[] => {
    let cumulativePnL = 0;
    return trades.map((trade, index) => {
      cumulativePnL += trade.pnl;
      return {
        index,
        pnl: trade.pnl,
        cumulativePnL,
        date: new Date(trade.timestamp).toLocaleDateString(),
      };
    });
  };

  const generateDailyMetrics = (): DailyMetrics[] => {
    const dailyMap = new Map<string, DailyMetrics>();

    trades.forEach((trade) => {
      const date = new Date(trade.timestamp).toLocaleDateString();
      const existing = dailyMap.get(date) || {
        date,
        wins: 0,
        losses: 0,
        pnl: 0,
      };

      if (trade.pnl > 0) {
        existing.wins += 1;
      } else if (trade.pnl < 0) {
        existing.losses += 1;
      }
      existing.pnl += trade.pnl;

      dailyMap.set(date, existing);
    });

    return Array.from(dailyMap.values()).slice(-30); // Last 30 days
  };

  const pnlData = generatePnLData();
  const dailyData = generateDailyMetrics();

  return (
    <div className="charts-container">
      <h2>Performance Charts</h2>

      {trades.length === 0 ? (
        <div className="no-data">No trades to display. Charts will appear after trades are executed.</div>
      ) : (
        <>
          {/* Cumulative P&L Chart */}
          <div className="chart-section">
            <h3>Cumulative P&L</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={pnlData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="index" />
                <YAxis />
                <Tooltip
                  formatter={(value: number) => `$${value.toFixed(2)}`}
                  labelFormatter={(label) => `Trade #${label}`}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="cumulativePnL"
                  stroke="#2ecc71"
                  name="Cumulative P&L"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Daily Metrics Chart */}
          {dailyData.length > 0 && (
            <div className="chart-section">
              <h3>Daily Wins vs Losses</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={dailyData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="wins" stackId="a" fill="#2ecc71" name="Wins" />
                  <Bar dataKey="losses" stackId="a" fill="#e74c3c" name="Losses" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Daily P&L Chart */}
          {dailyData.length > 0 && (
            <div className="chart-section">
              <h3>Daily P&L</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={dailyData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip formatter={(value: number) => `$${value.toFixed(2)}`} />
                  <Legend />
                  <Bar
                    dataKey="pnl"
                    fill="#3498db"
                    name="Daily P&L"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default Charts;
