-- Migration 002: Multi-Leg Position Support
-- Adds support for iron condors, spreads, and other multi-leg strategies
-- Date: November 5, 2025

-- Add multi-leg position columns to positions table
ALTER TABLE positions ADD COLUMN IF NOT EXISTS legs JSONB DEFAULT NULL;
ALTER TABLE positions ADD COLUMN IF NOT EXISTS net_credit NUMERIC(10,4) DEFAULT NULL;
ALTER TABLE positions ADD COLUMN IF NOT EXISTS max_loss NUMERIC(12,2) DEFAULT NULL;
ALTER TABLE positions ADD COLUMN IF NOT EXISTS spread_width NUMERIC(10,2) DEFAULT NULL;

-- Add index for querying multi-leg positions by strategy
CREATE INDEX IF NOT EXISTS idx_positions_strategy_legs ON positions(strategy) WHERE legs IS NOT NULL;

-- Add index for querying positions with legs data
CREATE INDEX IF NOT EXISTS idx_positions_legs_not_null ON positions(id) WHERE legs IS NOT NULL;

-- Update position_type to support new types
COMMENT ON COLUMN positions.position_type IS 'Position type: long, short, spread, iron_condor, straddle, strangle';

-- Add comment for legs column
COMMENT ON COLUMN positions.legs IS 'JSONB array of leg data for multi-leg positions: [{"symbol": "SPY251219C00600000", "side": "sell", "option_type": "call", "strike": 600.00, "quantity": 1, "entry_price": 0.50}]';

-- Add comment for net_credit column
COMMENT ON COLUMN positions.net_credit IS 'Net credit received (for credit spreads) or debit paid (for debit spreads)';

-- Add comment for max_loss column
COMMENT ON COLUMN positions.max_loss IS 'Maximum loss per position (spread width - credit) * quantity * 100';

-- Add comment for spread_width column
COMMENT ON COLUMN positions.spread_width IS 'Width of spread in dollars (e.g., 5.00 for $5 wide spread)';

-- Verify schema changes
DO $$
BEGIN
    -- Check if columns were added successfully
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'positions'
        AND column_name IN ('legs', 'net_credit', 'max_loss', 'spread_width')
    ) THEN
        RAISE NOTICE '✅ Multi-leg position columns added successfully';
    ELSE
        RAISE EXCEPTION '❌ Failed to add multi-leg position columns';
    END IF;
END $$;

-- Example multi-leg position structure (for reference)
/*
{
    "id": 1,
    "symbol": "iron_condor_SPY",
    "strategy": "iron_condor",
    "position_type": "spread",
    "quantity": 1,
    "entry_price": 1.00,  -- Net credit
    "status": "open",
    "legs": [
        {
            "symbol": "SPY251219C00600000",
            "side": "sell",
            "option_type": "call",
            "strike": 600.00,
            "quantity": 1,
            "entry_price": 0.50
        },
        {
            "symbol": "SPY251219C00605000",
            "side": "buy",
            "option_type": "call",
            "strike": 605.00,
            "quantity": 1,
            "entry_price": 0.10
        },
        {
            "symbol": "SPY251219P00590000",
            "side": "sell",
            "option_type": "put",
            "strike": 590.00,
            "quantity": 1,
            "entry_price": 0.50
        },
        {
            "symbol": "SPY251219P00585000",
            "side": "buy",
            "option_type": "put",
            "strike": 585.00,
            "quantity": 1,
            "entry_price": 0.10
        }
    ],
    "net_credit": 1.00,
    "max_loss": 400.00,
    "spread_width": 5.00
}
*/
