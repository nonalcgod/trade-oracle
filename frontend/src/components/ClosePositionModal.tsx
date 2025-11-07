/**
 * Close Position Modal for Momentum Scalping
 *
 * Smart close dialog with exit reason tracking.
 * Allows user to select why they're closing: profit, loss, discipline, manual.
 */

import React, { useState } from 'react';

interface ClosePositionModalProps {
  isOpen: boolean;
  position: {
    id: number;
    symbol: string;
    quantity: number;
    entry_price: number;
    current_price: number | null;
    unrealized_pnl: number | null;
  } | null;
  onClose: () => void;
  onConfirm: (positionId: number, exitReason: string) => Promise<void>;
}

export const ClosePositionModal: React.FC<ClosePositionModalProps> = ({
  isOpen,
  position,
  onClose,
  onConfirm,
}) => {
  const [exitReason, setExitReason] = useState<string>('manual');
  const [loading, setLoading] = useState(false);

  if (!isOpen || !position) return null;

  const handleConfirm = async () => {
    setLoading(true);
    try {
      await onConfirm(position.id, exitReason);
      onClose();
    } catch (error) {
      console.error('Close position failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const pnl = position.unrealized_pnl || 0;
  const pnlColor = pnl >= 0 ? 'text-emerald-600' : 'text-rose-600';
  const pnlEmoji = pnl >= 0 ? '📈' : '📉';

  const exitReasons = [
    {
      value: 'profit_target',
      label: '🎯 Profit Target Hit',
      description: 'Position reached profit target',
      color: 'emerald',
    },
    {
      value: 'stop_loss',
      label: '🛑 Stop Loss Hit',
      description: 'Position hit stop loss level',
      color: 'rose',
    },
    {
      value: 'manual',
      label: '✋ Manual Exit',
      description: 'User-initiated close',
      color: 'blue',
    },
    {
      value: 'time_exit',
      label: '⏰ Time Exit (11:30am)',
      description: 'Exit window closed, force close',
      color: 'amber',
    },
    {
      value: 'discipline',
      label: '🚨 Discipline Rule (2-Loss)',
      description: '2 consecutive losses, stop trading',
      color: 'red',
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-2xl border-2 border-black p-8 max-w-2xl w-full mx-4 shadow-lg">
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div>
            <h2 className="text-2xl font-sans font-semibold text-black">
              Close Position
            </h2>
            <p className="text-gray-600 mt-1">
              Select exit reason for tracking and analysis
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Position Summary */}
        <div className="mb-6 p-4 bg-gray-50 rounded-xl border border-gray-200">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-gray-600 uppercase tracking-wide mb-1">Symbol</p>
              <p className="font-mono font-semibold text-lg text-black">{position.symbol}</p>
            </div>
            <div>
              <p className="text-xs text-gray-600 uppercase tracking-wide mb-1">Quantity</p>
              <p className="font-mono font-semibold text-lg text-black">{position.quantity} shares</p>
            </div>
            <div>
              <p className="text-xs text-gray-600 uppercase tracking-wide mb-1">Entry Price</p>
              <p className="font-mono text-base text-gray-700">${position.entry_price.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-600 uppercase tracking-wide mb-1">Current P&L {pnlEmoji}</p>
              <p className={`font-mono font-semibold text-lg ${pnlColor}`}>
                ${pnl.toFixed(2)}
              </p>
            </div>
          </div>
        </div>

        {/* Exit Reason Selection */}
        <div className="mb-6">
          <p className="text-sm font-semibold text-gray-700 mb-3">Select Exit Reason:</p>
          <div className="space-y-2">
            {exitReasons.map((reason) => (
              <button
                key={reason.value}
                onClick={() => setExitReason(reason.value)}
                className={`w-full text-left p-4 rounded-lg border-2 transition ${
                  exitReason === reason.value
                    ? `border-${reason.color}-500 bg-${reason.color}-50`
                    : 'border-gray-200 bg-white hover:bg-gray-50'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-semibold text-black">{reason.label}</p>
                    <p className="text-sm text-gray-600 mt-1">{reason.description}</p>
                  </div>
                  {exitReason === reason.value && (
                    <svg className="w-5 h-5 text-teal-600 mt-1" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Warning Box */}
        {exitReason === 'discipline' && (
          <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 rounded">
            <p className="text-red-700 font-semibold">⚠️ Discipline Rule Triggered</p>
            <p className="text-red-600 text-sm mt-1">
              You've hit 2 consecutive losses. Take a break and review your setups.
              Come back tomorrow with fresh eyes.
            </p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-6 py-3 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg font-semibold transition"
            disabled={loading}
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={loading}
            className={`flex-1 px-6 py-3 rounded-lg font-semibold transition ${
              loading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-rose-500 hover:bg-rose-600 text-white transform hover:scale-105 active:scale-95'
            }`}
          >
            {loading ? 'Closing Position...' : 'Close Position'}
          </button>
        </div>

        {/* Psychology Note */}
        <div className="mt-4 p-3 bg-blue-50 border-l-4 border-blue-400 rounded">
          <p className="text-blue-700 text-sm">
            <strong>🧠 Psychology Note:</strong> Every exit is a learning opportunity.
            Review this trade later - what went right? What could improve?
          </p>
        </div>
      </div>
    </div>
  );
};
