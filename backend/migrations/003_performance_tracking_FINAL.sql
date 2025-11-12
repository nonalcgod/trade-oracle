-- Migration 003: Performance Tracking for Copy Trading Evaluation (FINAL)
-- Purpose: Track strategy performance over time to determine readiness for live capital
-- Date: 2025-11-11
-- Author: Claude Code + User
-- FIX: Uses actual trades table columns (signal_type, not action)

-- ============================================================================
-- PART 0: Drop conflicting views from previous migrations
-- ============================================================================

DROP VIEW IF EXISTS v_latest_strategy_performance CASCADE;
DROP VIEW IF EXISTS v_equity_curve CASCADE;
DROP VIEW IF EXISTS v_recent_trades_with_strategy CASCADE;
DROP VIEW IF EXISTS strategy_performance CASCADE;

-- ============================================================================
-- PART 1: Enhance trades table with copy trading metadata
-- ============================================================================

-- Add trading mode column (paper vs live)
ALTER TABLE trades ADD COLUMN IF NOT EXISTS trading_mode VARCHAR(10) DEFAULT 'paper';

-- Add account balance at time of trade (for position sizing analysis)
ALTER TABLE trades ADD COLUMN IF NOT EXISTS account_balance NUMERIC(15,2);

-- Add risk percentage used (for risk management validation)
ALTER TABLE trades ADD COLUMN IF NOT EXISTS risk_percentage NUMERIC(5,2);

-- Add strategy name for filtering (standardized enum-style names)
ALTER TABLE trades ADD COLUMN IF NOT EXISTS strategy_name VARCHAR(50);

-- Create index for fast strategy filtering
CREATE INDEX IF NOT EXISTS idx_trades_strategy_mode ON trades(strategy_name, trading_mode);
CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp);

-- ============================================================================
-- PART 2: Daily performance snapshots (equity curve)
-- ============================================================================

CREATE TABLE IF NOT EXISTS performance_snapshots (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    trading_mode VARCHAR(10) DEFAULT 'paper',

    -- Account metrics
    account_balance NUMERIC(15,2) NOT NULL,
    daily_pnl NUMERIC(15,2),
    cumulative_pnl NUMERIC(15,2),

    -- Trade metrics
    total_trades INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    win_rate NUMERIC(5,2),

    -- Risk metrics
    max_drawdown NUMERIC(5,2),
    sharpe_ratio NUMERIC(5,2),
    profit_factor NUMERIC(5,2),

    -- Risk management
    circuit_breakers_triggered INTEGER DEFAULT 0,
    max_consecutive_losses INTEGER DEFAULT 0,
    largest_loss NUMERIC(15,2),

    created_at TIMESTAMP DEFAULT NOW(),

    -- Unique constraint: One snapshot per date per mode
    UNIQUE(date, trading_mode)
);

CREATE INDEX IF NOT EXISTS idx_snapshots_date ON performance_snapshots(date DESC);
CREATE INDEX IF NOT EXISTS idx_snapshots_mode ON performance_snapshots(trading_mode);

-- ============================================================================
-- PART 3: Strategy-specific performance (monthly aggregation)
-- ============================================================================

CREATE TABLE IF NOT EXISTS strategy_performance (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(50) NOT NULL,
    month VARCHAR(7) NOT NULL,  -- Format: '2025-11'
    trading_mode VARCHAR(10) DEFAULT 'paper',

    -- Trade statistics
    total_trades INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    win_rate NUMERIC(5,2),

    -- P&L metrics
    total_pnl NUMERIC(15,2),
    average_win NUMERIC(15,2),
    average_loss NUMERIC(15,2),
    largest_win NUMERIC(15,2),
    largest_loss NUMERIC(15,2),

    -- Risk-adjusted returns
    sharpe_ratio NUMERIC(5,2),
    sortino_ratio NUMERIC(5,2),
    profit_factor NUMERIC(5,2),
    max_drawdown NUMERIC(5,2),

    -- Statistical confidence
    confidence_score NUMERIC(5,2),  -- 0-100 (statistical significance)
    sample_size_adequate BOOLEAN DEFAULT FALSE,  -- TRUE if >= 100 trades

    -- Copy trading readiness
    ready_for_live BOOLEAN DEFAULT FALSE,
    ready_for_live_reason TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Unique constraint: One record per strategy per month per mode
    UNIQUE(strategy_name, month, trading_mode)
);

CREATE INDEX IF NOT EXISTS idx_strategy_perf_name ON strategy_performance(strategy_name);
CREATE INDEX IF NOT EXISTS idx_strategy_perf_month ON strategy_performance(month DESC);
CREATE INDEX IF NOT EXISTS idx_strategy_perf_ready ON strategy_performance(ready_for_live);

-- ============================================================================
-- PART 4: Trading session logs (for audit trail)
-- ============================================================================

CREATE TABLE IF NOT EXISTS trading_sessions (
    id SERIAL PRIMARY KEY,
    session_date DATE NOT NULL,
    trading_mode VARCHAR(10) DEFAULT 'paper',

    -- Session metrics
    trades_executed INTEGER DEFAULT 0,
    strategies_used TEXT[],  -- Array of strategy names

    -- Market conditions
    vix_open NUMERIC(5,2),
    vix_close NUMERIC(5,2),
    market_regime VARCHAR(20),  -- 'high_vol', 'low_vol', 'trending', 'choppy'

    -- Session P&L
    session_pnl NUMERIC(15,2),

    -- Risk events
    circuit_breakers_hit TEXT[],  -- Array of triggered breaker names
    manual_interventions INTEGER DEFAULT 0,

    -- Notes
    notes TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_date ON trading_sessions(session_date DESC);

-- ============================================================================
-- PART 5: Strategy readiness criteria (configuration)
-- ============================================================================

CREATE TABLE IF NOT EXISTS strategy_criteria (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(50) NOT NULL UNIQUE,

    -- Minimum requirements for live trading
    min_trades_required INTEGER DEFAULT 100,
    min_win_rate NUMERIC(5,2) DEFAULT 65.0,
    min_sharpe_ratio NUMERIC(5,2) DEFAULT 1.5,
    max_drawdown_threshold NUMERIC(5,2) DEFAULT 10.0,
    min_profit_factor NUMERIC(5,2) DEFAULT 2.0,

    -- Current status
    is_enabled BOOLEAN DEFAULT TRUE,
    is_ready_for_live BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Insert default criteria for all 3 strategies
INSERT INTO strategy_criteria (strategy_name, min_trades_required, min_win_rate, min_sharpe_ratio, max_drawdown_threshold, min_profit_factor)
VALUES
    ('IV_MEAN_REVERSION', 100, 65.0, 1.5, 10.0, 2.0),
    ('IRON_CONDOR', 100, 65.0, 1.5, 10.0, 2.0),
    ('MOMENTUM_SCALPING', 100, 60.0, 1.3, 12.0, 1.8)  -- Slightly more lenient (higher variance)
ON CONFLICT (strategy_name) DO NOTHING;

-- ============================================================================
-- PART 6: Helper views for quick queries
-- ============================================================================

-- View: Latest performance for each strategy
CREATE OR REPLACE VIEW v_latest_strategy_performance AS
SELECT
    sp.*,
    sc.min_win_rate,
    sc.min_sharpe_ratio,
    sc.min_trades_required,
    CASE
        WHEN sp.total_trades >= sc.min_trades_required
             AND sp.win_rate >= sc.min_win_rate
             AND sp.sharpe_ratio >= sc.min_sharpe_ratio
             AND sp.max_drawdown <= sc.max_drawdown_threshold
        THEN TRUE
        ELSE FALSE
    END AS meets_criteria
FROM strategy_performance sp
JOIN strategy_criteria sc ON sp.strategy_name = sc.strategy_name
WHERE sp.month = TO_CHAR(CURRENT_DATE, 'YYYY-MM')
  AND sp.trading_mode = 'paper';

-- View: Equity curve (daily balance)
CREATE OR REPLACE VIEW v_equity_curve AS
SELECT
    date,
    account_balance,
    daily_pnl,
    cumulative_pnl,
    win_rate,
    max_drawdown,
    sharpe_ratio
FROM performance_snapshots
WHERE trading_mode = 'paper'
ORDER BY date DESC;

-- View: Recent trades with strategy breakdown
-- FIXED: Uses signal_type (not action) to match actual trades table
CREATE OR REPLACE VIEW v_recent_trades_with_strategy AS
SELECT
    t.id,
    t.timestamp,
    t.symbol,
    t.strategy_name,
    t.signal_type AS action,  -- FIXED: maps signal_type to action
    t.quantity,
    t.entry_price,
    t.exit_price,
    t.pnl,
    t.commission,
    t.trading_mode,
    t.risk_percentage,
    CASE WHEN t.pnl > 0 THEN 'WIN' ELSE 'LOSS' END as outcome
FROM trades t
ORDER BY t.timestamp DESC
LIMIT 100;

-- ============================================================================
-- PART 7: Update function for strategy performance (automated calculation)
-- ============================================================================

CREATE OR REPLACE FUNCTION update_strategy_performance(
    p_strategy_name VARCHAR,
    p_month VARCHAR,
    p_trading_mode VARCHAR DEFAULT 'paper'
)
RETURNS void AS $$
DECLARE
    v_total_trades INTEGER;
    v_wins INTEGER;
    v_losses INTEGER;
    v_win_rate NUMERIC(5,2);
    v_total_pnl NUMERIC(15,2);
    v_avg_win NUMERIC(15,2);
    v_avg_loss NUMERIC(15,2);
    v_confidence NUMERIC(5,2);
    v_ready BOOLEAN;
    v_reason TEXT;
BEGIN
    -- Calculate metrics from trades
    SELECT
        COUNT(*),
        COUNT(*) FILTER (WHERE pnl > 0),
        COUNT(*) FILTER (WHERE pnl <= 0),
        ROUND((COUNT(*) FILTER (WHERE pnl > 0)::NUMERIC / NULLIF(COUNT(*), 0) * 100), 2),
        SUM(pnl),
        AVG(pnl) FILTER (WHERE pnl > 0),
        AVG(pnl) FILTER (WHERE pnl <= 0)
    INTO
        v_total_trades,
        v_wins,
        v_losses,
        v_win_rate,
        v_total_pnl,
        v_avg_win,
        v_avg_loss
    FROM trades
    WHERE strategy_name = p_strategy_name
      AND TO_CHAR(timestamp, 'YYYY-MM') = p_month
      AND trading_mode = p_trading_mode;

    -- Calculate confidence score (0-100)
    -- Based on sample size and consistency
    v_confidence := CASE
        WHEN v_total_trades >= 100 AND v_win_rate >= 70 THEN 95
        WHEN v_total_trades >= 100 AND v_win_rate >= 65 THEN 90
        WHEN v_total_trades >= 50 AND v_win_rate >= 65 THEN 75
        WHEN v_total_trades >= 30 THEN 60
        ELSE 40
    END;

    -- Determine readiness for live trading
    SELECT
        CASE
            WHEN v_total_trades >= sc.min_trades_required
                 AND v_win_rate >= sc.min_win_rate
            THEN TRUE
            ELSE FALSE
        END,
        CASE
            WHEN v_total_trades < sc.min_trades_required
            THEN 'Need ' || (sc.min_trades_required - v_total_trades) || ' more trades'
            WHEN v_win_rate < sc.min_win_rate
            THEN 'Win rate ' || v_win_rate || '% below required ' || sc.min_win_rate || '%'
            ELSE 'Ready for live trading'
        END
    INTO v_ready, v_reason
    FROM strategy_criteria sc
    WHERE sc.strategy_name = p_strategy_name;

    -- Upsert into strategy_performance table
    INSERT INTO strategy_performance (
        strategy_name, month, trading_mode, total_trades, wins, losses, win_rate,
        total_pnl, average_win, average_loss, confidence_score,
        sample_size_adequate, ready_for_live, ready_for_live_reason, updated_at
    )
    VALUES (
        p_strategy_name, p_month, p_trading_mode, v_total_trades, v_wins, v_losses, v_win_rate,
        v_total_pnl, v_avg_win, v_avg_loss, v_confidence,
        v_total_trades >= 100, v_ready, v_reason, NOW()
    )
    ON CONFLICT (strategy_name, month, trading_mode)
    DO UPDATE SET
        total_trades = EXCLUDED.total_trades,
        wins = EXCLUDED.wins,
        losses = EXCLUDED.losses,
        win_rate = EXCLUDED.win_rate,
        total_pnl = EXCLUDED.total_pnl,
        average_win = EXCLUDED.average_win,
        average_loss = EXCLUDED.average_loss,
        confidence_score = EXCLUDED.confidence_score,
        sample_size_adequate = EXCLUDED.sample_size_adequate,
        ready_for_live = EXCLUDED.ready_for_live,
        ready_for_live_reason = EXCLUDED.ready_for_live_reason,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PART 8: Trigger to auto-update strategy performance after each trade
-- ============================================================================

CREATE OR REPLACE FUNCTION trigger_update_strategy_performance()
RETURNS TRIGGER AS $$
BEGIN
    -- Update performance for the strategy and month of this trade
    PERFORM update_strategy_performance(
        NEW.strategy_name,
        TO_CHAR(NEW.timestamp, 'YYYY-MM'),
        NEW.trading_mode
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger (only if it doesn't exist)
DROP TRIGGER IF EXISTS after_trade_insert_update_performance ON trades;
CREATE TRIGGER after_trade_insert_update_performance
    AFTER INSERT OR UPDATE ON trades
    FOR EACH ROW
    WHEN (NEW.strategy_name IS NOT NULL)
    EXECUTE FUNCTION trigger_update_strategy_performance();

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Verify tables created
DO $$
BEGIN
    RAISE NOTICE 'Migration 003 complete. Tables created:';
    RAISE NOTICE '  - trades (enhanced with copy trading columns)';
    RAISE NOTICE '  - performance_snapshots (daily equity curve)';
    RAISE NOTICE '  - strategy_performance (monthly aggregation)';
    RAISE NOTICE '  - trading_sessions (audit trail)';
    RAISE NOTICE '  - strategy_criteria (readiness thresholds)';
    RAISE NOTICE 'Views created:';
    RAISE NOTICE '  - v_latest_strategy_performance';
    RAISE NOTICE '  - v_equity_curve';
    RAISE NOTICE '  - v_recent_trades_with_strategy';
    RAISE NOTICE 'Functions created:';
    RAISE NOTICE '  - update_strategy_performance()';
    RAISE NOTICE 'Triggers created:';
    RAISE NOTICE '  - after_trade_insert_update_performance';
    RAISE NOTICE '';
    RAISE NOTICE 'Ready for copy trading evaluation! 🚀';
END $$;
