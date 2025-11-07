/**
 * useScalperSignals Hook
 *
 * Polls momentum scalping signals from backend every 60 seconds
 * Provides real-time signal data with 6-condition validation
 *
 * @returns {Object} Signal state
 * - signals: MomentumSignal[] - Array of current signals
 * - entryWindowActive: boolean - Backend-reported entry window status
 * - lastUpdate: Date | null - Last successful fetch timestamp
 * - loading: boolean - Initial loading state
 * - error: string | null - Error message if fetch fails
 * - refetch: () => Promise<void> - Manual refetch function
 */

import { useState, useEffect, useCallback } from 'react';

export interface MomentumSignal {
  signal_id: string;
  symbol: string;
  signal_type: 'BUY' | 'SELL';
  option_symbol?: string;
  confidence: number;

  // Technical indicators
  ema_9: number;
  ema_21: number;
  rsi_14: number;
  vwap: number;
  relative_volume: number;

  // 6-condition validation
  conditions_met?: {
    ema_crossover: boolean;
    rsi_confirmation: boolean;
    volume_spike: boolean;
    vwap_breakout: boolean;
    relative_strength: boolean;
    entry_window: boolean;
  };

  // Entry/Exit levels
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

interface UseScalperSignalsState {
  signals: MomentumSignal[];
  entryWindowActive: boolean;
  lastUpdate: Date | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

const POLL_INTERVAL = 60000; // 60 seconds

export const useScalperSignals = (): UseScalperSignalsState => {
  const [signals, setSignals] = useState<MomentumSignal[]>([]);
  const [entryWindowActive, setEntryWindowActive] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const fetchSignals = useCallback(async () => {
    try {
      const response = await fetch(`${apiUrl}/api/momentum-scalping/scan`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: ScanResponse = await response.json();

      setSignals(data.signals || []);
      setEntryWindowActive(data.entry_window_active);
      setLastUpdate(new Date());
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(`Signal fetch failed: ${errorMessage}`);
      console.error('Signal fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [apiUrl]);

  useEffect(() => {
    // Fetch immediately on mount
    fetchSignals();

    // Poll every 60 seconds
    const interval = setInterval(fetchSignals, POLL_INTERVAL);

    // Cleanup on unmount
    return () => clearInterval(interval);
  }, [fetchSignals]);

  return {
    signals,
    entryWindowActive,
    lastUpdate,
    loading,
    error,
    refetch: fetchSignals,
  };
};
