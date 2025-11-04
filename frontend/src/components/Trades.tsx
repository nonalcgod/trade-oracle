import React from 'react';
import { Trade } from '../api';
import '../styles/Trades.css';
import { formatDistanceToNow } from 'date-fns';

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

  const getTradeColor = (pnl: number) => {
    if (pnl > 0) return 'positive';
    if (pnl < 0) return 'negative';
    return 'neutral';
  };

  return (
    <div className="trades-container">
      <h2>Recent Trades</h2>

      {loading && <div className="loading">Loading trades...</div>}

      {!loading && trades.length === 0 && (
        <div className="no-trades">No trades yet. Waiting for signals...</div>
      )}

      {!loading && trades.length > 0 && (
        <div className="trades-table-wrapper">
          <table className="trades-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Symbol</th>
                <th>Type</th>
                <th>Entry Price</th>
                <th>Exit Price</th>
                <th>Qty</th>
                <th>P&L</th>
                <th>Strategy</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((trade) => (
                <tr key={trade.id} className={`trade-row ${getTradeColor(trade.pnl)}`}>
                  <td className="timestamp">
                    {formatDistanceToNow(new Date(trade.timestamp), { addSuffix: true })}
                  </td>
                  <td className="symbol">{trade.symbol}</td>
                  <td className="signal-type">
                    <span className={`badge ${trade.signal_type}`}>{trade.signal_type.toUpperCase()}</span>
                  </td>
                  <td className="price">{formatCurrency(trade.entry_price)}</td>
                  <td className="price">{trade.exit_price ? formatCurrency(trade.exit_price) : '-'}</td>
                  <td className="quantity">{trade.quantity}</td>
                  <td className={`pnl ${getTradeColor(trade.pnl)}`}>{formatCurrency(trade.pnl)}</td>
                  <td className="strategy">{trade.strategy}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default Trades;
