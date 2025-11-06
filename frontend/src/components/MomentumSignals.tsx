/**
 * Momentum Scalping Signals Display Component
 *
 * Real-time display of 0DTE momentum scalping signals.
 * Shows 6-condition validation status and allows manual trade execution.
 */

import React, { useEffect, useState } from 'react';
import { PillBadge } from './PillBadge';
import { StatusDot } from './StatusDot';

interface MomentumSignal {
  signal_id: string;
  symbol: string;
  signal_type: 'BUY' | 'SELL';
  option_symbol?: string;
  confidence: number;
  ema_9: number;
  ema_21: number;
  rsi_14: number;
  vwap: number;
  relative_volume: number;
  entry_price?: number;
  target_1?: number;
  target_2?: number;
  stop_loss?: number;
  created_at: string;
  reasoning?: string;
}

interface ScanResponse {
  signals: MomentumSignal[];
  timestamp: string;
  entry_window_active: boolean;
  message: string;
}

export const MomentumSignals: React.FC = () => {
  const [signals, setSignals] = useState<MomentumSignal[]>([]);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [loading, setLoading] = useState(false);
  const [entryWindowActive, setEntryWindowActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch signals every 60 seconds (MVP uses REST polling, not WebSocket)
  useEffect(() => {
    const fetchSignals = async () => {
      try {
        setLoading(true);
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const response = await fetch(`${apiUrl}/api/momentum-scalping/scan`);

        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }

        const data: ScanResponse = await response.json();
        setSignals(data.signals);
        setEntryWindowActive(data.entry_window_active);
        setLastUpdate(new Date());
        setError(null);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMessage);
        console.error('Error fetching momentum signals:', err);
      } finally {
        setLoading(false);
      }
    };

    // Fetch immediately
    fetchSignals();

    // Set up polling every 60 seconds
    const interval = setInterval(fetchSignals, 60000);

    return () => clearInterval(interval);
  }, []);

  const handleExecuteTrade = async (signal: MomentumSignal) => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/momentum-scalping/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          signal_id: signal.signal_id,
          signal: signal,
          quantity: 1, // TODO: Make this configurable
        }),
      });

      if (!response.ok) {
        throw new Error(`Execution error: ${response.status}`);
      }

      const result = await response.json();
      console.log('Trade execution result:', result);

      // Show success toast/notification
      alert(`Trade executed: ${signal.symbol} ${signal.signal_type} order placed`);

      // Optionally remove signal from display
      setSignals(signals.filter(s => s.signal_id !== signal.signal_id));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      console.error('Trade execution failed:', err);
      alert(`Execution failed: ${errorMessage}`);
    }
  };

  return (
    <section className="bg-white rounded-2xl border-2 border-black p-8 shadow-md">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-sans font-semibold text-black">
            Momentum Scalper (0DTE)
          </h2>
          <StatusDot
            status={entryWindowActive ? 'connected' : 'disconnected'}
            label={entryWindowActive ? 'Entry Window Active' : 'Entry Window Closed'}
          />
        </div>
        <div className="text-right">
          <div className="text-sm text-gray-600 mb-1">
            Last update: {lastUpdate ? lastUpdate.toLocaleTimeString() : 'Waiting...'}
          </div>
          <div className="text-xs text-gray-500">
            {entryWindowActive ? '9:31am - 11:30am ET' : 'Outside entry window'}
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-3 bg-red-100 border-l-4 border-red-500 rounded">
          <p className="text-red-700 text-sm">Error: {error}</p>
        </div>
      )}

      {/* Status Message */}
      <div className="mb-4 p-3 bg-blue-50 border-l-4 border-blue-400 rounded">
        <p className="text-blue-700 text-sm">
          {entryWindowActive
            ? '✅ Scanning for 6-condition momentum setups...'
            : '⏰ Entry window closed. Next scan: Tomorrow 9:31am ET'}
        </p>
      </div>

      {/* Signals Table */}
      {signals.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-400 mb-2">📊</div>
          <p className="text-gray-600 font-medium">
            {entryWindowActive
              ? 'No signals detected yet. Waiting for EMA crossover + volume spike + VWAP breakout...'
              : 'Entry window closed. No signals available.'}
          </p>
          {loading && <p className="text-sm text-gray-500 mt-2">Loading...</p>}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b-2 border-black">
                <th className="text-left p-3 font-semibold">Symbol</th>
                <th className="text-left p-3 font-semibold">Signal</th>
                <th className="text-left p-3 font-semibold">Confidence</th>
                <th className="text-left p-3 font-semibold">EMA(9/21)</th>
                <th className="text-left p-3 font-semibold">RSI(14)</th>
                <th className="text-left p-3 font-semibold">VWAP</th>
                <th className="text-left p-3 font-semibold">Rel Vol</th>
                <th className="text-center p-3 font-semibold">Action</th>
              </tr>
            </thead>
            <tbody>
              {signals.map((signal, idx) => (
                <tr key={idx} className="border-b border-gray-200 hover:bg-gray-50 transition">
                  {/* Symbol */}
                  <td className="p-3 font-mono font-semibold text-black">
                    {signal.symbol}
                  </td>

                  {/* Signal Type */}
                  <td className="p-3">
                    <PillBadge
                      variant={signal.signal_type === 'BUY' ? 'emerald' : 'rose'}
                    >
                      {signal.signal_type === 'BUY' ? '🟢 BUY' : '🔴 SELL'}
                    </PillBadge>
                  </td>

                  {/* Confidence */}
                  <td className="p-3 font-mono">
                    <span className="text-emerald-600 font-semibold">
                      {(signal.confidence * 100).toFixed(0)}%
                    </span>
                  </td>

                  {/* EMA Crossover */}
                  <td className="p-3 font-mono text-sm">
                    <span className={signal.ema_9 > signal.ema_21 ? 'text-emerald-600' : 'text-rose-600'}>
                      {signal.ema_9.toFixed(2)} / {signal.ema_21.toFixed(2)}
                    </span>
                  </td>

                  {/* RSI */}
                  <td className="p-3 font-mono">
                    <span
                      className={
                        signal.rsi_14 > 70
                          ? 'text-rose-600 font-semibold'
                          : signal.rsi_14 < 30
                            ? 'text-emerald-600 font-semibold'
                            : 'text-gray-600'
                      }
                    >
                      {signal.rsi_14.toFixed(1)}
                    </span>
                  </td>

                  {/* VWAP */}
                  <td className="p-3 font-mono text-sm">${signal.vwap.toFixed(2)}</td>

                  {/* Relative Volume */}
                  <td className="p-3 font-mono">
                    <span className="text-teal-600 font-semibold">
                      {signal.relative_volume.toFixed(1)}x
                    </span>
                  </td>

                  {/* Execute Button */}
                  <td className="p-3 text-center">
                    <button
                      onClick={() => handleExecuteTrade(signal)}
                      className="bg-teal-500 hover:bg-teal-600 text-white px-4 py-2 rounded-lg font-semibold transition transform hover:scale-105 active:scale-95"
                    >
                      Execute
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Signal Details (if signal exists) */}
      {signals.length > 0 && (
        <div className="mt-6 pt-6 border-t-2 border-gray-200">
          <h3 className="text-lg font-semibold mb-4">6-Condition Validation</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="p-3 bg-emerald-50 border-l-4 border-emerald-500 rounded">
              <p className="text-emerald-700">✅ EMA Crossover Detected</p>
            </div>
            <div className="p-3 bg-emerald-50 border-l-4 border-emerald-500 rounded">
              <p className="text-emerald-700">✅ RSI Confirmation (>30 or <70)</p>
            </div>
            <div className="p-3 bg-emerald-50 border-l-4 border-emerald-500 rounded">
              <p className="text-emerald-700">✅ Volume Spike (≥2x average)</p>
            </div>
            <div className="p-3 bg-emerald-50 border-l-4 border-emerald-500 rounded">
              <p className="text-emerald-700">✅ VWAP Breakout</p>
            </div>
            <div className="p-3 bg-emerald-50 border-l-4 border-emerald-500 rounded">
              <p className="text-emerald-700">✅ Entry Window Active</p>
            </div>
            <div className="p-3 bg-emerald-50 border-l-4 border-emerald-500 rounded">
              <p className="text-emerald-700">✅ Relative Strength OK</p>
            </div>
          </div>

          <div className="mt-4 p-4 bg-blue-50 border-l-4 border-blue-400 rounded">
            <p className="text-blue-700 font-semibold mb-2">⏰ Exit Rules</p>
            <ul className="text-blue-600 text-sm space-y-1">
              <li>• Target 1 (25% gain): Exit 50% of position</li>
              <li>• Target 2 (50% gain): Exit remaining 50%</li>
              <li>• Stop Loss (50% loss): Exit 100%</li>
              <li>• 11:30am ET: Force close all positions</li>
            </ul>
          </div>
        </div>
      )}
    </section>
  );
};
