import React from 'react';
import { PortfolioData } from '../api';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface PortfolioProps {
  portfolio: PortfolioData;
}

export const Portfolio: React.FC<PortfolioProps> = ({ portfolio }) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const dailyPnLPercent = portfolio.balance > 0 ? (portfolio.daily_pnl / portfolio.balance) * 100 : 0;
  const isProfitable = portfolio.daily_pnl >= 0;

  return (
    <section className="space-y-6">
      {/* Hero Balance Card */}
      <div className="bg-white rounded-2xl border-2 border-black p-8 text-center shadow-lg">
        <p className="text-xs uppercase tracking-wide text-gray-warm mb-2">
          Portfolio Balance
        </p>
        <h1 className="text-5xl lg:text-6xl font-mono font-bold text-black mb-4">
          {formatCurrency(portfolio.balance)}
        </h1>
        <div className="flex items-center justify-center gap-2">
          {isProfitable ? (
            <TrendingUp size={24} className="text-emerald" />
          ) : (
            <TrendingDown size={24} className="text-rose" />
          )}
          <span className={`text-2xl font-mono ${isProfitable ? 'text-emerald' : 'text-rose'}`}>
            {formatCurrency(portfolio.daily_pnl)} ({formatPercent(dailyPnLPercent)})
          </span>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Win Rate - Mint Background */}
        <div className="bg-[#E8F5E9] rounded-2xl p-8 border-2 border-black shadow-md">
          <p className="text-xs uppercase tracking-wide text-gray-600 mb-2">
            Win Rate
          </p>
          <p className="text-3xl font-mono font-bold text-black">
            {(portfolio.win_rate * 100).toFixed(1)}%
          </p>
        </div>

        {/* Delta - Cream Background */}
        <div className="bg-[#FFF8E1] rounded-2xl p-8 border-2 border-black shadow-md">
          <p className="text-xs uppercase tracking-wide text-gray-600 mb-2">
            Portfolio Delta
          </p>
          <p className="text-3xl font-mono font-bold text-black">
            {portfolio.delta >= 0 ? '+' : ''}{portfolio.delta.toFixed(1)}
          </p>
        </div>

        {/* Theta - Blue Background */}
        <div className="bg-[#E3F2FD] rounded-2xl p-8 border-2 border-black shadow-md">
          <p className="text-xs uppercase tracking-wide text-gray-600 mb-2">
            Portfolio Theta
          </p>
          <p className="text-3xl font-mono font-bold text-black">
            {portfolio.theta.toFixed(2)}
          </p>
        </div>

        {/* Consecutive Losses - Pink Background */}
        <div className="bg-[#FCE4EC] rounded-2xl p-8 border-2 border-black shadow-md">
          <p className="text-xs uppercase tracking-wide text-gray-600 mb-2">
            Consecutive Losses
          </p>
          <p className="text-3xl font-mono font-bold text-black">
            {portfolio.consecutive_losses}/3
          </p>
        </div>
      </div>
    </section>
  );
};

export default Portfolio;
