import { Position } from '../api';
import './Positions.css';

interface PositionsProps {
  positions: Position[];
  loading: boolean;
}

function Positions({ positions, loading }: PositionsProps) {
  if (loading) {
    return (
      <section className="card">
        <h2>Active Positions</h2>
        <div className="loading-spinner">Loading positions...</div>
      </section>
    );
  }

  if (positions.length === 0) {
    return (
      <section className="card">
        <h2>Active Positions</h2>
        <div className="empty-state">
          <p>No open positions</p>
          <p className="empty-state-subtitle">
            The monitor will automatically open positions when IV signals are detected
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="card">
      <h2>Active Positions ({positions.length})</h2>
      <div className="positions-grid">
        {positions.map((position) => {
          const pnlPercent = position.entry_price
            ? ((position.current_price - position.entry_price) / position.entry_price) * 100
            : 0;
          const isProfitable = pnlPercent > 0;

          // Calculate progress toward exit conditions
          const profitProgress = Math.min((pnlPercent / 50) * 100, 100); // 50% profit target
          const lossProgress = Math.min((Math.abs(pnlPercent) / 75) * 100, 100); // 75% stop loss

          // Calculate days to expiration (simplified)
          const daysToExp = position.symbol ? parseInt(position.symbol.substring(8, 10)) || 45 : 45;
          const dteProgress = ((45 - daysToExp) / (45 - 21)) * 100; // From 45 DTE to 21 DTE

          return (
            <div key={position.id} className="position-card">
              <div className="position-header">
                <div>
                  <h3 className="position-symbol">{position.symbol}</h3>
                  <div className="position-meta">
                    <span className="badge badge-strategy">{position.strategy}</span>
                    <span className={`badge badge-${position.position_type}`}>
                      {position.position_type.toUpperCase()}
                    </span>
                  </div>
                </div>
                <div className="position-pnl">
                  <div className={`pnl-value ${isProfitable ? 'positive' : 'negative'}`}>
                    ${position.unrealized_pnl.toFixed(2)}
                  </div>
                  <div className={`pnl-percent ${isProfitable ? 'positive' : 'negative'}`}>
                    {pnlPercent > 0 ? '+' : ''}{pnlPercent.toFixed(1)}%
                  </div>
                </div>
              </div>

              <div className="position-details">
                <div className="detail-row">
                  <span className="detail-label">Quantity:</span>
                  <span className="detail-value">{position.quantity} contracts</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Entry:</span>
                  <span className="detail-value">${position.entry_price.toFixed(2)}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Current:</span>
                  <span className="detail-value">${position.current_price.toFixed(2)}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Opened:</span>
                  <span className="detail-value">
                    {new Date(position.opened_at).toLocaleString()}
                  </span>
                </div>
              </div>

              <div className="exit-conditions">
                <h4>Exit Conditions</h4>

                {/* Profit Target */}
                <div className="condition-item">
                  <div className="condition-header">
                    <span className="condition-label">💰 Profit Target (50%)</span>
                    <span className={`condition-value ${profitProgress >= 100 ? 'triggered' : ''}`}>
                      {pnlPercent > 0 ? `${pnlPercent.toFixed(1)}%` : '0%'} / 50%
                    </span>
                  </div>
                  <div className="progress-bar">
                    <div
                      className="progress-fill profit"
                      style={{ width: `${Math.min(profitProgress, 100)}%` }}
                    />
                  </div>
                </div>

                {/* Stop Loss */}
                <div className="condition-item">
                  <div className="condition-header">
                    <span className="condition-label">🛑 Stop Loss (75%)</span>
                    <span className={`condition-value ${lossProgress >= 100 ? 'triggered' : ''}`}>
                      {pnlPercent < 0 ? `${Math.abs(pnlPercent).toFixed(1)}%` : '0%'} / 75%
                    </span>
                  </div>
                  <div className="progress-bar">
                    <div
                      className="progress-fill loss"
                      style={{ width: `${Math.min(lossProgress, 100)}%` }}
                    />
                  </div>
                </div>

                {/* DTE Threshold */}
                <div className="condition-item">
                  <div className="condition-header">
                    <span className="condition-label">⏰ DTE Threshold (21 days)</span>
                    <span className={`condition-value ${dteProgress >= 100 ? 'triggered' : ''}`}>
                      {daysToExp} DTE
                    </span>
                  </div>
                  <div className="progress-bar">
                    <div
                      className="progress-fill dte"
                      style={{ width: `${Math.min(dteProgress, 100)}%` }}
                    />
                  </div>
                </div>
              </div>

              <div className="position-footer">
                <span className="monitor-status">
                  🔄 Monitored every 60 seconds
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

export default Positions;
