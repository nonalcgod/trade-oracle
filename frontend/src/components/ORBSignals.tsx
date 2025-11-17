/**
 * Opening Range Breakout (ORB) Signals Display Component
 *
 * Real-time display of opening ranges and breakout signals for SPY, QQQ, IWM.
 * Shows 60-minute opening range (9:30-10:30am ET) and breakout opportunities.
 *
 * Win Rate: 75-89% historically
 * Entry Window: 10:30am - 2:00pm ET
 * Exit: Range invalidation, 50% gain, 40% loss, or 3:00pm force close
 */

import React, { useEffect, useState } from 'react';
import { PillBadge } from './ui/PillBadge';
import { StatusDot } from './ui/StatusDot';

interface OpeningRange {
  symbol: string;
  trade_date: string;
  duration_minutes: number;
  range_high: number | null;
  range_low: number | null;
  range_width: number | null; // Percentage
  gap_percent: number | null;
  range_complete: boolean;
  range_start_time: string | null;
  range_end_time: string | null;
}

interface ORBSignal {
  signal_id: string;
  symbol: string;
  direction: 'BULLISH' | 'BEARISH';
  opening_range_id: string;
  range_high: number;
  range_low: number;
  range_width: number;
  breakout_price: number;
  breakout_time: string;
  volume_confirmation: boolean;
  rsi_confirmation: number | null;
  target_price: number;
  stop_loss_price: number;
  confidence: number;
  reasoning: string;
  created_at: string;
}

interface RangeResponse {
  ranges: Record<string, OpeningRange>;
  timestamp: string;
  message: string;
}

interface SignalResponse {
  signals: ORBSignal[];
  timestamp: string;
  entry_window_active: boolean;
  message: string;
}

export const ORBSignals: React.FC = () => {
  const [ranges, setRanges] = useState<Record<string, OpeningRange>>({});
  const [signals, setSignals] = useState<ORBSignal[]>([]);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [loading, setLoading] = useState(false);
  const [entryWindowActive, setEntryWindowActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch opening ranges and signals every 30 seconds
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

        // Fetch ranges
        const rangesResponse = await fetch(`${apiUrl}/api/orb/ranges`);
        if (!rangesResponse.ok) {
          throw new Error(`Ranges API error: ${rangesResponse.status}`);
        }
        const rangesData: RangeResponse = await rangesResponse.json();
        setRanges(rangesData.ranges);

        // Fetch signals
        const signalsResponse = await fetch(`${apiUrl}/api/orb/scan`);
        if (!signalsResponse.ok) {
          throw new Error(`Signals API error: ${signalsResponse.status}`);
        }
        const signalsData: SignalResponse = await signalsResponse.json();
        setSignals(signalsData.signals);
        setEntryWindowActive(signalsData.entry_window_active);

        setLastUpdate(new Date());
        setError(null);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMessage);
        console.error('Error fetching ORB data:', err);
      } finally {
        setLoading(false);
      }
    };

    // Fetch immediately
    fetchData();

    // Set up polling every 30 seconds (faster refresh for ORB)
    const interval = setInterval(fetchData, 30000);

    return () => clearInterval(interval);
  }, []);

  const handleExecuteTrade = async (signal: ORBSignal) => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/orb/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          signal_id: signal.signal_id,
          signal: signal,
          quantity: 1, // TODO: Make this configurable
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Execution error: ${response.status}`);
      }

      const result = await response.json();
      console.log('ORB trade execution result:', result);

      // Show success toast/notification
      alert(`ORB trade executed: ${signal.symbol} ${signal.direction} breakout order placed`);

      // Remove signal from display
      setSignals(signals.filter(s => s.signal_id !== signal.signal_id));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      console.error('ORB trade execution failed:', err);
      alert(`Execution failed: ${errorMessage}`);
    }
  };

  // Calculate time remaining until range completion (10:30am ET)
  const getTimeUntilRangeComplete = () => {
    const now = new Date();
    const nowET = new Date(now.toLocaleString('en-US', { timeZone: 'America/New_York' }));

    // Market open: 9:30am ET
    const marketOpen = new Date(nowET);
    marketOpen.setHours(9, 30, 0, 0);

    // Range complete: 10:30am ET
    const rangeComplete = new Date(nowET);
    rangeComplete.setHours(10, 30, 0, 0);

    if (nowET < marketOpen) {
      return 'Market not open';
    } else if (nowET < rangeComplete) {
      const minutesRemaining = Math.floor((rangeComplete.getTime() - nowET.getTime()) / 60000);
      return `${minutesRemaining} min until range complete`;
    } else {
      return 'Range complete';
    }
  };

  const rangeArray = Object.values(ranges);
  const hasCompleteRanges = rangeArray.some(r => r.range_complete);

  return (
    <section className="bg-white rounded-2xl border-2 border-black p-8 shadow-md">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-sans font-semibold text-black">
            Opening Range Breakout (ORB)
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
            {entryWindowActive ? '10:30am - 2:00pm ET' : 'Outside entry window'}
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-3 bg-red-100 border-l-4 border-red-500 rounded">
          <p className="text-red-700 text-sm">Error: {error}</p>
        </div>
      )}

      {/* Opening Ranges Status */}
      <div className="mb-6 p-4 bg-blue-50 border-l-4 border-blue-400 rounded">
        <div className="flex justify-between items-center mb-2">
          <p className="text-blue-700 font-semibold">
            📊 60-Minute Opening Ranges (9:30-10:30am ET)
          </p>
          <span className="text-blue-600 text-sm font-mono">
            {getTimeUntilRangeComplete()}
          </span>
        </div>

        {rangeArray.length === 0 ? (
          <p className="text-blue-600 text-sm">No ranges tracked yet. Waiting for market open...</p>
        ) : (
          <div className="grid grid-cols-3 gap-4 mt-3">
            {rangeArray.map((range) => (
              <div
                key={range.symbol}
                className={`p-3 rounded-lg border-2 ${
                  range.range_complete
                    ? 'bg-emerald-50 border-emerald-500'
                    : 'bg-gray-50 border-gray-300'
                }`}
              >
                <div className="flex justify-between items-center mb-2">
                  <span className="font-mono font-bold text-black">{range.symbol}</span>
                  {range.range_complete && (
                    <span className="text-xs text-emerald-600 font-semibold">✓ COMPLETE</span>
                  )}
                </div>
                {range.range_high && range.range_low ? (
                  <>
                    <div className="text-sm font-mono">
                      <span className="text-gray-600">High:</span>{' '}
                      <span className="text-black font-semibold">${range.range_high.toFixed(2)}</span>
                    </div>
                    <div className="text-sm font-mono">
                      <span className="text-gray-600">Low:</span>{' '}
                      <span className="text-black font-semibold">${range.range_low.toFixed(2)}</span>
                    </div>
                    {range.range_width && (
                      <div className="text-sm font-mono mt-1">
                        <span className="text-teal-600 font-semibold">
                          {range.range_width.toFixed(2)}% width
                        </span>
                      </div>
                    )}
                  </>
                ) : (
                  <p className="text-sm text-gray-500 italic">Building range...</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Breakout Signals */}
      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-3">Breakout Signals</h3>
        {!hasCompleteRanges ? (
          <div className="text-center py-8">
            <div className="text-gray-400 mb-2">⏰</div>
            <p className="text-gray-600 font-medium">
              Waiting for opening ranges to complete at 10:30am ET...
            </p>
            <p className="text-sm text-gray-500 mt-2">
              {getTimeUntilRangeComplete()}
            </p>
          </div>
        ) : signals.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-gray-400 mb-2">📈</div>
            <p className="text-gray-600 font-medium">
              {entryWindowActive
                ? 'No breakouts detected yet. Watching for price to break above/below range...'
                : 'Entry window closed (2:00pm). No breakout opportunities available.'}
            </p>
            {loading && <p className="text-sm text-gray-500 mt-2">Loading...</p>}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b-2 border-black">
                  <th className="text-left p-3 font-semibold">Symbol</th>
                  <th className="text-left p-3 font-semibold">Direction</th>
                  <th className="text-left p-3 font-semibold">Breakout Price</th>
                  <th className="text-left p-3 font-semibold">Target</th>
                  <th className="text-left p-3 font-semibold">Stop Loss</th>
                  <th className="text-left p-3 font-semibold">Confidence</th>
                  <th className="text-left p-3 font-semibold">Confirmation</th>
                  <th className="text-center p-3 font-semibold">Action</th>
                </tr>
              </thead>
              <tbody>
                {signals.map((signal) => (
                  <tr
                    key={signal.signal_id}
                    className="border-b border-gray-200 hover:bg-gray-50 transition"
                  >
                    {/* Symbol */}
                    <td className="p-3 font-mono font-semibold text-black">
                      {signal.symbol}
                    </td>

                    {/* Direction */}
                    <td className="p-3">
                      <PillBadge
                        variant={signal.direction === 'BULLISH' ? 'emerald' : 'rose'}
                      >
                        {signal.direction === 'BULLISH' ? '🟢 BULLISH' : '🔴 BEARISH'}
                      </PillBadge>
                    </td>

                    {/* Breakout Price */}
                    <td className="p-3 font-mono text-sm">
                      ${signal.breakout_price.toFixed(2)}
                    </td>

                    {/* Target Price */}
                    <td className="p-3 font-mono text-sm">
                      <span className="text-emerald-600 font-semibold">
                        ${signal.target_price.toFixed(2)}
                      </span>
                    </td>

                    {/* Stop Loss */}
                    <td className="p-3 font-mono text-sm">
                      <span className="text-rose-600 font-semibold">
                        ${signal.stop_loss_price.toFixed(2)}
                      </span>
                    </td>

                    {/* Confidence */}
                    <td className="p-3 font-mono">
                      <span className="text-emerald-600 font-semibold">
                        {(signal.confidence * 100).toFixed(0)}%
                      </span>
                    </td>

                    {/* Confirmation */}
                    <td className="p-3">
                      <div className="flex flex-col gap-1 text-xs">
                        <span
                          className={`${
                            signal.volume_confirmation
                              ? 'text-emerald-600'
                              : 'text-gray-400'
                          }`}
                        >
                          {signal.volume_confirmation ? '✓' : '○'} Volume
                        </span>
                        <span
                          className={`${
                            signal.rsi_confirmation
                              ? 'text-emerald-600'
                              : 'text-gray-400'
                          }`}
                        >
                          {signal.rsi_confirmation ? '✓' : '○'} RSI{' '}
                          {signal.rsi_confirmation
                            ? `(${signal.rsi_confirmation.toFixed(0)})`
                            : ''}
                        </span>
                      </div>
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
      </div>

      {/* Signal Details (if signal exists) */}
      {signals.length > 0 && (
        <div className="mt-6 pt-6 border-t-2 border-gray-200">
          <h3 className="text-lg font-semibold mb-4">ORB Strategy Details</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-blue-50 border-l-4 border-blue-400 rounded">
              <p className="text-blue-700 font-semibold mb-2">📊 Entry Criteria</p>
              <ul className="text-blue-600 text-sm space-y-1">
                <li>✓ Opening range complete (10:30am)</li>
                <li>✓ Price breaks above/below range</li>
                <li>✓ Volume confirmation (≥1.5x avg)</li>
                <li>✓ RSI confirmation (&gt;50 or &lt;50)</li>
              </ul>
            </div>

            <div className="p-4 bg-emerald-50 border-l-4 border-emerald-500 rounded">
              <p className="text-emerald-700 font-semibold mb-2">🎯 Exit Rules</p>
              <ul className="text-emerald-600 text-sm space-y-1">
                <li>• Target: Range width × 1.5 OR 50% gain</li>
                <li>• Stop: Range re-entry OR 40% loss</li>
                <li>• Time: Force close at 3:00pm ET</li>
                <li>• Win Rate: 75-89% historically</li>
              </ul>
            </div>
          </div>

          {signals[0] && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <p className="text-gray-700 font-semibold mb-2">Signal Reasoning:</p>
              <p className="text-gray-600 text-sm">{signals[0].reasoning}</p>
            </div>
          )}
        </div>
      )}
    </section>
  );
};
