import React from 'react';
import { ArrowLeft, Sparkles, TrendingUp, TrendingDown } from 'lucide-react';
import { PillBadge } from '../components/ui';
import type { Trade } from '../types/trading';

export interface TradeHistoryScreenProps {
  trades: Trade[];
  onBack?: () => void;
}

interface PerformanceSummary {
  totalTrades: number;
  winRate: number;
  sharpe: number;
}

const TradeCard: React.FC<{ trade: Trade }> = ({ trade }) => {
  const isProfitable = trade.pnl >= 0;
  const pillVariant = trade.signalType === 'SELL' ? 'rose' : 'teal';

  return (
    <div className="bg-white rounded-2xl shadow-md p-6 space-y-4">
      {/* Symbol and Signal */}
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-base font-mono text-black mb-2">
            {trade.symbol}
          </h3>
          <PillBadge variant={pillVariant} className="text-xs">
            {trade.ivPercentile}%ile → {trade.signalType}
          </PillBadge>
        </div>
      </div>

      {/* Entry/Exit Prices */}
      <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-100">
        <div>
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">
            Entry
          </div>
          <div className="text-base font-mono text-black">
            ${trade.entryPrice.toFixed(2)}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">
            Exit
          </div>
          <div className="text-base font-mono text-black">
            ${trade.exitPrice.toFixed(2)}
          </div>
        </div>
      </div>

      {/* P&L */}
      <div className={`flex items-center gap-2 text-xl font-mono font-semibold ${
        isProfitable ? 'text-emerald' : 'text-rose'
      }`}>
        {isProfitable ? (
          <TrendingUp className="w-5 h-5" />
        ) : (
          <TrendingDown className="w-5 h-5" />
        )}
        <span>
          {isProfitable ? '+' : ''}${Math.abs(trade.pnl).toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
          })}
        </span>
        <span className="text-sm">
          ({isProfitable ? '+' : ''}{trade.pnlPercent.toFixed(1)}%)
        </span>
      </div>

      {/* Costs */}
      <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-100">
        <div>
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">
            Commission
          </div>
          <div className="text-sm font-mono text-gray-600">
            ${trade.commission.toFixed(2)}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">
            Slippage
          </div>
          <div className="text-sm font-mono text-gray-600">
            ${trade.slippage.toFixed(2)}
          </div>
        </div>
      </div>

      {/* Timestamp */}
      <div className="text-xs text-gray-400 text-right">
        {trade.timestamp}
      </div>
    </div>
  );
};

const PerformanceCard: React.FC<{ summary: PerformanceSummary }> = ({ summary }) => {
  return (
    <div className="bg-black border-2 border-teal rounded-2xl shadow-md p-6">
      <h3 className="text-lg font-semibold text-white mb-4">
        Performance Summary
      </h3>
      <div className="grid grid-cols-3 gap-4">
        <div>
          <div className="text-xs text-gray-400 uppercase tracking-wide mb-1">
            Total
          </div>
          <div className="text-xl font-mono font-semibold text-white">
            {summary.totalTrades}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-400 uppercase tracking-wide mb-1">
            Win Rate
          </div>
          <div className="text-xl font-mono font-semibold text-teal">
            {summary.winRate.toFixed(1)}%
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-400 uppercase tracking-wide mb-1">
            Sharpe
          </div>
          <div className="text-xl font-mono font-semibold text-white">
            {summary.sharpe.toFixed(2)}
          </div>
        </div>
      </div>
    </div>
  );
};

export const TradeHistoryScreen: React.FC<TradeHistoryScreenProps> = ({
  trades,
  onBack
}) => {
  // Calculate performance summary
  const winningTrades = trades.filter(t => t.pnl > 0).length;
  const summary: PerformanceSummary = {
    totalTrades: trades.length,
    winRate: trades.length > 0 ? (winningTrades / trades.length) * 100 : 0,
    sharpe: 1.84, // Mock value - would be calculated from actual data
  };

  return (
    <div className="min-h-screen bg-cream px-6 py-8 max-w-md mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-black hover:text-gray-700 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          <span className="font-medium">Trade History</span>
        </button>
        <Sparkles className="w-5 h-5 text-black" />
      </div>

      {/* Trade Cards */}
      <div className="space-y-4 mb-6">
        {trades.length > 0 ? (
          trades.map((trade, index) => (
            <TradeCard key={index} trade={trade} />
          ))
        ) : (
          <div className="bg-white rounded-2xl shadow-md p-8 text-center">
            <p className="text-gray-500">No trades yet</p>
          </div>
        )}
      </div>

      {/* Performance Summary */}
      {trades.length > 0 && (
        <PerformanceCard summary={summary} />
      )}
    </div>
  );
};
