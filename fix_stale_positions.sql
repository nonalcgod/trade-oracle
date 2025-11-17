-- Fix stale positions (Nov 17, 2025)
-- These positions are closed in Alpaca but showing as "open" in database
-- due to the P&L bug where exit_price and pnl were saved as NULL

-- Mark positions 4, 6, 7, 8 as closed
UPDATE positions
SET
    status = 'closed',
    closed_at = '2025-11-12T14:58:28Z',  -- Timestamp from trade 11
    exit_reason = 'automated_exit'
WHERE id IN (4, 6, 7, 8);

-- Verify the update
SELECT
    id,
    symbol,
    status,
    opened_at,
    closed_at,
    exit_trade_id,
    exit_reason
FROM positions
WHERE id IN (4, 6, 7, 8);

-- Show the related trades to understand what happened
SELECT
    id,
    timestamp,
    symbol,
    signal_type,
    entry_price,
    exit_price,
    pnl,
    quantity,
    reasoning
FROM trades
WHERE id IN (5, 6, 7, 8, 9, 10, 11)
ORDER BY id;
