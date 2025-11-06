import axios, { AxiosInstance } from 'axios';

// API Base URL - defaults to localhost for development, can be overridden by environment
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with base configuration
const api: AxiosInstance = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types for API responses
export interface PortfolioData {
  balance: number;
  daily_pnl: number;
  win_rate: number;
  consecutive_losses: number;
  delta: number;
  theta: number;
  active_positions: number;
  total_trades: number;
}

export interface Trade {
  id: number;
  timestamp: string;
  symbol: string;
  strategy: string;
  signal_type: 'buy' | 'sell';
  entry_price: number;
  exit_price: number | null;
  quantity: number;
  pnl: number;
  commission: number;
  slippage: number;
  reasoning: string;
}

export interface PerformanceMetrics {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  sharpe_ratio: number;
  max_drawdown: number;
}

export interface HealthStatus {
  status: string;
  services: {
    alpaca: 'configured' | 'not_configured';
    supabase: 'configured' | 'not_configured';
  };
  paper_trading: boolean;
}

export interface Position {
  id: number;
  symbol: string;
  strategy: string;
  position_type: 'long' | 'short';
  quantity: number;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  opened_at: string;
  status: string;
  legs?: IronCondorLeg[] | null;
  net_credit?: number | null;
  max_loss?: number | null;
  spread_width?: number | null;
}

export interface Signal {
  symbol: string;
  action: 'buy' | 'sell' | 'hold';
  confidence: number;
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  reasoning: string;
  iv_percentile: number;
  strategy: string;
}

export interface IronCondorLeg {
  side: 'buy' | 'sell';
  strike: number;
  type: 'call' | 'put';
  premium?: number;
}

export interface IronCondorBuild {
  legs: IronCondorLeg[];
  net_credit: number;
  max_loss: number;
  spread_width: number;
}

export interface EntryWindow {
  should_enter: boolean;
  reason: string;
  current_time: string;
}

export interface ExitCheck {
  should_exit: boolean;
  reason: string;
  current_pnl: number;
  current_pnl_percent: number;
}

// API Service Functions
export const apiService = {
  // Health & Status
  async getHealth(): Promise<HealthStatus> {
    const response = await api.get('/health');
    return response.data;
  },

  async getRoot() {
    const response = await api.get('/');
    return response.data;
  },

  // Portfolio
  async getPortfolio(): Promise<PortfolioData> {
    const response = await api.get('/api/execution/portfolio');
    const portfolio = response.data.portfolio;
    // Backend returns strings for Decimal fields - convert to numbers
    return {
      balance: parseFloat(portfolio.balance),
      daily_pnl: parseFloat(portfolio.daily_pnl),
      win_rate: portfolio.win_rate,
      consecutive_losses: portfolio.consecutive_losses,
      delta: parseFloat(portfolio.delta),
      theta: parseFloat(portfolio.theta),
      active_positions: portfolio.active_positions,
      total_trades: portfolio.total_trades,
    };
  },

  // Trades
  async getTrades(limit: number = 50): Promise<Trade[]> {
    const response = await api.get('/api/execution/trades', {
      params: { limit },
    });
    return response.data;
  },

  async getTradeById(id: number): Promise<Trade> {
    const response = await api.get(`/api/execution/trades/${id}`);
    return response.data;
  },

  // Performance
  async getPerformance(): Promise<PerformanceMetrics> {
    const response = await api.get('/api/execution/performance');
    return response.data;
  },

  // Strategies
  async getStrategyInfo() {
    const response = await api.get('/api/strategies/info');
    return response.data;
  },

  async getSignal(symbol: string) {
    const response = await api.get(`/api/strategies/signal/${symbol}`);
    return response.data;
  },

  // Risk Management
  async getRiskPortfolio() {
    const response = await api.get('/api/risk/portfolio');
    return response.data;
  },

  async approveRisk(data: unknown) {
    const response = await api.post('/api/risk/approve', data);
    return response.data;
  },

  // Data
  async getOptionData(symbol: string) {
    const response = await api.get(`/api/data/option/${symbol}`);
    return response.data;
  },

  // Positions
  async getPositions(): Promise<Position[]> {
    const response = await api.get('/api/execution/positions');
    return response.data.map((pos: any) => ({
      ...pos,
      entry_price: parseFloat(pos.entry_price),
      current_price: parseFloat(pos.current_price),
      unrealized_pnl: parseFloat(pos.unrealized_pnl),
    }));
  },

  async getPositionById(id: number): Promise<Position> {
    const response = await api.get(`/api/execution/positions/${id}`);
    return {
      ...response.data,
      entry_price: parseFloat(response.data.entry_price),
      current_price: parseFloat(response.data.current_price),
      unrealized_pnl: parseFloat(response.data.unrealized_pnl),
    };
  },

  // Iron Condor Methods
  async checkEntryWindow(): Promise<EntryWindow> {
    const response = await api.get('/api/iron-condor/should-enter');
    return response.data;
  },

  async generateIronCondorSignal(symbol: string, creditTarget?: number): Promise<Signal> {
    const response = await api.post('/api/iron-condor/signal', {
      symbol,
      credit_target: creditTarget,
    });
    return response.data;
  },

  async buildIronCondor(signal: Signal, underlyingPrice: number): Promise<IronCondorBuild> {
    const response = await api.post('/api/iron-condor/build', {
      signal,
      underlying_price: underlyingPrice,
    });
    return response.data;
  },

  async checkIronCondorExit(position: Position): Promise<ExitCheck> {
    const response = await api.post('/api/iron-condor/check-exit', {
      position,
    });
    return response.data;
  },

  async getIronCondorHealth(): Promise<{ status: string; initialized: boolean }> {
    const response = await api.get('/api/iron-condor/health');
    return response.data;
  },

  // Trade Execution
  async executeIVTrade(params: {
    symbol: string;
    side: 'buy' | 'sell';
    quantity: number;
    signal: any;
    approval: any;
  }): Promise<{ success: boolean; alpaca_order_id?: string; error?: string }> {
    const response = await api.post('/api/execution/order', {
      symbol: params.symbol,
      side: params.side,
      quantity: params.quantity,
      order_type: 'limit',
      signal: params.signal,
      approval: params.approval,
    });
    return response.data;
  },

  async executeMultiLegOrder(multiLegOrder: {
    strategy_type: string;
    legs: Array<{
      symbol: string;
      side: 'buy' | 'sell';
      quantity: number;
      option_type: 'call' | 'put';
      strike: number;
      expiration: string;
      limit_price: number;
    }>;
    net_credit: number;
    max_profit: number;
    max_loss: number;
  }): Promise<{ success: boolean; legs?: any[]; error?: string }> {
    const response = await api.post('/api/execution/order/multi-leg', multiLegOrder);
    return response.data;
  },
};

// Error handler wrapper
export const handleApiError = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    if (error.response) {
      // Server responded with error status
      return `Error: ${error.response.status} - ${error.response.statusText}`;
    } else if (error.request) {
      // Request made but no response
      return 'No response from server. Is the backend running?';
    } else {
      // Error in request setup
      return `Request error: ${error.message}`;
    }
  }
  return 'Unknown error occurred';
};

export default api;
