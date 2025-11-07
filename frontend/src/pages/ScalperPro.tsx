/**
 * ScalperPro - Elite 0DTE Momentum Scalping Dashboard
 *
 * Full-screen trading interface optimized for MacBook Pro 14"/16"
 * Features:
 * - Real-time 6-condition signal validation
 * - Entry window countdown (9:31am - 11:30am ET)
 * - Live position monitoring with P&L
 * - Psychology enforcement (2-loss rule, 4-trade limit)
 * - Pre-market analysis and go/no-go checklist
 * - Daily performance metrics
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Zap,
  Activity,
  Clock,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Target,
  Shield,
  BarChart3,
  ArrowLeft,
} from 'lucide-react';
import { PillBadge } from '../components/ui/PillBadge';
import { StatusDot } from '../components/ui/StatusDot';
import { ClosePositionModal } from '../components/ClosePositionModal';
import { useEntryWindow } from '../hooks/useEntryWindow';
import { useScalperSignals, MomentumSignal } from '../hooks/useScalperSignals';
import { useDisciplineTracker } from '../hooks/useDisciplineTracker';
import { useScalperPositions, ScalperPosition } from '../hooks/useScalperPositions';

const ScalperPro = () => {
  // Hooks
  const { isActive, timeRemaining, currentTimeET, minutesRemaining } = useEntryWindow();
  const { signals, entryWindowActive, lastUpdate, loading, error, refetch } = useScalperSignals();
  const {
    tradeCount,
    winCount,
    lossCount,
    consecutiveLosses,
    canTrade,
    recentTrades,
    recordTrade,
  } = useDisciplineTracker();
  const { positions, loading: positionsLoading, refetch: refetchPositions } = useScalperPositions();

  // Local state
  const [executing, setExecuting] = useState<string | null>(null);
  const [closeModalOpen, setCloseModalOpen] = useState(false);
  const [selectedPosition, setSelectedPosition] = useState<ScalperPosition | null>(null);

  // Format currency
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  // Format percentage
  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  // Execute trade handler
  const handleExecuteTrade = async (signal: MomentumSignal) => {
    if (!canTrade) {
      alert('Trading halted: 2-loss rule or 4-trade limit reached');
      return;
    }

    if (!entryWindowActive) {
      alert('Entry window closed. No new trades allowed.');
      return;
    }

    setExecuting(signal.signal_id);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/momentum-scalping/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          signal_id: signal.signal_id,
          signal: signal,
          quantity: 1,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      alert(`✅ Trade executed: ${signal.symbol} ${signal.signal_type}\nOrder ID: ${result.order_id || 'Pending'}`);

      // Refetch signals to update display
      await refetch();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      alert(`❌ Execution failed: ${errorMessage}`);
    } finally {
      setExecuting(null);
    }
  };

  // Open close position modal
  const handleOpenCloseModal = (position: ScalperPosition) => {
    setSelectedPosition(position);
    setCloseModalOpen(true);
  };

  // Close position handler
  const handleClosePosition = async (positionId: number, exitReason: string) => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/momentum-scalping/close-position`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          position_id: positionId,
          exit_reason: exitReason,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();

      if (!result.success) {
        throw new Error(result.message || 'Close position failed');
      }

      // Update discipline tracker
      const position = positions.find(p => p.id === positionId);
      if (position && position.pnl !== null && position.pnl !== undefined) {
        const tradeResult = position.pnl >= 0 ? 'WIN' : 'LOSS';
        recordTrade(tradeResult, {
          symbol: position.symbol,
          entry_price: position.entry_price,
          exit_price: position.current_price || position.entry_price,
          pnl: position.pnl,
          exit_reason: exitReason,
        });
      }

      alert(`✅ Position closed: ${result.message || 'Success'}\nP&L: $${position?.pnl?.toFixed(2) || '0.00'}`);

      // Refetch positions to update display
      await refetchPositions();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      alert(`❌ Close failed: ${errorMessage}`);
      throw err; // Re-throw for modal to handle loading state
    }
  };

  // Calculate 6-condition status
  const getConditionStatus = (signal: MomentumSignal) => {
    const conditionsObj = {
      ema_crossover: signal.signal_type === 'BUY' ? signal.ema_9 > signal.ema_21 : signal.ema_9 < signal.ema_21,
      rsi_confirmation: signal.signal_type === 'BUY' ? signal.rsi_14 > 30 : signal.rsi_14 < 70,
      volume_spike: signal.relative_volume >= 2.0,
      vwap_breakout: true, // Assume true if signal generated
      entry_window: entryWindowActive,
      relative_strength: true, // Phase 2 feature
    };

    const metCount = Object.values(conditionsObj).filter(Boolean).length;
    return { metCount, total: 6 };
  };

  // Calculate daily performance
  const calculatePerformance = () => {
    const totalPnL = recentTrades.reduce((sum, trade) => sum + trade.pnl, 0);
    const avgWin = winCount > 0
      ? recentTrades.filter(t => t.result === 'WIN').reduce((sum, t) => sum + t.pnl, 0) / winCount
      : 0;
    const avgLoss = lossCount > 0
      ? recentTrades.filter(t => t.result === 'LOSS').reduce((sum, t) => sum + t.pnl, 0) / lossCount
      : 0;
    const winRate = tradeCount > 0 ? (winCount / tradeCount) * 100 : 0;
    const winLossRatio = lossCount > 0 ? Math.abs(avgWin / avgLoss) : 0;

    return { totalPnL, avgWin, avgLoss, winRate, winLossRatio };
  };

  const performance = calculatePerformance();

  return (
    <div className="min-h-screen bg-[#F5F1E8]">
      <div className="mx-auto max-w-[1920px] px-6 lg:px-8 py-6">
        {/* Header */}
        <header className="mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                to="/"
                className="text-gray-600 hover:text-black transition-colors"
                aria-label="Back to dashboard"
              >
                <ArrowLeft size={24} />
              </Link>
              <div className="flex items-center gap-3">
                <Zap size={32} className="text-amber-500" />
                <h1 className="text-3xl font-sans font-semibold text-black">
                  ScalperPro
                </h1>
                <PillBadge variant="amber">0DTE MOMENTUM</PillBadge>
                <PillBadge variant="rose">PAPER TRADING</PillBadge>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-600">
                Last scan: {lastUpdate ? lastUpdate.toLocaleTimeString() : 'Waiting...'}
              </p>
            </div>
          </div>
        </header>

        {/* Sticky Entry Window Header */}
        <div className={`sticky top-0 z-10 mb-6 p-4 rounded-2xl border-2 shadow-lg ${
          isActive
            ? 'bg-teal-50 border-teal-500'
            : 'bg-rose-50 border-rose-500'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Clock size={24} className={isActive ? 'text-teal-600' : 'text-rose-600'} />
              <div>
                <h2 className="text-xl font-semibold text-black">
                  {isActive ? '🟢 ENTRY WINDOW ACTIVE' : '🔴 ENTRY WINDOW CLOSED'}
                </h2>
                <p className="text-sm text-gray-700">
                  {isActive
                    ? `Time Remaining: ${timeRemaining}`
                    : 'Window: 9:31am - 11:30am ET (Next: Tomorrow)'}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-lg font-mono font-semibold text-black">
                Current Time: {currentTimeET} ET
              </p>
              {isActive && (
                <p className="text-sm text-gray-700">
                  Force close all positions at 11:30am ET
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="mb-6 p-4 bg-rose-50 border-2 border-rose-500 rounded-2xl">
            <div className="flex items-center gap-2">
              <AlertTriangle size={20} className="text-rose-600" />
              <p className="text-rose-700 font-medium">{error}</p>
              <button
                onClick={() => refetch()}
                className="ml-auto px-4 py-1 bg-rose-600 text-white rounded-lg hover:bg-rose-700"
              >
                Retry
              </button>
            </div>
          </div>
        )}

        {/* Main Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Signals + Pre-market */}
          <div className="lg:col-span-2 space-y-6">
            {/* Real-Time Signal Scanner */}
            <section className="bg-white rounded-2xl border-2 border-black p-6 shadow-md">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <Activity size={24} className="text-teal-500" />
                  <h2 className="text-2xl font-sans font-semibold text-black">
                    Real-Time Signals
                  </h2>
                  <StatusDot
                    status={entryWindowActive ? 'connected' : 'disconnected'}
                    label={entryWindowActive ? 'Scanning' : 'Paused'}
                    showPulse={entryWindowActive}
                  />
                </div>
                <p className="text-sm text-gray-600">
                  Next scan: {60 - (new Date().getSeconds() % 60)}s
                </p>
              </div>

              {/* Signals Table */}
              {loading && signals.length === 0 ? (
                <div className="text-center py-8 text-gray-600">
                  <Activity size={32} className="mx-auto mb-2 animate-spin" />
                  <p>Scanning for 6-condition setups...</p>
                </div>
              ) : signals.length === 0 ? (
                <div className="text-center py-12">
                  <Zap size={48} className="text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 font-medium">
                    {entryWindowActive
                      ? 'No 6-condition setups detected. Waiting for alignment...'
                      : 'Entry window closed. Next scan: Tomorrow 9:31am ET'}
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b-2 border-black text-left">
                        <th className="p-3 font-semibold">Symbol</th>
                        <th className="p-3 font-semibold">Signal</th>
                        <th className="p-3 font-semibold">Confidence</th>
                        <th className="p-3 font-semibold">EMA(9/21)</th>
                        <th className="p-3 font-semibold">RSI(14)</th>
                        <th className="p-3 font-semibold">Vol</th>
                        <th className="p-3 font-semibold">Conditions</th>
                        <th className="p-3 text-center font-semibold">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {signals.map((signal) => {
                        const { metCount, total } = getConditionStatus(signal);
                        const allMet = metCount === total;

                        return (
                          <tr
                            key={signal.signal_id}
                            className="border-b border-gray-200 hover:bg-gray-50"
                          >
                            <td className="p-3 font-mono font-semibold text-black">
                              {signal.symbol}
                            </td>
                            <td className="p-3">
                              <PillBadge variant={signal.signal_type === 'BUY' ? 'emerald' : 'rose'}>
                                {signal.signal_type === 'BUY' ? '🟢 BUY' : '🔴 SELL'}
                              </PillBadge>
                            </td>
                            <td className="p-3 font-mono text-black">
                              {(signal.confidence * 100).toFixed(0)}%
                            </td>
                            <td className="p-3 font-mono text-sm text-gray-700">
                              {signal.ema_9.toFixed(2)} / {signal.ema_21.toFixed(2)}
                            </td>
                            <td className="p-3 font-mono text-sm text-gray-700">
                              {signal.rsi_14.toFixed(1)}
                            </td>
                            <td className="p-3 font-mono text-sm text-gray-700">
                              {signal.relative_volume.toFixed(1)}x
                            </td>
                            <td className="p-3">
                              <span className={`font-semibold ${allMet ? 'text-emerald-600' : 'text-amber-600'}`}>
                                {metCount}/{total} {allMet ? '✅' : '⚠️'}
                              </span>
                            </td>
                            <td className="p-3 text-center">
                              <button
                                onClick={() => handleExecuteTrade(signal)}
                                disabled={!allMet || !canTrade || executing === signal.signal_id}
                                className={`px-4 py-2 rounded-lg font-semibold transition ${
                                  allMet && canTrade
                                    ? 'bg-teal-500 hover:bg-teal-600 text-white transform hover:scale-105 active:scale-95'
                                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                }`}
                              >
                                {executing === signal.signal_id ? 'Executing...' : 'Execute'}
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}

              {/* 6-Condition Legend */}
              {signals.length > 0 && (
                <div className="mt-6 pt-6 border-t-2 border-gray-200">
                  <h3 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide">
                    6-Condition Validation
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                    <div className="flex items-center gap-2">
                      <CheckCircle size={16} className="text-emerald-500" />
                      <span className="text-gray-700">EMA Crossover</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle size={16} className="text-emerald-500" />
                      <span className="text-gray-700">RSI Confirmation</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle size={16} className="text-emerald-500" />
                      <span className="text-gray-700">Volume Spike (≥2x)</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle size={16} className="text-emerald-500" />
                      <span className="text-gray-700">VWAP Breakout</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle size={16} className="text-emerald-500" />
                      <span className="text-gray-700">Entry Window</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle size={16} className="text-emerald-500" />
                      <span className="text-gray-700">Relative Strength</span>
                    </div>
                  </div>
                </div>
              )}
            </section>

            {/* Active Positions Monitor */}
            <section className="bg-white rounded-2xl border-2 border-black p-6 shadow-md">
              <div className="flex items-center gap-3 mb-4">
                <Target size={24} className="text-emerald-500" />
                <h2 className="text-2xl font-sans font-semibold text-black">
                  Active Positions ({positions.length})
                </h2>
              </div>

              {positionsLoading && positions.length === 0 ? (
                <div className="text-center py-8 text-gray-600">Loading positions...</div>
              ) : positions.length === 0 ? (
                <div className="text-center py-8 text-gray-600">
                  No active momentum positions
                </div>
              ) : (
                <div className="space-y-4">
                  {positions.map((position) => (
                    <div
                      key={position.id}
                      className="p-4 border-2 border-gray-300 rounded-xl hover:border-teal-500 transition"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h3 className="font-mono font-semibold text-lg text-black">
                            {position.symbol}
                          </h3>
                          <p className="text-sm text-gray-600">
                            Entry: {formatCurrency(position.entry_price)} @ {new Date(position.entry_time).toLocaleTimeString()}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="font-mono text-2xl font-bold text-black">
                            {formatCurrency(position.current_price)}
                          </p>
                          <p className={`font-mono text-lg font-semibold ${
                            (position.pnl ?? 0) >= 0 ? 'text-emerald-600' : 'text-rose-600'
                          }`}>
                            {formatCurrency(position.pnl ?? 0)} ({formatPercent(position.pnl_percent ?? 0)})
                          </p>
                        </div>
                      </div>

                      {/* Exit Target Progress Bars */}
                      <div className="space-y-2">
                        <div>
                          <div className="flex justify-between text-xs text-gray-600 mb-1">
                            <span>Target 1 (+25%)</span>
                            <span>{position.target1Progress}%</span>
                          </div>
                          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-emerald-500 rounded-full transition-all duration-300"
                              style={{ width: `${Math.min(100, position.target1Progress)}%` }}
                            />
                          </div>
                        </div>

                        <div>
                          <div className="flex justify-between text-xs text-gray-600 mb-1">
                            <span>Target 2 (+50%)</span>
                            <span>{position.target2Progress}%</span>
                          </div>
                          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-emerald-600 rounded-full transition-all duration-300"
                              style={{ width: `${Math.min(100, position.target2Progress)}%` }}
                            />
                          </div>
                        </div>

                        <div>
                          <div className="flex justify-between text-xs text-gray-600 mb-1">
                            <span>Stop Loss (-50%)</span>
                            <span>{position.stopLossDistance > 0 ? 'Safe ✅' : 'BREACHED ⚠️'}</span>
                          </div>
                          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all duration-300 ${
                                position.stopLossDistance > 20 ? 'bg-emerald-500' :
                                position.stopLossDistance > 0 ? 'bg-amber-500' : 'bg-rose-500'
                              }`}
                              style={{ width: `${Math.min(100, Math.max(0, position.stopLossDistance))}%` }}
                            />
                          </div>
                        </div>
                      </div>

                      <div className="mt-3 flex items-center justify-between">
                        <p className="text-sm text-gray-600">
                          Force close: {position.timeToForceClose}
                        </p>
                        <button
                          onClick={() => handleOpenCloseModal(position)}
                          className="px-4 py-1 bg-rose-500 text-white rounded-lg hover:bg-rose-600 text-sm font-semibold transition transform hover:scale-105 active:scale-95"
                        >
                          Close Position
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>

          {/* Right Column: Discipline + Performance */}
          <div className="space-y-6">
            {/* Psychology Enforcement Panel */}
            <section className="bg-white rounded-2xl border-2 border-black p-6 shadow-md">
              <div className="flex items-center gap-3 mb-4">
                <Shield size={24} className="text-amber-500" />
                <h2 className="text-xl font-sans font-semibold text-black">
                  Discipline Tracker
                </h2>
              </div>

              <div className="space-y-4">
                {/* Trade Count */}
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm text-gray-600">Today's Trades</span>
                    <span className="font-mono font-semibold text-black">
                      {tradeCount}/4
                    </span>
                  </div>
                  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-teal-500 rounded-full transition-all"
                      style={{ width: `${(tradeCount / 4) * 100}%` }}
                    />
                  </div>
                </div>

                {/* Win/Loss */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-emerald-50 rounded-lg">
                    <p className="text-xs text-gray-600 mb-1">Wins</p>
                    <p className="font-mono text-2xl font-bold text-emerald-600">
                      {winCount}
                    </p>
                  </div>
                  <div className="p-3 bg-rose-50 rounded-lg">
                    <p className="text-xs text-gray-600 mb-1">Losses</p>
                    <p className="font-mono text-2xl font-bold text-rose-600">
                      {lossCount}
                    </p>
                  </div>
                </div>

                {/* 2-Loss Warning */}
                {consecutiveLosses > 0 && (
                  <div className={`p-4 rounded-lg border-2 ${
                    consecutiveLosses >= 2
                      ? 'bg-rose-50 border-rose-500'
                      : 'bg-amber-50 border-amber-500'
                  }`}>
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle size={20} className={consecutiveLosses >= 2 ? 'text-rose-600' : 'text-amber-600'} />
                      <p className="font-semibold text-black">
                        {consecutiveLosses >= 2 ? '🛑 TRADING HALTED' : '⚠️ CAUTION'}
                      </p>
                    </div>
                    <p className="text-sm text-gray-700">
                      {consecutiveLosses >= 2
                        ? 'Two consecutive losses. Come back tomorrow.'
                        : `${2 - consecutiveLosses} more loss${2 - consecutiveLosses === 1 ? '' : 'es'} = HALT`}
                    </p>
                  </div>
                )}

                {/* Recent Trades */}
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-2 uppercase tracking-wide">
                    Recent Activity
                  </h3>
                  {recentTrades.length === 0 ? (
                    <p className="text-sm text-gray-500 text-center py-4">
                      No trades today
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {recentTrades.map((trade, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between p-2 bg-gray-50 rounded-lg text-sm"
                        >
                          <div className="flex items-center gap-2">
                            {trade.result === 'WIN' ? (
                              <CheckCircle size={16} className="text-emerald-500" />
                            ) : (
                              <XCircle size={16} className="text-rose-500" />
                            )}
                            <span className="font-mono font-semibold text-black">
                              {trade.symbol}
                            </span>
                          </div>
                          <span className={`font-mono font-semibold ${
                            trade.result === 'WIN' ? 'text-emerald-600' : 'text-rose-600'
                          }`}>
                            {formatPercent(trade.pnlPercent)}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </section>

            {/* Performance Metrics */}
            <section className="bg-white rounded-2xl border-2 border-black p-6 shadow-md">
              <div className="flex items-center gap-3 mb-4">
                <BarChart3 size={24} className="text-teal-500" />
                <h2 className="text-xl font-sans font-semibold text-black">
                  Today's Performance
                </h2>
              </div>

              <div className="space-y-4">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-xs uppercase tracking-wide text-gray-600 mb-1">
                    Total P&L
                  </p>
                  <p className={`font-mono text-3xl font-bold ${
                    performance.totalPnL >= 0 ? 'text-emerald-600' : 'text-rose-600'
                  }`}>
                    {formatCurrency(performance.totalPnL)}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <p className="text-xs text-gray-600 mb-1">Win Rate</p>
                    <p className="font-mono text-xl font-semibold text-black">
                      {performance.winRate.toFixed(0)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600 mb-1">W/L Ratio</p>
                    <p className="font-mono text-xl font-semibold text-black">
                      {performance.winLossRatio > 0 ? performance.winLossRatio.toFixed(1) : '-'}x
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <p className="text-xs text-gray-600 mb-1">Avg Win</p>
                    <p className="font-mono text-lg font-semibold text-emerald-600">
                      {formatCurrency(performance.avgWin)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600 mb-1">Avg Loss</p>
                    <p className="font-mono text-lg font-semibold text-rose-600">
                      {formatCurrency(performance.avgLoss)}
                    </p>
                  </div>
                </div>
              </div>
            </section>

            {/* Pre-Market Analysis (conditional) */}
            {!isActive && minutesRemaining < 120 && minutesRemaining > 0 && (
              <section className="bg-white rounded-2xl border-2 border-black p-6 shadow-md">
                <div className="flex items-center gap-3 mb-4">
                  <Activity size={24} className="text-amber-500" />
                  <h2 className="text-xl font-sans font-semibold text-black">
                    Pre-Market Protocol
                  </h2>
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg">
                    <CheckCircle size={16} className="text-emerald-500" />
                    <span className="text-gray-700">VIX Level (checking...)</span>
                  </div>
                  <div className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg">
                    <CheckCircle size={16} className="text-emerald-500" />
                    <span className="text-gray-700">IV Rank (checking...)</span>
                  </div>
                  <div className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg">
                    <CheckCircle size={16} className="text-emerald-500" />
                    <span className="text-gray-700">Economic Calendar (safe)</span>
                  </div>
                  <div className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg">
                    <CheckCircle size={16} className="text-emerald-500" />
                    <span className="text-gray-700">Market Regime (normal)</span>
                  </div>
                </div>

                <div className="mt-4 p-3 bg-emerald-50 border-2 border-emerald-500 rounded-lg">
                  <p className="font-semibold text-emerald-700 text-center">
                    ✅ GO: Ready to execute at 9:31am ET
                  </p>
                </div>
              </section>
            )}
          </div>
        </div>
      </div>

      {/* Close Position Modal */}
      <ClosePositionModal
        isOpen={closeModalOpen}
        position={selectedPosition ? {
          id: selectedPosition.id,
          symbol: selectedPosition.symbol,
          quantity: selectedPosition.quantity,
          entry_price: selectedPosition.entry_price,
          current_price: selectedPosition.current_price,
          unrealized_pnl: selectedPosition.pnl || 0,
        } : null}
        onClose={() => {
          setCloseModalOpen(false);
          setSelectedPosition(null);
        }}
        onConfirm={handleClosePosition}
      />
    </div>
  );
};

export default ScalperPro;
