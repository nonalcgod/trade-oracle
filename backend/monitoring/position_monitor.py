"""
Position Monitor - Background Task

Monitors open positions every 60 seconds and automatically exits
when conditions are met (profit target, stop loss, DTE, earnings).
"""

import asyncio
import structlog
from datetime import datetime

logger = structlog.get_logger()


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
                        # Check exit conditions
                        exit_reason = await check_exit_conditions(position)

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
