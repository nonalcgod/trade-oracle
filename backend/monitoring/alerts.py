"""
Alerting & Monitoring Infrastructure

Sends alerts for critical events via webhooks (Discord, Slack, etc.)
and tracks system metrics for performance monitoring.
"""

import os
import asyncio
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import structlog
import httpx

logger = structlog.get_logger()

# ============================================================================
# Alert Configuration
# ============================================================================

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# Alert levels
class AlertLevel:
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


# ============================================================================
# Alert Senders
# ============================================================================

async def send_discord_alert(title: str, message: str, level: str = AlertLevel.INFO):
    """
    Send alert to Discord webhook

    Args:
        title: Alert title
        message: Alert message
        level: INFO, WARNING, or CRITICAL
    """
    if not DISCORD_WEBHOOK_URL:
        logger.debug("Discord webhook not configured, skipping alert")
        return False

    try:
        # Color codes for different levels
        colors = {
            AlertLevel.INFO: 3447003,      # Blue
            AlertLevel.WARNING: 16776960,  # Yellow
            AlertLevel.CRITICAL: 15158332  # Red
        }

        payload = {
            "embeds": [{
                "title": f"🤖 Trade Oracle: {title}",
                "description": message,
                "color": colors.get(level, 3447003),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {
                    "text": "Trade Oracle Alert System"
                }
            }]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                DISCORD_WEBHOOK_URL,
                json=payload,
                timeout=10.0
            )

            if response.status_code == 204:
                logger.info("Discord alert sent", title=title, level=level)
                return True
            else:
                logger.error("Discord alert failed",
                           status=response.status_code,
                           response=response.text)
                return False

    except Exception as e:
        logger.error("Failed to send Discord alert", error=str(e))
        return False


async def send_slack_alert(title: str, message: str, level: str = AlertLevel.INFO):
    """
    Send alert to Slack webhook

    Args:
        title: Alert title
        message: Alert message
        level: INFO, WARNING, or CRITICAL
    """
    if not SLACK_WEBHOOK_URL:
        logger.debug("Slack webhook not configured, skipping alert")
        return False

    try:
        # Emoji for different levels
        emojis = {
            AlertLevel.INFO: ":information_source:",
            AlertLevel.WARNING: ":warning:",
            AlertLevel.CRITICAL: ":rotating_light:"
        }

        payload = {
            "text": f"{emojis.get(level, ':robot_face:')} *Trade Oracle Alert*",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": title
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Level:* {level} | *Time:* {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
                        }
                    ]
                }
            ]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                SLACK_WEBHOOK_URL,
                json=payload,
                timeout=10.0
            )

            if response.status_code == 200:
                logger.info("Slack alert sent", title=title, level=level)
                return True
            else:
                logger.error("Slack alert failed",
                           status=response.status_code,
                           response=response.text)
                return False

    except Exception as e:
        logger.error("Failed to send Slack alert", error=str(e))
        return False


async def send_alert(title: str, message: str, level: str = AlertLevel.INFO):
    """
    Send alert to all configured channels

    Args:
        title: Alert title
        message: Alert message
        level: INFO, WARNING, or CRITICAL
    """
    tasks = [
        send_discord_alert(title, message, level),
        send_slack_alert(title, message, level)
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Return True if at least one succeeded
    return any(r is True for r in results)


# ============================================================================
# Predefined Alerts
# ============================================================================

async def alert_circuit_breaker_triggered(reason: str, portfolio_balance: Decimal, daily_pnl: Decimal):
    """Alert when circuit breaker stops trading"""
    message = f"""
**Circuit Breaker Triggered!** 🚨

Trading has been automatically stopped.

**Reason:** {reason}
**Portfolio Balance:** ${float(portfolio_balance):,.2f}
**Daily P&L:** ${float(daily_pnl):,.2f}

All new trades are blocked until conditions improve.
Review your risk management settings.
    """.strip()

    await send_alert(
        title="Circuit Breaker Triggered",
        message=message,
        level=AlertLevel.CRITICAL
    )


async def alert_position_closed(
    symbol: str,
    entry_price: Decimal,
    exit_price: Decimal,
    pnl: Decimal,
    reason: str
):
    """Alert when position is automatically closed"""
    pnl_emoji = "📈" if pnl > 0 else "📉"

    message = f"""
**Position Closed {pnl_emoji}**

**Symbol:** {symbol}
**Entry:** ${float(entry_price):.2f}
**Exit:** ${float(exit_price):.2f}
**P&L:** ${float(pnl):,.2f}
**Reason:** {reason}
    """.strip()

    level = AlertLevel.INFO if pnl > 0 else AlertLevel.WARNING

    await send_alert(
        title=f"Position Closed: {symbol}",
        message=message,
        level=level
    )


async def alert_order_failed(symbol: str, reason: str):
    """Alert when order execution fails"""
    message = f"""
**Order Execution Failed** ❌

**Symbol:** {symbol}
**Reason:** {reason}

Check Alpaca API status and trading hours.
    """.strip()

    await send_alert(
        title="Order Execution Failed",
        message=message,
        level=AlertLevel.WARNING
    )


async def alert_high_consecutive_losses(consecutive_losses: int):
    """Alert approaching consecutive loss limit"""
    message = f"""
**High Consecutive Losses** ⚠️

**Current:** {consecutive_losses} losses
**Limit:** 3 losses

One more loss will trigger the circuit breaker.
    """.strip()

    await send_alert(
        title=f"Consecutive Losses: {consecutive_losses}",
        message=message,
        level=AlertLevel.WARNING
    )


async def alert_position_opened(
    symbol: str,
    quantity: int,
    entry_price: Decimal,
    strategy: str,
    reasoning: str
):
    """Alert when new position is opened"""
    message = f"""
**New Position Opened** 📊

**Symbol:** {symbol}
**Quantity:** {quantity} contracts
**Entry Price:** ${float(entry_price):.2f}
**Strategy:** {strategy}
**Reasoning:** {reasoning}

Monitor: https://trade-oracle-lac.vercel.app
    """.strip()

    await send_alert(
        title=f"Position Opened: {symbol}",
        message=message,
        level=AlertLevel.INFO
    )


async def alert_daily_summary(
    total_trades: int,
    winners: int,
    losers: int,
    daily_pnl: Decimal,
    portfolio_balance: Decimal
):
    """Send daily trading summary"""
    win_rate = (winners / total_trades * 100) if total_trades > 0 else 0

    message = f"""
**Daily Trading Summary** 📊

**Total Trades:** {total_trades}
**Winners:** {winners} | **Losers:** {losers}
**Win Rate:** {win_rate:.1f}%
**Daily P&L:** ${float(daily_pnl):,.2f}
**Portfolio Balance:** ${float(portfolio_balance):,.2f}

Dashboard: https://trade-oracle-lac.vercel.app
    """.strip()

    await send_alert(
        title="Daily Summary",
        message=message,
        level=AlertLevel.INFO
    )


async def alert_api_error(service: str, error_message: str):
    """Alert when external API fails"""
    message = f"""
**API Error** 🚨

**Service:** {service}
**Error:** {error_message}

Check service status and API keys.
    """.strip()

    await send_alert(
        title=f"{service} API Error",
        message=message,
        level=AlertLevel.CRITICAL
    )


# ============================================================================
# Performance Monitoring
# ============================================================================

class PerformanceMonitor:
    """Track system performance metrics"""

    def __init__(self):
        self.metrics: Dict[str, Any] = {}

    def record_api_call(self, endpoint: str, duration_ms: float, status_code: int):
        """Record API call metrics"""
        if endpoint not in self.metrics:
            self.metrics[endpoint] = {
                "calls": 0,
                "total_duration": 0,
                "errors": 0
            }

        self.metrics[endpoint]["calls"] += 1
        self.metrics[endpoint]["total_duration"] += duration_ms

        if status_code >= 400:
            self.metrics[endpoint]["errors"] += 1

    def get_summary(self) -> dict:
        """Get performance summary"""
        summary = {}

        for endpoint, data in self.metrics.items():
            avg_duration = data["total_duration"] / data["calls"] if data["calls"] > 0 else 0
            error_rate = data["errors"] / data["calls"] * 100 if data["calls"] > 0 else 0

            summary[endpoint] = {
                "total_calls": data["calls"],
                "avg_duration_ms": round(avg_duration, 2),
                "error_rate": round(error_rate, 2)
            }

        return summary


# Global monitor instance
performance_monitor = PerformanceMonitor()


# ============================================================================
# Health Check Alerting
# ============================================================================

async def check_system_health():
    """
    Check system health and send alerts if degraded

    Should be called periodically (e.g., every 5 minutes)
    """
    issues = []

    # Check Railway memory usage
    # TODO: Add Railway API integration

    # Check Supabase connection
    try:
        from api.execution import supabase
        if not supabase:
            issues.append("Supabase not connected")
    except:
        issues.append("Supabase connection failed")

    # Check Alpaca connection
    try:
        from api.execution import trading_client
        if not trading_client:
            issues.append("Alpaca not connected")
    except:
        issues.append("Alpaca connection failed")

    if issues:
        message = "**System Health Issues:**\n" + "\n".join(f"• {issue}" for issue in issues)
        await send_alert(
            title="System Health Degraded",
            message=message,
            level=AlertLevel.WARNING
        )


# ============================================================================
# Test Function
# ============================================================================

async def test_alerts():
    """Test alert system"""
    await send_alert(
        title="Alert System Test",
        message="This is a test alert. If you receive this, alerts are working! 🎉",
        level=AlertLevel.INFO
    )
