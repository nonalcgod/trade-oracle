"""
Supabase Real-Time Service

Provides push-based updates for positions, trades, and portfolio changes.
Eliminates 5-second polling by pushing updates instantly to frontend.

Expected Impact: Sub-second latency for trade notifications
"""

import os
import structlog
from typing import Optional, Callable, Dict, Any
from supabase import create_client, Client

logger = structlog.get_logger()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Initialize Supabase client
supabase: Optional[Client] = None

try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Real-time service initialized")
except Exception as e:
    logger.error("Failed to initialize real-time service", error=str(e))


# ============================================================================
# Real-Time Channel Management
# ============================================================================

class RealtimeChannels:
    """Channel names for different data types"""
    POSITIONS = "position-updates"
    TRADES = "trade-updates"
    PORTFOLIO = "portfolio-updates"
    SYSTEM = "system-updates"


async def broadcast_position_update(position_id: int, position_data: dict):
    """
    Broadcast position update to all connected clients

    Args:
        position_id: Position ID
        position_data: Position data to broadcast
    """
    if not supabase:
        logger.warning("Supabase not configured, skipping broadcast")
        return

    try:
        # Supabase Real-Time automatically broadcasts changes
        # when you update the database. This function is for
        # manual broadcasts if needed.

        channel = supabase.channel(RealtimeChannels.POSITIONS)

        # Broadcast to channel
        await channel.send({
            "type": "broadcast",
            "event": "position_updated",
            "payload": {
                "position_id": position_id,
                "data": position_data
            }
        })

        logger.info("Position update broadcast",
                   position_id=position_id,
                   channel=RealtimeChannels.POSITIONS)

    except Exception as e:
        logger.error("Failed to broadcast position update",
                    position_id=position_id,
                    error=str(e))


async def broadcast_trade_executed(trade_id: int, trade_data: dict):
    """
    Broadcast trade execution to all connected clients

    Args:
        trade_id: Trade ID
        trade_data: Trade data to broadcast
    """
    if not supabase:
        logger.warning("Supabase not configured, skipping broadcast")
        return

    try:
        channel = supabase.channel(RealtimeChannels.TRADES)

        await channel.send({
            "type": "broadcast",
            "event": "trade_executed",
            "payload": {
                "trade_id": trade_id,
                "data": trade_data
            }
        })

        logger.info("Trade execution broadcast",
                   trade_id=trade_id,
                   channel=RealtimeChannels.TRADES)

    except Exception as e:
        logger.error("Failed to broadcast trade execution",
                    trade_id=trade_id,
                    error=str(e))


async def broadcast_portfolio_update(portfolio_data: dict):
    """
    Broadcast portfolio update to all connected clients

    Args:
        portfolio_data: Portfolio state data
    """
    if not supabase:
        logger.warning("Supabase not configured, skipping broadcast")
        return

    try:
        channel = supabase.channel(RealtimeChannels.PORTFOLIO)

        await channel.send({
            "type": "broadcast",
            "event": "portfolio_updated",
            "payload": portfolio_data
        })

        logger.info("Portfolio update broadcast",
                   balance=portfolio_data.get('balance'),
                   channel=RealtimeChannels.PORTFOLIO)

    except Exception as e:
        logger.error("Failed to broadcast portfolio update", error=str(e))


async def broadcast_system_alert(alert_type: str, message: str, level: str = "info"):
    """
    Broadcast system alert to all connected clients

    Args:
        alert_type: Type of alert (circuit_breaker, order_failed, etc.)
        message: Alert message
        level: Alert level (info, warning, critical)
    """
    if not supabase:
        logger.warning("Supabase not configured, skipping broadcast")
        return

    try:
        channel = supabase.channel(RealtimeChannels.SYSTEM)

        await channel.send({
            "type": "broadcast",
            "event": "system_alert",
            "payload": {
                "alert_type": alert_type,
                "message": message,
                "level": level,
                "timestamp": None  # Will be set by Supabase
            }
        })

        logger.info("System alert broadcast",
                   alert_type=alert_type,
                   level=level,
                   channel=RealtimeChannels.SYSTEM)

    except Exception as e:
        logger.error("Failed to broadcast system alert", error=str(e))


# ============================================================================
# Database Triggers for Automatic Broadcasting
# ============================================================================

# These SQL triggers should be applied in Supabase:

REALTIME_TRIGGERS_SQL = """
-- Enable Real-Time for tables
ALTER PUBLICATION supabase_realtime ADD TABLE positions;
ALTER PUBLICATION supabase_realtime ADD TABLE trades;
ALTER PUBLICATION supabase_realtime ADD TABLE portfolio_snapshots;

-- Trigger function to notify clients of position changes
CREATE OR REPLACE FUNCTION notify_position_change()
RETURNS TRIGGER AS $$
BEGIN
  -- Trigger notification
  PERFORM pg_notify(
    'position_updates',
    json_build_object(
      'operation', TG_OP,
      'position_id', NEW.id,
      'symbol', NEW.symbol,
      'status', NEW.status,
      'unrealized_pnl', NEW.unrealized_pnl
    )::text
  );

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to positions table
DROP TRIGGER IF EXISTS position_change_trigger ON positions;
CREATE TRIGGER position_change_trigger
  AFTER INSERT OR UPDATE ON positions
  FOR EACH ROW
  EXECUTE FUNCTION notify_position_change();

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
      'signal_type', NEW.signal_type,
      'pnl', NEW.pnl
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

-- Trigger function for portfolio updates
CREATE OR REPLACE FUNCTION notify_portfolio_update()
RETURNS TRIGGER AS $$
BEGIN
  PERFORM pg_notify(
    'portfolio_updates',
    json_build_object(
      'balance', NEW.balance,
      'daily_pnl', NEW.daily_pnl,
      'active_positions', NEW.active_positions
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
"""

# ============================================================================
# Helper Functions
# ============================================================================

def get_realtime_triggers_sql() -> str:
    """
    Get SQL for creating real-time triggers

    Returns:
        SQL string to execute in Supabase
    """
    return REALTIME_TRIGGERS_SQL


async def test_realtime_broadcast():
    """
    Test real-time broadcasting

    Sends a test message to verify real-time is working
    """
    await broadcast_system_alert(
        alert_type="test",
        message="Real-time broadcasting is working! 🎉",
        level="info"
    )

    logger.info("Real-time broadcast test complete")
