-- Trade Oracle - Supabase Schema
-- Execute this in Supabase SQL Editor or via psql

-- Enable UUID extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table: option_ticks
-- Stores real-time market data with Greeks
CREATE TABLE IF NOT EXISTS option_ticks (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    symbol TEXT NOT NULL,
    underlying_price NUMERIC(10,2),
    strike NUMERIC(10,2),
    bid NUMERIC(10,4),
    ask NUMERIC(10,4),
    delta NUMERIC(8,6),
    gamma NUMERIC(8,6),
    theta NUMERIC(8,6),
    vega NUMERIC(8,6),
    iv NUMERIC(8,6)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_ticks_time ON option_ticks(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ticks_symbol ON option_ticks(symbol);
CREATE INDEX IF NOT EXISTS idx_ticks_symbol_time ON option_ticks(symbol, timestamp DESC);

-- Table: trades
-- Execution history with P&L tracking
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    symbol TEXT NOT NULL,
    strategy TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    entry_price NUMERIC(10,4),
    exit_price NUMERIC(10,4),
    quantity INTEGER,
    pnl NUMERIC(12,2),
    commission NUMERIC(8,2),
    slippage NUMERIC(8,4),
    reasoning TEXT
);

-- Indexes for performance queries
CREATE INDEX IF NOT EXISTS idx_trades_time ON trades(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_trades_strategy ON trades(strategy);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);

-- Table: reflections
-- Weekly Claude AI analysis of trading performance
CREATE TABLE IF NOT EXISTS reflections (
    id SERIAL PRIMARY KEY,
    week_ending DATE NOT NULL,
    analysis JSONB NOT NULL,
    metrics JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for date-based queries
CREATE INDEX IF NOT EXISTS idx_reflections_week ON reflections(week_ending DESC);

-- Table: portfolio_snapshots
-- Daily portfolio state for tracking equity curve
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    balance NUMERIC(12,2),
    daily_pnl NUMERIC(12,2),
    win_rate NUMERIC(5,4),
    consecutive_losses INTEGER,
    delta NUMERIC(10,4),
    theta NUMERIC(10,4),
    active_positions INTEGER
);

-- Index for time-series queries
CREATE INDEX IF NOT EXISTS idx_snapshots_time ON portfolio_snapshots(timestamp DESC);

-- View: recent_trades
-- Convenience view for dashboard
CREATE OR REPLACE VIEW recent_trades AS
SELECT 
    id,
    timestamp,
    symbol,
    strategy,
    signal_type,
    entry_price,
    exit_price,
    quantity,
    pnl,
    commission,
    slippage
FROM trades
ORDER BY timestamp DESC
LIMIT 100;

-- Table: positions
-- Track open and closed positions with full lifecycle
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    strategy TEXT NOT NULL,
    position_type TEXT NOT NULL,  -- 'long' or 'short'
    quantity INTEGER NOT NULL,
    entry_price NUMERIC(10,4),
    entry_trade_id INTEGER REFERENCES trades(id),
    current_price NUMERIC(10,4),
    unrealized_pnl NUMERIC(12,2),
    opened_at TIMESTAMPTZ DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    exit_trade_id INTEGER REFERENCES trades(id),
    exit_reason TEXT,
    status TEXT DEFAULT 'open'  -- 'open' or 'closed'
);

-- Indexes for position queries
CREATE INDEX IF NOT EXISTS idx_positions_open ON positions(status) WHERE status = 'open';
CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);
CREATE INDEX IF NOT EXISTS idx_positions_opened ON positions(opened_at DESC);

-- View: strategy_performance
-- Aggregate statistics by strategy
CREATE OR REPLACE VIEW strategy_performance AS
SELECT
    strategy,
    COUNT(*) as total_trades,
    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as win_rate,
    AVG(CASE WHEN pnl > 0 THEN pnl ELSE NULL END) as avg_win,
    AVG(CASE WHEN pnl < 0 THEN pnl ELSE NULL END) as avg_loss,
    SUM(pnl) as total_pnl
FROM trades
WHERE exit_price IS NOT NULL
GROUP BY strategy;

