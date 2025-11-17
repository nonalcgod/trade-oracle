"""
Position Monitor - Background Task

Monitors open positions every 60 seconds and automatically exits
when conditions are met (profit target, stop loss, DTE, earnings).

Supports multiple strategies:
- IV Mean Reversion (single-leg options)
- 0DTE Iron Condor (multi-leg spreads)
- 0DTE Momentum Scalping (single-leg with 11:30am force close)
- Opening Range Breakout (single-leg with range invalidation + 3pm force close)
- Earnings Straddles (coming soon)
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
        import pytz
        from datetime import time

        # Route to appropriate strategy checker
        if strategy_name.lower() == "momentum_scalping" or "momentum" in strategy_name.lower():
            # Momentum scalping: force close at 11:30am ET
            eastern = pytz.timezone('US/Eastern')
            now_et = datetime.now(eastern).time()
            momentum_force_close_time = time(11, 30)  # 11:30am ET

            if now_et >= momentum_force_close_time:
                return "11:30am force close (momentum scalping - avoid lunch decay)"

            # Also check 3:50pm final force close
            final_force_close_time = time(15, 50)  # 3:50pm ET
            if now_et >= final_force_close_time:
                return "3:50pm force close (final market close - gamma risk)"

            # Check 50% profit target (exit 100%)
            if position.current_price and position.entry_price:
                pnl_pct = (float(position.current_price) - float(position.entry_price)) / float(position.entry_price)
                if pnl_pct >= 0.50:
                    return f"50% profit target reached ({pnl_pct*100:.1f}%)"

            # Check 50% stop loss
            if position.current_price and position.entry_price:
                pnl_pct = (float(position.current_price) - float(position.entry_price)) / float(position.entry_price)
                if pnl_pct <= -0.50:
                    return f"50% stop loss hit ({pnl_pct*100:.1f}%)"

            return None  # No exit conditions met

        elif strategy_name.lower() == "iron_condor" or "condor" in strategy_name.lower():
            # Check iron condor exit conditions
            from api.execution import get_latest_tick
            import pytz
            from datetime import time

            # Validate position has legs data
            if not position.legs or len(position.legs) < 4:
                logger.warning("Iron condor position missing legs data",
                             position_id=position.id,
                             legs_count=len(position.legs) if position.legs else 0)
                return None

            # Fetch current prices for all 4 legs
            leg_values = []
            for leg_data in position.legs:
                tick = await get_latest_tick(leg_data['symbol'])
                if not tick:
                    logger.warning("Cannot get tick for leg",
                                 symbol=leg_data['symbol'],
                                 position_id=position.id)
                    return None

                current_price = (tick.bid + tick.ask) / 2

                # Calculate leg value contribution
                # Sell legs: negative (we owe money to close)
                # Buy legs: positive (we receive money to close)
                if leg_data['side'] == 'sell':
                    leg_value = -(float(current_price) * leg_data['quantity'] * 100)
                else:  # buy
                    leg_value = float(current_price) * leg_data['quantity'] * 100

                leg_values.append(leg_value)

            # Sum all leg values to get net cost to close position
            current_position_value = abs(sum(leg_values))

            # Original credit received (entry_price stores net credit)
            entry_credit = float(position.entry_price) * position.quantity * 100

            # P&L = Credit Received - Cost to Close
            pnl = entry_credit - current_position_value
            pnl_pct = (pnl / entry_credit) if entry_credit > 0 else 0

            logger.debug("Iron condor P&L calculated",
                        position_id=position.id,
                        entry_credit=entry_credit,
                        current_value=current_position_value,
                        pnl=pnl,
                        pnl_pct=pnl_pct)

            # Exit condition 1: 50% profit target
            if pnl_pct >= 0.50:
                return f"50% profit target reached ({pnl_pct*100:.1f}%)"

            # Exit condition 2: 2x credit stop loss
            if pnl <= -(entry_credit * 2):
                return f"2x credit stop loss hit (${pnl:.2f} loss)"

            # Exit condition 3: 3:50pm ET force close
            eastern = pytz.timezone('US/Eastern')
            now_et = datetime.now(eastern).time()
            force_close_time = time(15, 50)  # 3:50pm ET

            if now_et >= force_close_time:
                return "3:50pm force close (10min before market close)"

            # Exit condition 4: Breach detection (2% buffer)
            # Extract underlying symbol from first leg
            first_leg_symbol = position.legs[0]['symbol']
            underlying_symbol = first_leg_symbol[:first_leg_symbol.index(next(filter(str.isdigit, first_leg_symbol)))]

            # Get underlying price
            underlying_tick = await get_latest_tick(underlying_symbol)
            if underlying_tick:
                underlying_price = (underlying_tick.bid + underlying_tick.ask) / 2

                # Identify short strikes (legs 0 and 2 are typically short call/put)
                short_call_strike = None
                short_put_strike = None

                for leg_data in position.legs:
                    if leg_data['side'] == 'sell':
                        if leg_data['option_type'] == 'call':
                            short_call_strike = leg_data['strike']
                        elif leg_data['option_type'] == 'put':
                            short_put_strike = leg_data['strike']

                # Check 2% breach buffer
                if short_call_strike:
                    call_distance = (short_call_strike - float(underlying_price)) / float(underlying_price)
                    if call_distance <= 0.02:
                        return f"Price breached call strike (distance: {call_distance*100:.1f}%)"

                if short_put_strike:
                    put_distance = (float(underlying_price) - short_put_strike) / float(underlying_price)
                    if put_distance <= 0.02:
                        return f"Price breached put strike (distance: {put_distance*100:.1f}%)"

            return None  # No exit conditions met

        elif strategy_name.lower() == "opening_range_breakout" or "orb" in strategy_name.lower():
            # Opening Range Breakout strategy exit conditions
            from api.execution import get_latest_tick
            import pytz
            from datetime import time

            # Get current underlying price
            # Extract underlying symbol (e.g., "SPY" from "SPY251217C00600000")
            option_symbol = position.symbol
            underlying_symbol = option_symbol[:option_symbol.index(next(filter(str.isdigit, option_symbol)))]

            underlying_tick = await get_latest_tick(underlying_symbol)
            if not underlying_tick:
                logger.warning("Cannot get underlying price for ORB exit check",
                             symbol=underlying_symbol,
                             position_id=position.id)
                return None

            underlying_price = (underlying_tick.bid + underlying_tick.ask) / 2

            # Exit condition 1: Range invalidation (price re-enters opening range)
            # Range boundaries stored in signal_data when position was created
            if hasattr(position, 'signal_data') and position.signal_data:
                range_high = position.signal_data.get('range_high')
                range_low = position.signal_data.get('range_low')
                direction = position.signal_data.get('direction')

                if range_high and range_low:
                    # Check if price re-entered range (thesis invalidation)
                    if direction == "BULLISH":
                        # For bullish breakout, price should stay above range_high
                        if underlying_price <= range_high:
                            return f"Range invalidation: price re-entered range (${underlying_price:.2f} below ${range_high:.2f})"
                    elif direction == "BEARISH":
                        # For bearish breakout, price should stay below range_low
                        if underlying_price >= range_low:
                            return f"Range invalidation: price re-entered range (${underlying_price:.2f} above ${range_low:.2f})"

            # Exit condition 2: Option profit targets (50% gain) or stop loss (40% loss)
            if position.current_price and position.entry_price:
                pnl_pct = (float(position.current_price) - float(position.entry_price)) / float(position.entry_price)

                # 50% profit target
                if pnl_pct >= 0.50:
                    return f"50% profit target reached ({pnl_pct*100:.1f}%)"

                # 40% stop loss
                if pnl_pct <= -0.40:
                    return f"40% stop loss hit ({pnl_pct*100:.1f}%)"

            # Exit condition 3: Target price reached (range width × 1.5)
            if hasattr(position, 'signal_data') and position.signal_data:
                target_price = position.signal_data.get('target_price')
                direction = position.signal_data.get('direction')

                if target_price:
                    if direction == "BULLISH" and underlying_price >= target_price:
                        return f"Target price reached (${underlying_price:.2f} >= ${target_price:.2f})"
                    elif direction == "BEARISH" and underlying_price <= target_price:
                        return f"Target price reached (${underlying_price:.2f} <= ${target_price:.2f})"

            # Exit condition 4: 3:00pm ET force close (ORB-specific, earlier than other 0DTE)
            eastern = pytz.timezone('US/Eastern')
            now_et = datetime.now(eastern).time()
            orb_force_close_time = time(15, 0)  # 3:00pm ET

            if now_et >= orb_force_close_time:
                return "3:00pm force close (ORB time exit - sufficient time for execution)"

            return None  # No exit conditions met

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
