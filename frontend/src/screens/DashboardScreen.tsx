import React from 'react';
import { TrendingUp, TrendingDown, Settings, Sparkles } from 'lucide-react';
import { PillBadge, StatusDot, MetricCard } from '../components/ui';
import type { Portfolio } from '../types/trading';

export interface DashboardScreenProps {
  portfolio: Portfolio;
  onViewTrades?: () => void;
}

export const DashboardScreen: React.FC<DashboardScreenProps> = ({
  portfolio,
  onViewTrades
}) => {
  const isProfitable = portfolio.dailyPnL >= 0;
  const secondsSinceUpdate = Math.round(
    (Date.now() - new Date(portfolio.lastUpdate).getTime()) / 1000
  );

  // Determine win rate color
  const getWinRateColor = () => {
    if (portfolio.winRate >= 70) return 'teal';
    if (portfolio.winRate >= 50) return 'amber';
    return 'red';
  };

  // Determine consecutive losses status
  const getLossesColor = () => {
    if (portfolio.consecutiveLosses >= 3) return 'red';
    if (portfolio.consecutiveLosses >= 2) return 'amber';
    return 'teal';
  };

  return (
    <div className="min-h-screen bg-cream px-6 py-8 max-w-md mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <PillBadge variant="rose" className="text-xs">
          PAPER TRADING
        </PillBadge>
        <button className="p-2 hover:bg-gray-200 rounded-full transition-colors">
          <Settings className="w-5 h-5 text-black" />
        </button>
      </div>

      {/* Title */}
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-black mb-1">
          Trade Oracle
        </h1>
        <p className="text-sm text-gray-warm">
          IV Mean Reversion
        </p>
      </div>

      {/* Portfolio Balance Card */}
      <div className="bg-white rounded-2xl shadow-md p-6 mb-6">
        <div className="text-center mb-4">
          <div className="text-5xl font-mono font-bold text-black mb-2">
            ${portfolio.balance.toLocaleString('en-US', {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2
            })}
          </div>
          <div className={`flex items-center justify-center gap-2 text-2xl font-mono ${
            isProfitable ? 'text-emerald' : 'text-rose'
          }`}>
            {isProfitable ? (
              <TrendingUp className="w-6 h-6" />
            ) : (
              <TrendingDown className="w-6 h-6" />
            )}
            <span>
              {isProfitable ? '+' : ''}${Math.abs(portfolio.dailyPnL).toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
              })}
            </span>
            <span className="text-lg">
              ({isProfitable ? '+' : ''}{portfolio.dailyPnLPercent.toFixed(2)}%)
            </span>
          </div>
        </div>

        <div className="flex items-center justify-center gap-4 pt-4 border-t border-gray-200">
          <StatusDot status="connected" label="Connected" />
          <span className="text-sm text-gray-400">
            Updated {secondsSinceUpdate}s ago
          </span>
        </div>
      </div>

      {/* Metrics Card */}
      <div className="bg-black border-2 border-teal rounded-2xl shadow-md p-6 mb-6">
        <div className="grid grid-cols-2 gap-6">
          <MetricCard
            label="Win Rate"
            value={`${portfolio.winRate.toFixed(1)}%`}
            color={getWinRateColor()}
          />
          <MetricCard
            label="Delta"
            value={portfolio.delta >= 0 ? `+${portfolio.delta.toFixed(1)}` : portfolio.delta.toFixed(1)}
            color="white"
          />
          <div className="flex flex-col">
            <span className="text-sm text-gray-400 uppercase tracking-wide mb-1">
              Consec. Losses
            </span>
            <div className="flex items-center gap-2">
              <span className={`text-xl font-mono font-semibold ${
                getLossesColor() === 'red' ? 'text-rose' :
                getLossesColor() === 'amber' ? 'text-amber' : 'text-teal'
              }`}>
                {portfolio.consecutiveLosses}/3
              </span>
              {portfolio.consecutiveLosses >= 2 && (
                <span className="text-amber">⚠️</span>
              )}
            </div>
          </div>
          <MetricCard
            label="Theta"
            value={portfolio.theta.toFixed(1)}
            color="white"
          />
        </div>
      </div>

      {/* View Trades Button */}
      <button
        onClick={onViewTrades}
        className="w-full bg-black text-white py-4 rounded-xl font-medium shadow-lg hover:scale-105 transition-transform mb-6"
      >
        View Trades →
      </button>

      {/* Footer */}
      <div className="text-center">
        <div className="flex items-center justify-center gap-2 text-sm text-gray-warm">
          <Sparkles className="w-4 h-4" />
          <span>Free Tier Services</span>
        </div>
        <p className="text-xs text-gray-400 mt-2">
          Railway • Vercel • Supabase • Alpaca Paper Trading
        </p>
      </div>
    </div>
  );
};
