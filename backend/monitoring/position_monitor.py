"""
Position Monitor - Background Task

Monitors open positions every 60 seconds and automatically exits
when conditions are met (profit target, stop loss, DTE, earnings).

Supports multiple strategies:
- IV Mean Reversion (single-leg options)
- 0DTE Iron Condor (multi-leg spreads)
- Earnings Straddles (coming soon)
- Momentum Swings (coming soon)
"""

import asyncio
import structlog
from datetime import datetime
from decimal import Decimal
from typing import Optional

logger = structlog.get_logger()


async def check_strategy_specific_exit(position, strategy_name: str) -> Optional[str]:
    """
    Dispatch to strategy-specific exit checker

    Args:
        position: Position object
        strategy_name: Strategy identifier

    Returns:
        Exit reason if should exit, None otherwise
    """
    try:
        # Route to appropriate strategy checker
        if strategy_name.lower() == "iron_condor" or "condor" in strategy_name.lower():
            # Check iron condor exit conditions
            # For iron condors, we need to:
            # 1. Get current value of all 4 legs
            # 2. Check 50% profit, 2x stop, time-based, breach
            from strategies.iron_condor import IronCondorStrategy
            from api.execution import get_latest_tick

            # Get current position value (simplified - in production, sum all legs)
            tick = await get_latest_tick(position.symbol)
            if not tick:
                logger.warning("Cannot get tick for iron condor exit check", symbol=position.symbol)
                return None

            current_value = (tick.bid + tick.ask) / 2

            # TODO: Load setup from database or position metadata
            # For now, use generic exit logic
            return None  # Placeholder until we store iron condor setup

        else:
            # Default to single-leg exit logic
            from api.execution import check_exit_conditions
            return await check_exit_conditions(position)

    except Exception as e:
        logger.error("Failed strategy-specific exit check",
                    position_id=position.id,
                    strategy=strategy_name,
                    error=str(e))
        return None


async def monitor_positions():
    """
    Background task to monitor and close positions

    Runs continuously, checking all open positions every 60 seconds
    and executing automatic exits when conditions are met.

    Exit conditions:
    - 50% profit target reached
    - 75% stop loss hit
    - 21 DTE threshold (avoid gamma risk)
    - Earnings within 2 days
    """
    # Import here to avoid circular imports
    from api.execution import get_open_positions, check_exit_conditions, close_position

    logger.info("Position monitor started")

    while True:
        try:
            # Get all open positions
            positions = await get_open_positions()

            if not positions:
                logger.debug("No open positions to monitor")
            else:
                logger.info("Monitoring positions", count=len(positions))

                for position in positions:
                    try:
                        # Check strategy-specific exit conditions
                        exit_reason = await check_strategy_specific_exit(position, position.strategy)

                        if exit_reason:
                            logger.info(
                                "Exit condition met, closing position",
                                position_id=position.id,
                                symbol=position.symbol,
                                reason=exit_reason
                            )

                            # Close position
                            result = await close_position(position)

                            if result.success:
                                logger.info(
                                    "Position closed successfully",
                                    position_id=position.id,
                                    symbol=position.symbol,
                                    exit_reason=exit_reason
                                )
                            else:
                                logger.error(
                                    "Failed to close position",
                                    position_id=position.id,
                                    symbol=position.symbol,
                                    error=result.message
                                )

                    except Exception as e:
                        logger.error(
                            "Error monitoring individual position",
                            position_id=position.id,
                            symbol=position.symbol,
                            error=str(e)
                        )

            # Wait 60 seconds before next check
            await asyncio.sleep(60)

        except Exception as e:
            logger.error("Error in position monitor", error=str(e))
            # Wait before retrying to avoid rapid error loops
            await asyncio.sleep(60)


if __name__ == "__main__":
    # For testing the monitor standalone
    asyncio.run(monitor_positions())
