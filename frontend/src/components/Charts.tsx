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

  if (trades.length === 0) {
    return (
      <section className="bg-white rounded-2xl border-2 border-black p-8 shadow-md">
        <h2 className="text-2xl font-sans font-semibold text-black mb-4">Performance Charts</h2>
        <div className="text-center text-gray-warm py-8">
          No trades to display. Charts will appear after trades are executed.
        </div>
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <h2 className="text-2xl font-sans font-semibold text-black">Performance Charts</h2>

      {/* Cumulative P&L Chart */}
      <div className="bg-white rounded-2xl border-2 border-black p-8 shadow-md">
        <h3 className="text-lg font-sans font-medium text-black mb-4">Cumulative P&L</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={pnlData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis dataKey="index" stroke="#6B7280" />
            <YAxis stroke="#6B7280" />
            <Tooltip
              formatter={(value: number) => `$${value.toFixed(2)}`}
              labelFormatter={(label) => `Trade #${label}`}
              contentStyle={{
                backgroundColor: 'white',
                border: '2px solid #14B8A6',
                borderRadius: '12px',
              }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="cumulativePnL"
              stroke="#14B8A6"
              strokeWidth={2}
              name="Cumulative P&L"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Daily Metrics Chart */}
      {dailyData.length > 0 && (
        <div className="bg-white rounded-2xl border-2 border-black p-8 shadow-md">
          <h3 className="text-lg font-sans font-medium text-black mb-4">Daily Wins vs Losses</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={dailyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="date" stroke="#6B7280" />
              <YAxis stroke="#6B7280" />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'white',
                  border: '2px solid #14B8A6',
                  borderRadius: '12px',
                }}
              />
              <Legend />
              <Bar dataKey="wins" stackId="a" fill="#10B981" name="Wins" />
              <Bar dataKey="losses" stackId="a" fill="#EF4444" name="Losses" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Daily P&L Chart */}
      {dailyData.length > 0 && (
        <div className="bg-white rounded-2xl border-2 border-black p-8 shadow-md">
          <h3 className="text-lg font-sans font-medium text-black mb-4">Daily P&L</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={dailyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="date" stroke="#6B7280" />
              <YAxis stroke="#6B7280" />
              <Tooltip
                formatter={(value: number) => `$${value.toFixed(2)}`}
                contentStyle={{
                  backgroundColor: 'white',
                  border: '2px solid #14B8A6',
                  borderRadius: '12px',
                }}
              />
              <Legend />
              <Bar
                dataKey="pnl"
                fill="#14B8A6"
                name="Daily P&L"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
};

export default Charts;
