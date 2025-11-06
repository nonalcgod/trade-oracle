# Database Migration Instructions - Multi-Leg Position Support

**Migration ID**: 002
**Date**: November 6, 2025
**Status**: ⚠️ **PENDING USER ACTION**
**Estimated Time**: 2 minutes

---

## Overview

This migration adds support for multi-leg options positions (iron condors, spreads, straddles, strangles) to the Trade Oracle database. It's **backward compatible** - existing single-leg positions will continue to work without modification.

## What This Migration Does

Adds 4 new columns to the `positions` table:
- `legs` (JSONB): Stores array of individual option legs
- `net_credit` (Numeric): Net credit received or debit paid
- `max_loss` (Numeric): Maximum loss per position
- `spread_width` (Numeric): Width of spread in dollars

All columns are **nullable with defaults** - won't break existing data.

---

## Prerequisites

✅ You have Supabase project access
✅ You have the SQL Editor open in Supabase dashboard
✅ The backend code has been deployed to Railway (commit 325b874)

---

## Step-by-Step Instructions

### 1. Open Supabase SQL Editor

1. Go to https://supabase.com/dashboard
2. Select your Trade Oracle project
3. Click **SQL Editor** in the left sidebar
4. Click **New query**

### 2. Copy Migration SQL

The migration SQL is located at:
```
/Users/joshuajames/Projects/trade-oracle/backend/migrations/002_multi_leg_positions.sql
```

Or copy from below:

```sql
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
```

### 3. Execute Migration

1. Paste the SQL into the Supabase SQL Editor
2. Click **Run** (or press `Ctrl/Cmd + Enter`)
3. Wait for execution to complete (~2 seconds)

### 4. Verify Success

You should see in the Results panel:
```
✅ Multi-leg position columns added successfully
```

If you see an error instead, **STOP** and share the error message.

---

## Post-Migration Verification

Run these queries to verify the migration:

### Check New Columns Exist
```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'positions'
AND column_name IN ('legs', 'net_credit', 'max_loss', 'spread_width');
```

**Expected Result**: 4 rows showing the new columns

### Check Indexes Were Created
```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'positions'
AND indexname LIKE '%legs%';
```

**Expected Result**: 2 indexes (`idx_positions_strategy_legs`, `idx_positions_legs_not_null`)

### Verify Existing Data Unaffected
```sql
SELECT COUNT(*) as existing_positions
FROM positions
WHERE legs IS NULL;
```

**Expected Result**: Same count as before migration (all existing positions still have `legs = NULL`)

---

## Rollback (If Needed)

If you need to undo this migration:

```sql
-- Remove indexes
DROP INDEX IF EXISTS idx_positions_strategy_legs;
DROP INDEX IF EXISTS idx_positions_legs_not_null;

-- Remove columns
ALTER TABLE positions DROP COLUMN IF EXISTS legs;
ALTER TABLE positions DROP COLUMN IF EXISTS net_credit;
ALTER TABLE positions DROP COLUMN IF EXISTS max_loss;
ALTER TABLE positions DROP COLUMN IF EXISTS spread_width;
```

**⚠️ WARNING**: This will delete all iron condor position data!

---

## What Happens After Migration

Once applied, the backend can:

✅ Store iron condor positions with all 4 legs
✅ Track net credit and max loss for multi-leg trades
✅ Query positions by strategy type efficiently
✅ Display iron condor details in frontend

**Existing single-leg positions**: Continue working with `legs = NULL`

---

## Example Data Structure

After migration, an iron condor position looks like:

```json
{
  "id": 123,
  "symbol": "iron_condor_SPY_20251219",
  "strategy": "iron_condor",
  "position_type": "spread",
  "quantity": 1,
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
```

---

## Support

If you encounter any issues:
1. Share the exact error message from Supabase
2. Check `backend/migrations/002_multi_leg_positions.sql` exists
3. Verify you have ALTER TABLE permissions in Supabase

---

**Migration prepared by**: Claude Code
**Git commit**: 325b874
**Railway deployment**: ✅ Live
**Vercel deployment**: ✅ Live

**Next Step**: Apply this migration to enable iron condor functionality!
