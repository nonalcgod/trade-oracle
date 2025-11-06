-- Cleanup Phantom Positions
-- These positions exist in database but not in Alpaca
-- Caused by bug where orders were assumed filled before verification

-- Mark phantom positions as closed
UPDATE positions
SET
  status = 'closed',
  closed_at = NOW(),
  exit_reason = 'Phantom position - order never filled in Alpaca'
WHERE
  symbol = 'SPY251219C00600000'
  AND status = 'open'
  AND id IN (1, 2);

-- Verify update
SELECT
  id,
  symbol,
  status,
  exit_reason,
  opened_at,
  closed_at
FROM positions
WHERE symbol = 'SPY251219C00600000'
ORDER BY id;
