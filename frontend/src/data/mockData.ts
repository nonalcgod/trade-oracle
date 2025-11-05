// Mock data for UI testing - Trade Oracle
import type { Portfolio, Trade, CircuitBreakers, ServiceStatus } from '../types/trading';

export const mockPortfolio: Portfolio = {
  balance: 102350.00,
  dailyPnL: 2350.00,
  dailyPnLPercent: 2.35,
  winRate: 76.2,
  consecutiveLosses: 1,
  delta: 12.4,
  theta: -8.2,
  activePositions: 3,
  lastUpdate: new Date()
};

export const mockTrades: Trade[] = [
  {
    symbol: "SPY250117C00450000",
    ivPercentile: 73,
    signalType: "SELL",
    entryPrice: 4.50,
    exitPrice: 3.20,
    pnl: 1300,
    pnlPercent: 28.8,
    commission: 0.65,
    slippage: 4.50,
    timestamp: "2h ago"
  },
  {
    symbol: "QQQ250124P00380000",
    ivPercentile: 28,
    signalType: "BUY",
    entryPrice: 2.10,
    exitPrice: 1.85,
    pnl: -250,
    pnlPercent: -11.9,
    commission: 0.65,
    slippage: 2.10,
    timestamp: "5h ago"
  },
  {
    symbol: "IWM250131C00210000",
    ivPercentile: 81,
    signalType: "SELL",
    entryPrice: 3.75,
    exitPrice: 2.90,
    pnl: 850,
    pnlPercent: 22.6,
    commission: 0.65,
    slippage: 3.75,
    timestamp: "1d ago"
  },
  {
    symbol: "SPY250214P00440000",
    ivPercentile: 25,
    signalType: "BUY",
    entryPrice: 1.95,
    exitPrice: 2.45,
    pnl: 500,
    pnlPercent: 25.6,
    commission: 0.65,
    slippage: 1.95,
    timestamp: "2d ago"
  }
];

export const mockCircuitBreakers: CircuitBreakers = {
  dailyLossPercent: -2.1,
  dailyLossLimit: -3.0,
  consecutiveLosses: 1,
  consecutiveLossLimit: 3,
  maxRiskPerTrade: 2.0
};

export const mockServices: ServiceStatus = {
  backendApi: true,
  alpacaMarkets: true,
  supabaseDatabase: true
};
