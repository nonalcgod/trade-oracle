/**
 * useDisciplineTracker Hook
 *
 * Enforces 2-loss rule and 4-trade daily limit for momentum scalping
 * Uses localStorage for persistence across browser sessions
 * Auto-resets at midnight ET
 *
 * @returns {Object} Discipline state
 * - tradeCount: number - Total trades executed today (0-4)
 * - winCount: number - Winning trades today
 * - lossCount: number - Losing trades today
 * - consecutiveLosses: number - Current consecutive loss streak
 * - canTrade: boolean - Whether user can execute another trade
 * - recentTrades: TradeRecord[] - Last 5 trades for display
 * - recordTrade: (result: 'WIN' | 'LOSS', details: TradeDetails) => void
 * - resetDaily: () => void - Manual reset (for testing)
 */

import { useState, useEffect, useCallback } from 'react';

interface TradeDetails {
  symbol: string;
  pnl: number;
  pnlPercent: number;
  timestamp: string;
}

interface TradeRecord extends TradeDetails {
  result: 'WIN' | 'LOSS';
}

interface DailyStats {
  date: string; // YYYY-MM-DD
  tradeCount: number;
  winCount: number;
  lossCount: number;
  consecutiveLosses: number;
  recentTrades: TradeRecord[];
}

interface UseDisciplineTrackerState {
  tradeCount: number;
  winCount: number;
  lossCount: number;
  consecutiveLosses: number;
  canTrade: boolean;
  recentTrades: TradeRecord[];
  recordTrade: (result: 'WIN' | 'LOSS', details: TradeDetails) => void;
  resetDaily: () => void;
}

const STORAGE_KEY = 'scalper-discipline-tracker';
const MAX_TRADES_PER_DAY = 4;
const MAX_CONSECUTIVE_LOSSES = 2;

const getTodayDate = (): string => {
  const now = new Date();
  return now.toISOString().split('T')[0]; // YYYY-MM-DD
};

const getInitialStats = (): DailyStats => {
  const today = getTodayDate();

  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const stats: DailyStats = JSON.parse(stored);

      // Check if stored data is from today
      if (stats.date === today) {
        return stats;
      }
    }
  } catch (err) {
    console.error('Failed to load discipline tracker from localStorage:', err);
  }

  // Return fresh stats for today
  return {
    date: today,
    tradeCount: 0,
    winCount: 0,
    lossCount: 0,
    consecutiveLosses: 0,
    recentTrades: [],
  };
};

const saveStats = (stats: DailyStats): void => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(stats));
  } catch (err) {
    console.error('Failed to save discipline tracker to localStorage:', err);
  }
};

export const useDisciplineTracker = (): UseDisciplineTrackerState => {
  const [stats, setStats] = useState<DailyStats>(getInitialStats);

  // Auto-reset at midnight ET (check every minute)
  useEffect(() => {
    const checkForNewDay = () => {
      const today = getTodayDate();
      if (stats.date !== today) {
        console.log('New trading day detected - resetting discipline tracker');
        const newStats = getInitialStats();
        setStats(newStats);
        saveStats(newStats);
      }
    };

    const interval = setInterval(checkForNewDay, 60000); // Check every minute
    return () => clearInterval(interval);
  }, [stats.date]);

  // Calculate canTrade status
  const canTrade =
    stats.tradeCount < MAX_TRADES_PER_DAY &&
    stats.consecutiveLosses < MAX_CONSECUTIVE_LOSSES;

  const recordTrade = useCallback((result: 'WIN' | 'LOSS', details: TradeDetails) => {
    setStats((prevStats) => {
      const newStats: DailyStats = {
        ...prevStats,
        tradeCount: prevStats.tradeCount + 1,
        winCount: result === 'WIN' ? prevStats.winCount + 1 : prevStats.winCount,
        lossCount: result === 'LOSS' ? prevStats.lossCount + 1 : prevStats.lossCount,
        consecutiveLosses: result === 'LOSS' ? prevStats.consecutiveLosses + 1 : 0,
        recentTrades: [
          { result, ...details },
          ...prevStats.recentTrades,
        ].slice(0, 5), // Keep only last 5 trades
      };

      saveStats(newStats);
      return newStats;
    });
  }, []);

  const resetDaily = useCallback(() => {
    const newStats: DailyStats = {
      date: getTodayDate(),
      tradeCount: 0,
      winCount: 0,
      lossCount: 0,
      consecutiveLosses: 0,
      recentTrades: [],
    };
    setStats(newStats);
    saveStats(newStats);
  }, []);

  return {
    tradeCount: stats.tradeCount,
    winCount: stats.winCount,
    lossCount: stats.lossCount,
    consecutiveLosses: stats.consecutiveLosses,
    canTrade,
    recentTrades: stats.recentTrades,
    recordTrade,
    resetDaily,
  };
};
