-- Trade Oracle Performance Indexes
-- Execute these in Supabase SQL Editor for immediate performance gains
-- Expected Impact: 90-day IV rank queries from ~500ms to ~50ms

-- ============================================================================
-- HIGH PRIORITY INDEXES (Execute First)
-- ============================================================================

-- 1. IV Rank Calculation (Most Common Query)
-- Used by strategy service for 90-day IV rank calculation
CREATE INDEX IF NOT EXISTS idx_option_ticks_symbol_timestamp
  ON option_ticks(symbol, timestamp DESC);

-- 2. Open Positions Quick Lookup
-- Used by position monitor every 60 seconds
CREATE INDEX IF NOT EXISTS idx_positions_status_opened
  ON positions(status, opened_at DESC)
  WHERE status = 'open';

-- 3. Recent Trades Lookup
-- Used by dashboard for trade history display
CREATE INDEX IF NOT EXISTS idx_trades_timestamp_desc
  ON trades(timestamp DESC);

-- 4. Position History by Symbol
-- Used for per-symbol performance analysis
CREATE INDEX IF NOT EXISTS idx_positions_symbol_status
  ON positions(symbol, status);

-- ============================================================================
-- MEDIUM PRIORITY INDEXES
-- ============================================================================

-- 5. Strategy Performance Analysis
-- Used for risk management historical stats
CREATE INDEX IF NOT EXISTS idx_trades_strategy_timestamp
  ON trades(strategy, timestamp DESC)
  WHERE exit_price IS NOT NULL;

-- 6. Daily Portfolio Snapshots
-- Used for equity curve and performance charting
CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_timestamp_desc
  ON portfolio_snapshots(timestamp DESC);

-- 7. Option Ticks by IV (High Volatility Search)
-- Used to find elevated IV opportunities
CREATE INDEX IF NOT EXISTS idx_option_ticks_iv_desc
  ON option_ticks(iv DESC)
  WHERE iv IS NOT NULL
    AND timestamp > NOW() - INTERVAL '90 days';

-- ============================================================================
-- PARTIAL INDEXES (Save Space, Improve Speed)
-- ============================================================================

-- 8. Recent Option Ticks (90-day window)
-- Reduces index size significantly
CREATE INDEX IF NOT EXISTS idx_option_ticks_recent
  ON option_ticks(symbol, timestamp DESC, iv)
  WHERE timestamp > NOW() - INTERVAL '90 days';

-- 9. Winning Trades Only
-- Fast lookup for win rate calculations
CREATE INDEX IF NOT EXISTS idx_trades_wins
  ON trades(strategy, pnl)
  WHERE pnl > 0 AND exit_price IS NOT NULL;

-- 10. Losing Trades Only
-- Fast lookup for risk analysis
CREATE INDEX IF NOT EXISTS idx_trades_losses
  ON trades(strategy, pnl)
  WHERE pnl < 0 AND exit_price IS NOT NULL;

-- ============================================================================
-- ANALYZE TABLES (Update Query Planner Statistics)
-- ============================================================================

ANALYZE option_ticks;
ANALYZE trades;
ANALYZE positions;
ANALYZE portfolio_snapshots;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check index sizes
SELECT
  schemaname,
  tablename,
  indexname,
  pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_indexes
JOIN pg_class ON pg_class.relname = indexname
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;

-- Check query performance before/after
-- Run this before and after creating indexes
EXPLAIN ANALYZE
SELECT iv
FROM option_ticks
WHERE symbol = 'QQQ251219C00640000'
  AND timestamp > NOW() - INTERVAL '90 days'
ORDER BY timestamp DESC;

-- Expected improvement:
-- BEFORE: Seq Scan on option_ticks (cost=0.00..1234.56)
-- AFTER:  Index Scan using idx_option_ticks_symbol_timestamp (cost=0.42..12.34)
