/**
 * AutoTrade Component - One-Click Intelligent Trading
 *
 * Features:
 * - Single button to start auto-trade workflow
 * - Researches market conditions automatically
 * - Auto-selects best strategy
 * - Waits for market open if needed
 * - Executes trade automatically
 * - Shows live status updates
 */

import { useState, useEffect } from 'react';
import './AutoTrade.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface MarketConditions {
  vix_level: number | null;
  vix_interpretation: string;
  market_trend: string;
  economic_events_today: string[];
  recommended_strategy: string;
  confidence: number;
  reasoning: string;
}

interface TradeDetails {
  strategy: string;
  signal: any;
  order: any;
  result: any;
}

interface AutoTradeState {
  status: 'pending' | 'researching' | 'waiting_for_market' | 'executing' | 'monitoring' | 'completed' | 'failed';
  message: string;
  market_conditions: MarketConditions | null;
  selected_strategy: string | null;
  trade_details: TradeDetails | null;
  position_id: number | null;
  order_id: string | null;
  error: string | null;
  started_at: string;
  completed_at: string | null;
}

interface MarketStatus {
  is_open: boolean;
  seconds_until_open?: number;
  minutes_until_open?: number;
  hours_until_open?: number;
  message: string;
}

export default function AutoTrade() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [state, setState] = useState<AutoTradeState | null>(null);
  const [marketStatus, setMarketStatus] = useState<MarketStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch market status on mount
  useEffect(() => {
    fetchMarketStatus();
    const interval = setInterval(fetchMarketStatus, 30000); // Update every 30s
    return () => clearInterval(interval);
  }, []);

  // Poll for status updates when session is active
  useEffect(() => {
    if (!sessionId || !state || state.status === 'completed' || state.status === 'failed') {
      return;
    }

    const interval = setInterval(() => {
      fetchStatus();
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(interval);
  }, [sessionId, state]);

  const fetchMarketStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/api/auto-trade/market-status`);
      const data = await response.json();
      setMarketStatus(data);
    } catch (err) {
      console.error('Failed to fetch market status:', err);
    }
  };

  const fetchStatus = async () => {
    if (!sessionId) return;

    try {
      const response = await fetch(`${API_URL}/api/auto-trade/status/${sessionId}`);
      if (!response.ok) throw new Error('Failed to fetch status');

      const data = await response.json();
      setState(data);

      // Stop polling if completed or failed
      if (data.status === 'completed' || data.status === 'failed') {
        setIsLoading(false);
      }
    } catch (err) {
      console.error('Failed to fetch status:', err);
      setError('Failed to fetch status updates');
      setIsLoading(false);
    }
  };

  const startAutoTrade = async () => {
    setIsLoading(true);
    setError(null);
    setState(null);

    try {
      const response = await fetch(`${API_URL}/api/auto-trade/start`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to start auto-trade');
      }

      const data = await response.json();
      setSessionId(data.session_id);

      // Start polling for updates
      setTimeout(fetchStatus, 1000);
    } catch (err) {
      console.error('Failed to start auto-trade:', err);
      setError(err instanceof Error ? err.message : 'Failed to start auto-trade');
      setIsLoading(false);
    }
  };

  const cancelAutoTrade = async () => {
    if (!sessionId) return;

    try {
      await fetch(`${API_URL}/api/auto-trade/cancel/${sessionId}`, {
        method: 'DELETE',
      });

      setIsLoading(false);
      setState(null);
      setSessionId(null);
    } catch (err) {
      console.error('Failed to cancel:', err);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return '#10B981'; // green
      case 'failed':
        return '#EF4444'; // red
      case 'researching':
      case 'executing':
        return '#14B8A6'; // teal
      case 'waiting_for_market':
        return '#F59E0B'; // amber
      default:
        return '#6B7280'; // gray
    }
  };

  const getStrategyEmoji = (strategy: string | null) => {
    switch (strategy) {
      case 'iv_mean_reversion':
        return '📊';
      case 'iron_condor':
        return '🦅';
      case 'momentum_scalping':
        return '⚡';
      default:
        return '🤖';
    }
  };


  return (
    <div className="auto-trade-container">
      <div className="auto-trade-header">
        <h2>🤖 Auto-Trade</h2>
        <p className="subtitle">One-click intelligent trading with market research</p>
      </div>

      {/* Market Status Banner */}
      {marketStatus && (
        <div className={`market-status ${marketStatus.is_open ? 'open' : 'closed'}`}>
          <div className="status-indicator">
            <div className={`status-dot ${marketStatus.is_open ? 'pulse' : ''}`} />
            <span>{marketStatus.is_open ? 'Market Open' : 'Market Closed'}</span>
          </div>
          <p className="status-message">{marketStatus.message}</p>
        </div>
      )}

      {/* Main Action Button */}
      {!isLoading && !state && (
        <button
          className="auto-trade-button"
          onClick={startAutoTrade}
          disabled={isLoading}
        >
          <span className="button-icon">🚀</span>
          <span className="button-text">Start Auto-Trade</span>
          <span className="button-subtitle">Research → Select → Execute</span>
        </button>
      )}

      {/* Error Display */}
      {error && (
        <div className="error-banner">
          <span className="error-icon">⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {/* Status Display */}
      {state && (
        <div className="status-container">
          {/* Current Status */}
          <div className="status-card" style={{ borderColor: getStatusColor(state.status) }}>
            <div className="status-header">
              <div className="status-badge" style={{ backgroundColor: getStatusColor(state.status) }}>
                {state.status.replace('_', ' ').toUpperCase()}
              </div>
              {state.status !== 'completed' && state.status !== 'failed' && (
                <div className="spinner" />
              )}
            </div>
            <p className="status-message">{state.message}</p>
          </div>

          {/* Market Research Results */}
          {state.market_conditions && (
            <div className="research-card">
              <h3>📊 Market Research</h3>

              <div className="research-grid">
                <div className="research-item">
                  <span className="label">Market Trend:</span>
                  <span className="value">{state.market_conditions.market_trend}</span>
                </div>

                {state.market_conditions.vix_level && (
                  <div className="research-item">
                    <span className="label">VIX Level:</span>
                    <span className="value">{state.market_conditions.vix_level.toFixed(2)}</span>
                  </div>
                )}

                <div className="research-item">
                  <span className="label">VIX Interpretation:</span>
                  <span className="value">{state.market_conditions.vix_interpretation}</span>
                </div>

                <div className="research-item">
                  <span className="label">Recommended Strategy:</span>
                  <span className="value strategy">
                    {getStrategyEmoji(state.market_conditions.recommended_strategy)}
                    {state.market_conditions.recommended_strategy.replace(/_/g, ' ').toUpperCase()}
                  </span>
                </div>

                <div className="research-item">
                  <span className="label">Confidence:</span>
                  <span className="value">
                    <div className="confidence-bar">
                      <div
                        className="confidence-fill"
                        style={{ width: `${state.market_conditions.confidence * 100}%` }}
                      />
                    </div>
                    <span>{(state.market_conditions.confidence * 100).toFixed(0)}%</span>
                  </span>
                </div>
              </div>

              <div className="research-reasoning">
                <p className="label">Reasoning:</p>
                <p className="reasoning-text">{state.market_conditions.reasoning}</p>
              </div>

              {state.market_conditions.economic_events_today.length > 0 && (
                <div className="economic-events">
                  <p className="label">Today's Economic Events:</p>
                  <ul>
                    {state.market_conditions.economic_events_today.map((event, idx) => (
                      <li key={idx}>{event}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Trade Details */}
          {state.trade_details && (
            <div className="trade-card">
              <h3>📝 Trade Details</h3>

              {state.order_id && (
                <div className="trade-info">
                  <span className="label">Order ID:</span>
                  <span className="value monospace">{state.order_id}</span>
                </div>
              )}

              {state.position_id && (
                <div className="trade-info">
                  <span className="label">Position ID:</span>
                  <span className="value monospace">{state.position_id}</span>
                </div>
              )}

              <div className="trade-info">
                <span className="label">Strategy:</span>
                <span className="value">
                  {getStrategyEmoji(state.selected_strategy)}
                  {state.selected_strategy?.replace(/_/g, ' ').toUpperCase()}
                </span>
              </div>
            </div>
          )}

          {/* Completed / Failed State */}
          {state.status === 'completed' && (
            <div className="success-banner">
              <span className="success-icon">✅</span>
              <div>
                <p className="success-title">Trade Executed Successfully!</p>
                <p className="success-subtitle">Position is now being monitored automatically</p>
              </div>
            </div>
          )}

          {state.status === 'failed' && state.error && (
            <div className="error-banner">
              <span className="error-icon">❌</span>
              <div>
                <p className="error-title">Auto-Trade Failed</p>
                <p className="error-subtitle">{state.error}</p>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="action-buttons">
            {(state.status === 'completed' || state.status === 'failed') && (
              <button
                className="secondary-button"
                onClick={() => {
                  setState(null);
                  setSessionId(null);
                  setError(null);
                }}
              >
                Start New Auto-Trade
              </button>
            )}

            {state.status !== 'completed' && state.status !== 'failed' && (
              <button className="cancel-button" onClick={cancelAutoTrade}>
                Cancel
              </button>
            )}
          </div>
        </div>
      )}

      {/* Info Section */}
      {!state && (
        <div className="info-section">
          <h3>How It Works</h3>
          <ol className="steps-list">
            <li>
              <strong>Research Market</strong>
              <p>Analyzes VIX, market trends, and economic calendar</p>
            </li>
            <li>
              <strong>Select Strategy</strong>
              <p>Auto-selects best strategy based on conditions</p>
            </li>
            <li>
              <strong>Wait for Market</strong>
              <p>Automatically waits if market is closed</p>
            </li>
            <li>
              <strong>Execute Trade</strong>
              <p>Places order with optimal parameters</p>
            </li>
            <li>
              <strong>Monitor Position</strong>
              <p>Auto-exits at profit targets or stop loss</p>
            </li>
          </ol>

          <div className="strategies-info">
            <h4>Available Strategies</h4>
            <div className="strategy-grid">
              <div className="strategy-box">
                <span className="strategy-emoji">📊</span>
                <strong>IV Mean Reversion</strong>
                <p>Best when VIX &gt; 20, all-day trading</p>
              </div>
              <div className="strategy-box">
                <span className="strategy-emoji">🦅</span>
                <strong>Iron Condor</strong>
                <p>9:31-9:45am ET, range-bound markets</p>
              </div>
              <div className="strategy-box">
                <span className="strategy-emoji">⚡</span>
                <strong>Momentum Scalping</strong>
                <p>9:31-11:30am ET, strong trends</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
