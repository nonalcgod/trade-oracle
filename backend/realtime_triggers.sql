-- Supabase Real-Time Triggers
-- Execute these in Supabase SQL Editor to enable push notifications
-- Expected Impact: Sub-second updates to frontend (no more 5s polling)

-- ============================================================================
-- ENABLE REAL-TIME FOR TABLES
-- ============================================================================

-- Enable Real-Time replication for our tables
ALTER PUBLICATION supabase_realtime ADD TABLE positions;
ALTER PUBLICATION supabase_realtime ADD TABLE trades;
ALTER PUBLICATION supabase_realtime ADD TABLE portfolio_snapshots;

-- ============================================================================
-- POSITION CHANGE NOTIFICATIONS
-- ============================================================================

-- Trigger function to notify clients when positions change
CREATE OR REPLACE FUNCTION notify_position_change()
RETURNS TRIGGER AS $$
BEGIN
  -- Calculate P&L percentage for easy filtering
  DECLARE
    pnl_pct NUMERIC;
  BEGIN
    IF NEW.entry_price > 0 AND NEW.current_price IS NOT NULL THEN
      pnl_pct := ((NEW.current_price - NEW.entry_price) / NEW.entry_price) * 100;
    ELSE
      pnl_pct := 0;
    END IF;

    -- Send notification via PostgreSQL NOTIFY
    PERFORM pg_notify(
      'position_updates',
      json_build_object(
        'operation', TG_OP,
        'position_id', NEW.id,
        'symbol', NEW.symbol,
        'status', NEW.status,
        'entry_price', NEW.entry_price,
        'current_price', NEW.current_price,
        'unrealized_pnl', NEW.unrealized_pnl,
        'pnl_percent', pnl_pct,
        'opened_at', NEW.opened_at,
        'closed_at', NEW.closed_at,
        'exit_reason', NEW.exit_reason
      )::text
    );
  END;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to positions table
DROP TRIGGER IF EXISTS position_change_trigger ON positions;
CREATE TRIGGER position_change_trigger
  AFTER INSERT OR UPDATE ON positions
  FOR EACH ROW
  EXECUTE FUNCTION notify_position_change();

-- ============================================================================
-- TRADE EXECUTION NOTIFICATIONS
-- ============================================================================

-- Trigger function for trade notifications
CREATE OR REPLACE FUNCTION notify_trade_executed()
RETURNS TRIGGER AS $$
BEGIN
  PERFORM pg_notify(
    'trade_updates',
    json_build_object(
      'operation', TG_OP,
      'trade_id', NEW.id,
      'symbol', NEW.symbol,
      'strategy', NEW.strategy,
      'signal_type', NEW.signal_type,
      'entry_price', NEW.entry_price,
      'exit_price', NEW.exit_price,
      'quantity', NEW.quantity,
      'pnl', NEW.pnl,
      'commission', NEW.commission,
      'timestamp', NEW.timestamp
    )::text
  );

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to trades table
DROP TRIGGER IF EXISTS trade_executed_trigger ON trades;
CREATE TRIGGER trade_executed_trigger
  AFTER INSERT ON trades
  FOR EACH ROW
  EXECUTE FUNCTION notify_trade_executed();

-- ============================================================================
-- PORTFOLIO UPDATE NOTIFICATIONS
-- ============================================================================

-- Trigger function for portfolio updates
CREATE OR REPLACE FUNCTION notify_portfolio_update()
RETURNS TRIGGER AS $$
BEGIN
  PERFORM pg_notify(
    'portfolio_updates',
    json_build_object(
      'balance', NEW.balance,
      'daily_pnl', NEW.daily_pnl,
      'win_rate', NEW.win_rate,
      'consecutive_losses', NEW.consecutive_losses,
      'delta', NEW.delta,
      'theta', NEW.theta,
      'active_positions', NEW.active_positions,
      'timestamp', NEW.timestamp
    )::text
  );

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to portfolio_snapshots table
DROP TRIGGER IF EXISTS portfolio_update_trigger ON portfolio_snapshots;
CREATE TRIGGER portfolio_update_trigger
  AFTER INSERT OR UPDATE ON portfolio_snapshots
  FOR EACH ROW
  EXECUTE FUNCTION notify_portfolio_update();

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Check that triggers are installed
SELECT
  trigger_name,
  event_manipulation,
  event_object_table
FROM information_schema.triggers
WHERE trigger_schema = 'public'
  AND trigger_name IN (
    'position_change_trigger',
    'trade_executed_trigger',
    'portfolio_update_trigger'
  )
ORDER BY event_object_table, trigger_name;

-- Expected output:
-- position_change_trigger | INSERT OR UPDATE | positions
-- trade_executed_trigger  | INSERT           | trades
-- portfolio_update_trigger | INSERT OR UPDATE | portfolio_snapshots

-- ============================================================================
-- TEST REAL-TIME UPDATES
-- ============================================================================

-- Test by updating a position (if any exist)
-- UPDATE positions SET current_price = current_price + 0.01 WHERE id = 1;

-- You should see a notification in your frontend if subscribed to the channel
