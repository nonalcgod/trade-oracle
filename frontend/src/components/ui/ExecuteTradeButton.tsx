import React, { useState } from 'react';
import { apiService } from '../../api';

interface ExecuteTradeButtonProps {
  strategy: 'iv-mean-reversion' | 'iron-condor';
  disabled?: boolean;
  onExecute?: () => void;
}

export const ExecuteTradeButton: React.FC<ExecuteTradeButtonProps> = ({
  strategy,
  disabled = false,
  onExecute,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [quantity, setQuantity] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleOpenModal = () => {
    setIsOpen(true);
    setError(null);
    setSuccess(null);
  };

  const handleCloseModal = () => {
    setIsOpen(false);
    setError(null);
    setSuccess(null);
  };

  const handleExecute = async () => {
    // Native confirm dialog as per user preference
    const confirmed = confirm(
      `Execute ${strategy === 'iv-mean-reversion' ? 'IV Mean Reversion' : '0DTE Iron Condor'} trade with ${quantity} contract(s)?`
    );

    if (!confirmed) return;

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      if (strategy === 'iron-condor') {
        // Execute Iron Condor
        const buildResponse = await apiService.buildIronCondor({} as any, 0); // Placeholder
        const result = await apiService.executeMultiLegOrder(buildResponse as any);

        if (result.success) {
          setSuccess(`✓ Iron condor executed successfully!`);
          if (onExecute) onExecute();
          setTimeout(handleCloseModal, 2000);
        } else {
          setError(result.error || 'Execution failed');
        }
      } else {
        // Execute IV Mean Reversion
        // This would require generating signal and getting approval first
        setError('IV Mean Reversion execution requires signal generation first');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Main Button - Ben AI Styling */}
      <button
        onClick={handleOpenModal}
        disabled={disabled}
        className="
          w-full px-6 py-4
          bg-black text-white
          rounded-xl shadow-lg
          font-sans font-medium text-lg
          hover:shadow-xl hover:scale-[1.02]
          active:scale-[0.98]
          disabled:opacity-50 disabled:cursor-not-allowed
          transition-all duration-200
          flex items-center justify-center gap-2
        "
      >
        <span>✨</span>
        <span>Execute Trade</span>
      </button>

      {/* Modal Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
          onClick={handleCloseModal}
        >
          <div
            className="bg-[#F5F1E8] rounded-2xl shadow-2xl max-w-md w-full p-6"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex justify-between items-start mb-6">
              <div>
                <h2 className="text-2xl font-sans font-semibold text-black">
                  {strategy === 'iv-mean-reversion' ? 'IV Mean Reversion' : '0DTE Iron Condor'}
                </h2>
                <p className="text-sm text-gray-600 mt-1">Execute options trade</p>
              </div>
              <button
                onClick={handleCloseModal}
                className="text-gray-500 hover:text-black text-2xl leading-none"
              >
                ×
              </button>
            </div>

            {/* Strategy Details */}
            <div className="bg-white rounded-xl p-4 mb-6 shadow-sm">
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-sans text-gray-600 uppercase tracking-wide">
                    Strategy
                  </span>
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-teal-100 text-teal-800">
                    {strategy === 'iv-mean-reversion' ? 'IV MEAN REVERSION' : '0DTE IRON CONDOR'}
                  </span>
                </div>

                {strategy === 'iron-condor' && (
                  <>
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-sans text-gray-600">Entry Window</span>
                      <span className="text-sm font-mono text-black">9:31-9:45am ET</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-sans text-gray-600">Target Delta</span>
                      <span className="text-sm font-mono text-black">0.15</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-sans text-gray-600">Profit Target</span>
                      <span className="text-sm font-mono text-green-600">50%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-sans text-gray-600">Stop Loss</span>
                      <span className="text-sm font-mono text-red-600">2x credit</span>
                    </div>
                  </>
                )}

                {strategy === 'iv-mean-reversion' && (
                  <>
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-sans text-gray-600">IV Threshold</span>
                      <span className="text-sm font-mono text-black">30th / 70th percentile</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-sans text-gray-600">Profit Target</span>
                      <span className="text-sm font-mono text-green-600">50%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-sans text-gray-600">Stop Loss</span>
                      <span className="text-sm font-mono text-red-600">75%</span>
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Quantity Selector */}
            <div className="mb-6">
              <label className="block text-sm font-sans text-gray-600 uppercase tracking-wide mb-2">
                Quantity
              </label>
              <select
                value={quantity}
                onChange={(e) => setQuantity(Number(e.target.value))}
                disabled={loading}
                className="
                  w-full px-4 py-3
                  bg-white border-2 border-gray-200
                  rounded-xl
                  font-mono text-lg text-black
                  focus:outline-none focus:border-teal-500
                  disabled:opacity-50 disabled:cursor-not-allowed
                  transition-colors
                "
              >
                <option value={1}>1 contract</option>
                <option value={2}>2 contracts</option>
                <option value={5}>5 contracts</option>
                <option value={10}>10 contracts</option>
              </select>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-4 p-4 bg-red-50 border-2 border-red-200 rounded-xl">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            {/* Success Message */}
            {success && (
              <div className="mb-4 p-4 bg-green-50 border-2 border-green-200 rounded-xl">
                <p className="text-sm text-green-800">{success}</p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3">
              <button
                onClick={handleCloseModal}
                disabled={loading}
                className="
                  flex-1 px-6 py-3
                  bg-white text-black border-2 border-gray-300
                  rounded-xl font-sans font-medium
                  hover:bg-gray-50
                  disabled:opacity-50 disabled:cursor-not-allowed
                  transition-colors
                "
              >
                Cancel
              </button>
              <button
                onClick={handleExecute}
                disabled={loading}
                className="
                  flex-1 px-6 py-3
                  bg-black text-white
                  rounded-xl font-sans font-medium
                  hover:bg-gray-800
                  disabled:opacity-50 disabled:cursor-not-allowed
                  transition-colors
                  flex items-center justify-center gap-2
                "
              >
                {loading ? (
                  <>
                    <span className="animate-spin">⏳</span>
                    <span>Executing...</span>
                  </>
                ) : (
                  <>
                    <span>✨</span>
                    <span>Execute</span>
                  </>
                )}
              </button>
            </div>

            {/* PAPER TRADING Notice */}
            <div className="mt-4 pt-4 border-t border-gray-300">
              <div className="flex items-center justify-center gap-2">
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                  PAPER TRADING
                </span>
                <span className="text-xs text-gray-500">No real money at risk</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
