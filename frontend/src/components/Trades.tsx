import React from 'react';
import { Trade } from '../api';
import { formatDistanceToNow } from 'date-fns';
import { PillBadge } from './ui/PillBadge';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface TradesProps {
  trades: Trade[];
  loading: boolean;
}

export const Trades: React.FC<TradesProps> = ({ trades, loading }) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  // Extract IV percentile from reasoning if available (placeholder logic)
  const getIVPercentile = (reasoning: string): number | null => {
    // Look for patterns like "73%ile" or "percentile: 73"
    const match = reasoning.match(/(\d+)(?:%ile|th percentile)/i);
    return match ? parseInt(match[1]) : null;
  };

  if (loading) {
    return (
      <section className="bg-white rounded-2xl border-2 border-black p-8 shadow-md">
        <h2 className="text-2xl font-sans font-semibold text-black mb-4">Recent Trades</h2>
        <div className="text-center text-gray-warm py-8">Loading trades...</div>
      </section>
    );
  }

  if (trades.length === 0) {
    return (
      <section className="bg-white rounded-2xl border-2 border-black p-8 shadow-md">
        <h2 className="text-2xl font-sans font-semibold text-black mb-4">Recent Trades</h2>
        <div className="text-center text-gray-warm py-8">
          No trades yet. Waiting for signals...
        </div>
      </section>
    );
  }

  return (
    <section className="bg-white rounded-2xl border-2 border-black p-8 shadow-md">
      <h2 className="text-2xl font-sans font-semibold text-black mb-6">Recent Trades</h2>

      {/* Card Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {trades.map((trade) => {
          const ivPercentile = getIVPercentile(trade.reasoning);
          const isProfitable = trade.pnl >= 0;

          return (
            <div key={trade.id} className="bg-white border-2 border-black rounded-2xl p-6 shadow-md transition-all hover:shadow-lg">
              {/* Header */}
              <div className="mb-3">
                <h3 className="text-sm font-mono text-black mb-2 truncate">{trade.symbol}</h3>
                <div className="flex items-center gap-2">
                  {ivPercentile !== null && (
                    <PillBadge variant={trade.signal_type === 'buy' ? 'teal' : 'rose'}>
                      {ivPercentile}%ile → {trade.signal_type.toUpperCase()}
                    </PillBadge>
                  )}
                  {!ivPercentile && (
                    <PillBadge variant={trade.signal_type === 'buy' ? 'teal' : 'rose'}>
                      {trade.signal_type.toUpperCase()}
                    </PillBadge>
                  )}
                </div>
              </div>

              {/* Prices */}
              <div className="space-y-1 mb-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-warm">Entry:</span>
                  <span className="font-mono text-black">{formatCurrency(trade.entry_price)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-warm">Exit:</span>
                  <span className="font-mono text-black">
                    {trade.exit_price ? formatCurrency(trade.exit_price) : '-'}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-warm">Qty:</span>
                  <span className="font-mono text-black">{trade.quantity}</span>
                </div>
              </div>

              {/* P&L */}
              <div className={`flex items-center justify-between p-3 rounded-xl mb-3 ${
                isProfitable ? 'bg-emerald/10' : 'bg-rose/10'
              }`}>
                {isProfitable ? (
                  <TrendingUp size={20} className="text-emerald" />
                ) : (
                  <TrendingDown size={20} className="text-rose" />
                )}
                <div className="text-right">
                  <p className={`text-lg font-mono font-bold ${isProfitable ? 'text-emerald' : 'text-rose'}`}>
                    {formatCurrency(trade.pnl)}
                  </p>
                </div>
              </div>

              {/* Costs */}
              <div className="space-y-1 mb-3 text-xs">
                <div className="flex justify-between text-gray-warm">
                  <span>Commission:</span>
                  <span className="font-mono">{formatCurrency(trade.commission)}</span>
                </div>
                <div className="flex justify-between text-gray-warm">
                  <span>Slippage:</span>
                  <span className="font-mono">{formatCurrency(trade.slippage)}</span>
                </div>
              </div>

              {/* Timestamp */}
              <div className="text-xs text-gray-warm text-right">
                {formatDistanceToNow(new Date(trade.timestamp), { addSuffix: true })}
              </div>
            </div>
          );
        })}
      </div>

      {/* Trade Summary - Ben AI Style */}
      {trades.length > 0 && (
        <div className="mt-6 bg-white rounded-2xl border-2 border-black p-8 shadow-md">
          <h3 className="text-lg font-semibold text-black mb-4">Trade Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p className="text-xs uppercase tracking-wide text-gray-600 mb-1">Total Trades</p>
              <p className="text-2xl font-mono font-bold text-black">{trades.length}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-gray-600 mb-1">Win Rate</p>
              <p className="text-2xl font-mono font-bold text-black">
                {((trades.filter(t => t.pnl > 0).length / trades.length) * 100).toFixed(1)}%
              </p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-gray-600 mb-1">Total P&L</p>
              <p className={`text-2xl font-mono font-bold ${
                trades.reduce((sum, t) => sum + t.pnl, 0) >= 0 ? 'text-emerald' : 'text-rose'
              }`}>
                {formatCurrency(trades.reduce((sum, t) => sum + t.pnl, 0))}
              </p>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};

export default Trades;
