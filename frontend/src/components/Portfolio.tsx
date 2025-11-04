import React from 'react';
import { PortfolioData } from '../api';
import '../styles/Portfolio.css';

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
    return `${(value * 100).toFixed(2)}%`;
  };

  return (
    <div className="portfolio-container">
      <h2>Portfolio Overview</h2>

      <div className="portfolio-grid">
        <div className="portfolio-card">
          <div className="card-label">Account Balance</div>
          <div className="card-value">{formatCurrency(portfolio.balance)}</div>
          <div className="card-subtext">Total equity</div>
        </div>

        <div className="portfolio-card">
          <div className="card-label">Daily P&L</div>
          <div className={`card-value ${portfolio.daily_pnl >= 0 ? 'positive' : 'negative'}`}>
            {formatCurrency(portfolio.daily_pnl)}
          </div>
          <div className="card-subtext">
            {portfolio.daily_pnl >= 0 ? 'Profitable' : 'Loss'}
          </div>
        </div>

        <div className="portfolio-card">
          <div className="card-label">Win Rate</div>
          <div className="card-value">{formatPercent(portfolio.win_rate)}</div>
          <div className="card-subtext">Trading success</div>
        </div>

        <div className="portfolio-card">
          <div className="card-label">Active Positions</div>
          <div className="card-value">{portfolio.active_positions}</div>
          <div className="card-subtext">Open trades</div>
        </div>

        <div className="portfolio-card">
          <div className="card-label">Portfolio Delta</div>
          <div className="card-value">{portfolio.delta.toFixed(2)}</div>
          <div className="card-subtext">Directional exposure</div>
        </div>

        <div className="portfolio-card">
          <div className="card-label">Portfolio Theta</div>
          <div className="card-value">{portfolio.theta.toFixed(4)}</div>
          <div className="card-subtext">Daily decay</div>
        </div>

        <div className="portfolio-card">
          <div className="card-label">Consecutive Losses</div>
          <div className={`card-value ${portfolio.consecutive_losses > 0 ? 'warning' : 'good'}`}>
            {portfolio.consecutive_losses}
          </div>
          <div className="card-subtext">
            {portfolio.consecutive_losses >= 3 ? 'Trading paused' : 'Good'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Portfolio;
