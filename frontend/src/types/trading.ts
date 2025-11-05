// Trading data types for Trade Oracle UI

export interface Portfolio {
  balance: number;
  dailyPnL: number;
  dailyPnLPercent: number;
  winRate: number;
  consecutiveLosses: number;
  delta: number;
  theta: number;
  activePositions: number;
  lastUpdate: Date;
}

export interface Trade {
  symbol: string;
  ivPercentile: number;
  signalType: 'SELL' | 'BUY';
  entryPrice: number;
  exitPrice: number;
  pnl: number;
  pnlPercent: number;
  commission: number;
  slippage: number;
  timestamp: string;
}

export interface CircuitBreakers {
  dailyLossPercent: number;
  dailyLossLimit: number;
  consecutiveLosses: number;
  consecutiveLossLimit: number;
  maxRiskPerTrade: number;
}

export interface ServiceStatus {
  backendApi: boolean;
  alpacaMarkets: boolean;
  supabaseDatabase: boolean;
}
