/**
 * useScalperPositions Hook
 *
 * Polls active momentum scalping positions every 3 seconds
 * Calculates real-time P&L and exit target progress
 *
 * @returns {Object} Position state
 * - positions: ScalperPosition[] - Active momentum positions with progress
 * - loading: boolean - Initial loading state
 * - error: string | null - Error message if fetch fails
 * - refetch: () => Promise<void> - Manual refetch function
 */

import { useState, useEffect, useCallback } from 'react';

interface Position {
  id: number;
  symbol: string;
  option_symbol: string;
  strategy: string;
  action: 'BUY' | 'SELL';
  quantity: number;
  entry_price: number;
  current_price: number;
  entry_time: string;
  status: string;
  pnl?: number;
  pnl_percent?: number;
  exit_conditions?: {
    target_1?: number;
    target_2?: number;
    stop_loss?: number;
    force_close_time?: string;
  };
}

export interface ScalperPosition extends Position {
  // Exit target progress (0-100)
  target1Progress: number;
  target2Progress: number;
  stopLossDistance: number; // How far from stop loss (positive = safe)
  timeToForceClose: string; // Human-readable time remaining
  minutesToForceClose: number;
}

interface UseScalperPositionsState {
  positions: ScalperPosition[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

const POLL_INTERVAL = 3000; // 3 seconds
const FORCE_CLOSE_HOUR = 11;
const FORCE_CLOSE_MINUTE = 30;

const calculateExitProgress = (position: Position): ScalperPosition => {
  const { entry_price, current_price, exit_conditions, action } = position;

  // Default progress values
  let target1Progress = 0;
  let target2Progress = 0;
  let stopLossDistance = 100; // Default safe distance

  if (exit_conditions) {
    const { target_1, target_2, stop_loss } = exit_conditions;

    if (action === 'BUY') {
      // Long position: profit when price goes up
      if (target_1) {
        const targetRange = target_1 - entry_price;
        const currentRange = current_price - entry_price;
        target1Progress = Math.min(100, Math.max(0, (currentRange / targetRange) * 100));
      }

      if (target_2) {
        const targetRange = target_2 - entry_price;
        const currentRange = current_price - entry_price;
        target2Progress = Math.min(100, Math.max(0, (currentRange / targetRange) * 100));
      }

      if (stop_loss) {
        // Distance from stop loss (negative = breached)
        stopLossDistance = ((current_price - stop_loss) / entry_price) * 100;
      }
    } else {
      // Short position: profit when price goes down
      if (target_1) {
        const targetRange = entry_price - target_1;
        const currentRange = entry_price - current_price;
        target1Progress = Math.min(100, Math.max(0, (currentRange / targetRange) * 100));
      }

      if (target_2) {
        const targetRange = entry_price - target_2;
        const currentRange = entry_price - current_price;
        target2Progress = Math.min(100, Math.max(0, (currentRange / targetRange) * 100));
      }

      if (stop_loss) {
        stopLossDistance = ((stop_loss - current_price) / entry_price) * 100;
      }
    }
  }

  // Calculate time to force close (11:30am ET)
  const now = new Date();
  const forceCloseTime = new Date(now);
  forceCloseTime.setHours(FORCE_CLOSE_HOUR, FORCE_CLOSE_MINUTE, 0, 0);

  const msToForceClose = forceCloseTime.getTime() - now.getTime();
  const minutesToForceClose = Math.max(0, Math.floor(msToForceClose / 60000));

  let timeToForceClose = 'Window closed';
  if (minutesToForceClose > 0) {
    const hours = Math.floor(minutesToForceClose / 60);
    const mins = minutesToForceClose % 60;
    if (hours > 0) {
      timeToForceClose = `${hours}h ${mins}m`;
    } else {
      timeToForceClose = `${mins} min`;
    }
  }

  return {
    ...position,
    target1Progress: Math.round(target1Progress),
    target2Progress: Math.round(target2Progress),
    stopLossDistance: Math.round(stopLossDistance),
    timeToForceClose,
    minutesToForceClose,
  };
};

export const useScalperPositions = (): UseScalperPositionsState => {
  const [positions, setPositions] = useState<ScalperPosition[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const fetchPositions = useCallback(async () => {
    try {
      const response = await fetch(`${apiUrl}/api/execution/positions`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: Position[] = await response.json();

      // Filter for momentum scalping positions only
      const momentumPositions = data.filter(
        (pos) => pos.strategy === 'MOMENTUM_SCALPING' && pos.status === 'OPEN'
      );

      // Calculate exit progress for each position
      const positionsWithProgress = momentumPositions.map(calculateExitProgress);

      setPositions(positionsWithProgress);
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(`Position fetch failed: ${errorMessage}`);
      console.error('Position fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [apiUrl]);

  useEffect(() => {
    // Fetch immediately on mount
    fetchPositions();

    // Poll every 3 seconds for real-time P&L
    const interval = setInterval(fetchPositions, POLL_INTERVAL);

    // Cleanup on unmount
    return () => clearInterval(interval);
  }, [fetchPositions]);

  return {
    positions,
    loading,
    error,
    refetch: fetchPositions,
  };
};
