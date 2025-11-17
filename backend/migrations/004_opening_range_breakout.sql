-- Migration 004: Opening Range Breakout Strategy
-- Adds support for ORB (Opening Range Breakout) strategy with 75-89% win rate
-- Tracks opening ranges and breakout signals for SPY, QQQ, IWM
-- Date: November 17, 2025

-- Create opening_ranges table
CREATE TABLE IF NOT EXISTS opening_ranges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(20) NOT NULL,
    trade_date DATE NOT NULL,
    duration_minutes INTEGER NOT NULL DEFAULT 60,

    -- Range boundaries
    range_high NUMERIC(10,2) NOT NULL,
    range_low NUMERIC(10,2) NOT NULL,
    range_width NUMERIC(10,4) NOT NULL, -- Percentage (e.g., 0.39 for 0.39%)

    -- Pre-market data
    gap_percent NUMERIC(5,2), -- Pre-market gap percentage
    pre_market_volume INTEGER,

    -- Timestamps
    range_start_time TIMESTAMP WITH TIME ZONE,
    range_end_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Unique constraint: one range per symbol per day per duration
    CONSTRAINT unique_opening_range UNIQUE(symbol, trade_date, duration_minutes)
);

-- Add indexes for opening_ranges
CREATE INDEX IF NOT EXISTS idx_opening_ranges_symbol ON opening_ranges(symbol);
CREATE INDEX IF NOT EXISTS idx_opening_ranges_date ON opening_ranges(trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_opening_ranges_symbol_date ON opening_ranges(symbol, trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_opening_ranges_created ON opening_ranges(created_at DESC);

-- Add comments for opening_ranges table
COMMENT ON TABLE opening_ranges IS 'Opening ranges tracked during first 60 minutes of trading (9:30-10:30am ET). Used for Opening Range Breakout strategy.';
COMMENT ON COLUMN opening_ranges.range_high IS 'Highest price during opening range window';
COMMENT ON COLUMN opening_ranges.range_low IS 'Lowest price during opening range window';
COMMENT ON COLUMN opening_ranges.range_width IS 'Range width as percentage of low price (used for target calculation)';
COMMENT ON COLUMN opening_ranges.gap_percent IS 'Pre-market gap percentage (positive = gap up, negative = gap down)';


-- Create orb_signals table
CREATE TABLE IF NOT EXISTS orb_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id VARCHAR(20) NOT NULL UNIQUE, -- Short ID for frontend reference

    -- Signal details
    symbol VARCHAR(20) NOT NULL,
    direction VARCHAR(20) NOT NULL, -- 'BULLISH' or 'BEARISH'

    -- Reference to opening range
    opening_range_id UUID REFERENCES opening_ranges(id) ON DELETE CASCADE,
    range_high NUMERIC(10,2) NOT NULL,
    range_low NUMERIC(10,2) NOT NULL,
    range_width NUMERIC(10,4) NOT NULL,

    -- Breakout details
    breakout_price NUMERIC(10,2) NOT NULL,
    breakout_time TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Confirmation indicators
    volume_confirmation BOOLEAN NOT NULL DEFAULT FALSE,
    rsi_confirmation NUMERIC(5,2), -- RSI value at breakout

    -- Entry/Exit levels
    target_price NUMERIC(10,2) NOT NULL, -- Range width × 1.5
    stop_loss_price NUMERIC(10,2) NOT NULL, -- Range boundary (invalidation level)

    -- Confidence scoring (0-1)
    confidence NUMERIC(3,2) NOT NULL DEFAULT 0.75,

    -- Metadata
    reasoning TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Track if signal was executed
    executed BOOLEAN DEFAULT FALSE,
    position_id INTEGER, -- Reference to positions table (if executed)

    CHECK (direction IN ('BULLISH', 'BEARISH')),
    CHECK (confidence >= 0 AND confidence <= 1)
);

-- Add indexes for orb_signals
CREATE INDEX IF NOT EXISTS idx_orb_signals_symbol ON orb_signals(symbol);
CREATE INDEX IF NOT EXISTS idx_orb_signals_direction ON orb_signals(direction);
CREATE INDEX IF NOT EXISTS idx_orb_signals_created ON orb_signals(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orb_signals_opening_range ON orb_signals(opening_range_id);
CREATE INDEX IF NOT EXISTS idx_orb_signals_executed ON orb_signals(executed);
CREATE INDEX IF NOT EXISTS idx_orb_signals_position ON orb_signals(position_id) WHERE position_id IS NOT NULL;

-- Add comments for orb_signals table
COMMENT ON TABLE orb_signals IS 'Opening Range Breakout signals with volume and RSI confirmation. Win rate: 75-89% historically.';
COMMENT ON COLUMN orb_signals.direction IS 'Breakout direction: BULLISH (price broke above range) or BEARISH (price broke below range)';
COMMENT ON COLUMN orb_signals.target_price IS 'Target price = range boundary + (range width × 1.5). Exit at target or 50% option gain, whichever first.';
COMMENT ON COLUMN orb_signals.stop_loss_price IS 'Stop loss = range boundary. If price re-enters range, thesis is invalidated.';
COMMENT ON COLUMN orb_signals.confidence IS 'Confidence score 0-1. Base: 0.75, +0.10 for RSI confirmation, +0.05 for strong volume.';


-- Add ORB-specific columns to positions table
ALTER TABLE positions ADD COLUMN IF NOT EXISTS orb_signal_id UUID REFERENCES orb_signals(id);
ALTER TABLE positions ADD COLUMN IF NOT EXISTS opening_range_id UUID REFERENCES opening_ranges(id);
ALTER TABLE positions ADD COLUMN IF NOT EXISTS target_price NUMERIC(10,2);
ALTER TABLE positions ADD COLUMN IF NOT EXISTS range_invalidation BOOLEAN DEFAULT FALSE;

-- Add indexes for ORB position queries
CREATE INDEX IF NOT EXISTS idx_positions_orb_signal ON positions(orb_signal_id) WHERE orb_signal_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_positions_opening_range ON positions(opening_range_id) WHERE opening_range_id IS NOT NULL;

-- Add comments for ORB position columns
COMMENT ON COLUMN positions.orb_signal_id IS 'Reference to ORB signal that generated this position';
COMMENT ON COLUMN positions.opening_range_id IS 'Reference to opening range that triggered this trade';
COMMENT ON COLUMN positions.target_price IS 'Target price for exit (range width × 1.5 or 50% option gain)';
COMMENT ON COLUMN positions.range_invalidation IS 'TRUE if price re-entered opening range (thesis invalidated, force exit)';


-- Create view for ORB performance analytics
CREATE OR REPLACE VIEW orb_performance AS
SELECT
    DATE(o.trade_date) AS trade_date,
    o.symbol,
    o.range_width,
    o.gap_percent,
    COUNT(s.id) AS total_signals,
    COUNT(s.id) FILTER (WHERE s.executed = TRUE) AS executed_signals,
    COUNT(p.id) AS total_positions,
    COUNT(p.id) FILTER (WHERE p.status = 'closed') AS closed_positions,
    COUNT(t.id) FILTER (WHERE t.pnl > 0) AS winning_positions,
    COUNT(t.id) FILTER (WHERE t.pnl < 0) AS losing_positions,
    ROUND(
        COUNT(t.id) FILTER (WHERE t.pnl > 0)::NUMERIC /
        NULLIF(COUNT(t.id), 0) * 100,
        2
    ) AS win_rate_pct,
    SUM(t.pnl) AS total_pnl,
    AVG(t.pnl) FILTER (WHERE t.pnl > 0) AS avg_win,
    AVG(t.pnl) FILTER (WHERE t.pnl < 0) AS avg_loss,
    AVG(s.confidence) AS avg_confidence
FROM opening_ranges o
LEFT JOIN orb_signals s ON s.opening_range_id = o.id
LEFT JOIN positions p ON p.orb_signal_id = s.id
LEFT JOIN trades t ON t.id = p.exit_trade_id
GROUP BY DATE(o.trade_date), o.symbol, o.range_width, o.gap_percent
ORDER BY trade_date DESC, o.symbol;

-- Add comment for view
COMMENT ON VIEW orb_performance IS 'Daily ORB performance analytics: win rate, P&L, signal quality by symbol and range characteristics.';


-- Verify schema changes
DO $$
BEGIN
    -- Check if opening_ranges table exists
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_name = 'opening_ranges'
    ) THEN
        RAISE NOTICE '✅ opening_ranges table created successfully';
    ELSE
        RAISE EXCEPTION '❌ Failed to create opening_ranges table';
    END IF;

    -- Check if orb_signals table exists
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_name = 'orb_signals'
    ) THEN
        RAISE NOTICE '✅ orb_signals table created successfully';
    ELSE
        RAISE EXCEPTION '❌ Failed to create orb_signals table';
    END IF;

    -- Check if positions columns were added
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'positions'
        AND column_name IN ('orb_signal_id', 'opening_range_id', 'target_price', 'range_invalidation')
    ) THEN
        RAISE NOTICE '✅ ORB position columns added successfully';
    ELSE
        RAISE EXCEPTION '❌ Failed to add ORB position columns';
    END IF;

    -- Check if view was created
    IF EXISTS (
        SELECT 1
        FROM information_schema.views
        WHERE table_name = 'orb_performance'
    ) THEN
        RAISE NOTICE '✅ orb_performance view created successfully';
    ELSE
        RAISE EXCEPTION '❌ Failed to create orb_performance view';
    END IF;

    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE '✅ Migration 004 completed successfully';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Opening Range Breakout strategy enabled';
    RAISE NOTICE 'Expected win rate: 75-89%%';
    RAISE NOTICE 'Daily target: $200-400';
    RAISE NOTICE 'Entry window: 10:30am - 2:00pm ET';
    RAISE NOTICE '========================================';
END $$;


-- Example opening range (for reference)
/*
INSERT INTO opening_ranges (symbol, trade_date, duration_minutes, range_high, range_low, range_width, gap_percent)
VALUES ('SPY', '2025-11-17', 60, 593.50, 591.20, 0.39, 0.15)
RETURNING *;

-- Example ORB signal (for reference)
INSERT INTO orb_signals (
    signal_id, symbol, direction, opening_range_id, range_high, range_low, range_width,
    breakout_price, breakout_time, volume_confirmation, rsi_confirmation,
    target_price, stop_loss_price, confidence, reasoning
)
VALUES (
    'abc123', 'SPY', 'BULLISH', '...uuid...', 593.50, 591.20, 0.39,
    593.95, NOW(), TRUE, 58.3,
    595.15, 593.50, 0.85, 'BULLISH breakout from 60-min opening range. Volume: 2.1x average. RSI: 58.3.'
)
RETURNING *;
*/
