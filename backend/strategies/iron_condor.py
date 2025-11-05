"""
Iron Condor Strategy (0DTE)

Sells OTM call spread and OTM put spread simultaneously for credit.
Targets 0DTE (same-day expiration) for high theta decay.

Entry:
- 9:31am ET (market open)
- Find 0.15 delta strikes (ITM probability ~15%)
- Collect ~$0.50-$1.00 credit per spread ($1.00-$2.00 total)

Exit:
- 50% profit target (e.g., $1.00 credit → close at $0.50)
- 2x stop loss (e.g., $1.00 credit → stop at $3.00 loss)
- 3:50pm ET force close (10min before market close)
- Breach detection (price approaches short strike)

Risk:
- Max loss = (width - credit) per side
- Width typically $5 for SPY/QQQ
"""

from decimal import Decimal
from datetime import datetime, time, timedelta
from typing import Optional, List, Tuple
import pytz
import structlog
from alpaca.data import OptionHistoricalDataClient, StockHistoricalDataClient
from alpaca.data.requests import OptionChainRequest, StockLatestQuoteRequest

from models.strategies import (
    IronCondorSetup,
    IronCondorSignal,
    IronCondorExitConditions,
    OptionLeg,
    MultiLegOrder
)

logger = structlog.get_logger()

# Market hours (Eastern Time)
EASTERN = pytz.timezone('US/Eastern')
MARKET_OPEN = time(9, 31)  # 9:31am ET
FORCE_CLOSE_TIME = time(15, 50)  # 3:50pm ET

# Strike selection parameters
TARGET_DELTA = Decimal('0.15')  # 15% ITM probability
DELTA_TOLERANCE = Decimal('0.05')  # Accept 0.10-0.20 delta

# Spread parameters
SPREAD_WIDTH = Decimal('5.00')  # $5 wide spreads for SPY/QQQ
MIN_CREDIT = Decimal('0.50')  # Minimum $0.50 credit per spread
TARGET_CREDIT_TOTAL = Decimal('1.00')  # Target $1.00-$2.00 total

# Exit parameters
PROFIT_TARGET_PCT = Decimal('0.50')  # Close at 50% profit
STOP_LOSS_MULTIPLE = Decimal('2.0')  # Stop at 2x credit loss
BREACH_BUFFER_PCT = Decimal('0.02')  # Close if price within 2% of short strike


class IronCondorStrategy:
    """0DTE Iron Condor strategy implementation"""

    def __init__(
        self,
        option_data_client: OptionHistoricalDataClient,
        stock_data_client: StockHistoricalDataClient
    ):
        self.option_client = option_data_client
        self.stock_client = stock_data_client

    async def should_enter_now(self) -> bool:
        """
        Check if current time is within entry window

        Returns:
            True if should consider entering iron condor
        """
        now_et = datetime.now(EASTERN).time()

        # Entry window: 9:31am - 9:45am ET (first 15 minutes)
        entry_start = MARKET_OPEN
        entry_end = time(9, 45)

        return entry_start <= now_et <= entry_end

    async def find_strike_by_delta(
        self,
        underlying: str,
        expiration: datetime,
        option_type: str,  # "call" or "put"
        target_delta: Decimal,
        underlying_price: Decimal
    ) -> Optional[Decimal]:
        """
        Find option strike closest to target delta

        Args:
            underlying: Underlying symbol (SPY, QQQ)
            expiration: Expiration date
            option_type: "call" or "put"
            target_delta: Target delta (e.g., 0.15)
            underlying_price: Current underlying price

        Returns:
            Strike price or None if not found
        """
        try:
            # Get option chain
            request = OptionChainRequest(
                underlying_symbol=underlying,
                expiration_date=expiration.date()
            )

            chain = self.option_client.get_option_chain(request)

            if not chain:
                logger.warning("Empty option chain", underlying=underlying)
                return None

            # Filter by option type
            options = [opt for opt in chain if opt.type.lower() == option_type]

            # Find strike closest to target delta
            best_strike = None
            best_delta_diff = Decimal('999')

            for option in options:
                if not option.greeks or not option.greeks.delta:
                    continue

                delta = abs(Decimal(str(option.greeks.delta)))
                delta_diff = abs(delta - target_delta)

                if delta_diff < best_delta_diff:
                    best_delta_diff = delta_diff
                    best_strike = Decimal(str(option.strike_price))

            if best_delta_diff > DELTA_TOLERANCE:
                logger.warning("No strike within delta tolerance",
                             target_delta=float(target_delta),
                             best_delta_diff=float(best_delta_diff))
                return None

            logger.info("Found strike by delta",
                       underlying=underlying,
                       option_type=option_type,
                       strike=float(best_strike),
                       delta_diff=float(best_delta_diff))

            return best_strike

        except Exception as e:
            logger.error("Failed to find strike by delta",
                        underlying=underlying,
                        error=str(e))
            return None

    async def get_current_price(self, symbol: str) -> Optional[Decimal]:
        """
        Get current price for underlying or option

        Args:
            symbol: Stock or option symbol

        Returns:
            Current mid price or None
        """
        try:
            # Check if option symbol (contains digits and C/P)
            if any(char.isdigit() for char in symbol) and ('C' in symbol or 'P' in symbol):
                # Option - would need option quote (not implemented yet)
                # For now, return None and require explicit pricing
                return None
            else:
                # Stock
                request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
                quote = self.stock_client.get_stock_latest_quote(request)

                if quote and symbol in quote:
                    bid = Decimal(str(quote[symbol].bid_price))
                    ask = Decimal(str(quote[symbol].ask_price))
                    return (bid + ask) / 2

                return None

        except Exception as e:
            logger.error("Failed to get current price", symbol=symbol, error=str(e))
            return None

    async def build_iron_condor(
        self,
        underlying: str,
        expiration: datetime,
        quantity: int = 1
    ) -> Optional[IronCondorSetup]:
        """
        Build iron condor setup with strike selection

        Args:
            underlying: Underlying symbol (SPY, QQQ)
            expiration: Expiration date (0DTE)
            quantity: Number of iron condors (default 1)

        Returns:
            IronCondorSetup with all strikes and pricing, or None if failed
        """
        try:
            # Get underlying price
            underlying_price = await self.get_current_price(underlying)
            if not underlying_price:
                logger.error("Cannot get underlying price", symbol=underlying)
                return None

            logger.info("Building iron condor",
                       underlying=underlying,
                       price=float(underlying_price),
                       expiration=expiration.date())

            # Find call strikes (above current price)
            short_call_strike = await self.find_strike_by_delta(
                underlying, expiration, "call", TARGET_DELTA, underlying_price
            )

            if not short_call_strike:
                logger.error("Cannot find short call strike")
                return None

            long_call_strike = short_call_strike + SPREAD_WIDTH

            # Find put strikes (below current price)
            short_put_strike = await self.find_strike_by_delta(
                underlying, expiration, "put", TARGET_DELTA, underlying_price
            )

            if not short_put_strike:
                logger.error("Cannot find short put strike")
                return None

            long_put_strike = short_put_strike - SPREAD_WIDTH

            # Calculate credits (placeholder - need actual option quotes)
            # In production, fetch actual bid/ask for each option
            call_spread_credit = MIN_CREDIT  # Placeholder
            put_spread_credit = MIN_CREDIT   # Placeholder
            total_credit = call_spread_credit + put_spread_credit

            # Calculate risk metrics
            max_profit = total_credit * quantity
            max_loss_per_side = (SPREAD_WIDTH - total_credit) * quantity

            # Days to expiration
            dte = (expiration - datetime.now()).days

            # Create setup
            setup = IronCondorSetup(
                underlying_symbol=underlying,
                short_call_strike=short_call_strike,
                long_call_strike=long_call_strike,
                short_put_strike=short_put_strike,
                long_put_strike=long_put_strike,
                quantity=quantity,
                call_spread_credit=call_spread_credit,
                put_spread_credit=put_spread_credit,
                total_credit=total_credit,
                max_profit=max_profit,
                max_loss_per_side=max_loss_per_side,
                expiration=expiration,
                dte=dte,
                entry_time=datetime.utcnow(),
                underlying_price_at_entry=underlying_price
            )

            logger.info("Iron condor built",
                       call_spread=f"{short_call_strike}/{long_call_strike}",
                       put_spread=f"{short_put_strike}/{long_put_strike}",
                       total_credit=float(total_credit))

            return setup

        except Exception as e:
            logger.error("Failed to build iron condor", error=str(e))
            return None

    def create_multi_leg_order(self, setup: IronCondorSetup) -> MultiLegOrder:
        """
        Convert IronCondorSetup to MultiLegOrder for execution

        Args:
            setup: Configured iron condor

        Returns:
            MultiLegOrder with all 4 legs
        """
        # Build OCC option symbols
        # Format: SYMBOL YYMMDD C/P STRIKE (8 digits)
        expiration_str = setup.expiration.strftime("%y%m%d")

        def format_strike(strike: Decimal) -> str:
            """Format strike as 8-digit string (e.g., 600.00 → 00600000)"""
            return f"{int(strike * 1000):08d}"

        symbol_base = setup.underlying_symbol

        # Create 4 legs
        legs = [
            # Leg 1: Sell short call
            OptionLeg(
                symbol=f"{symbol_base}{expiration_str}C{format_strike(setup.short_call_strike)}",
                side="sell",
                quantity=setup.quantity,
                option_type="call",
                strike=setup.short_call_strike,
                expiration=setup.expiration,
                limit_price=setup.call_spread_credit / 2  # Half of spread credit
            ),

            # Leg 2: Buy long call (protection)
            OptionLeg(
                symbol=f"{symbol_base}{expiration_str}C{format_strike(setup.long_call_strike)}",
                side="buy",
                quantity=setup.quantity,
                option_type="call",
                strike=setup.long_call_strike,
                expiration=setup.expiration,
                limit_price=setup.call_spread_credit / 4  # Estimate
            ),

            # Leg 3: Sell short put
            OptionLeg(
                symbol=f"{symbol_base}{expiration_str}P{format_strike(setup.short_put_strike)}",
                side="sell",
                quantity=setup.quantity,
                option_type="put",
                strike=setup.short_put_strike,
                expiration=setup.expiration,
                limit_price=setup.put_spread_credit / 2
            ),

            # Leg 4: Buy long put (protection)
            OptionLeg(
                symbol=f"{symbol_base}{expiration_str}P{format_strike(setup.long_put_strike)}",
                side="buy",
                quantity=setup.quantity,
                option_type="put",
                strike=setup.long_put_strike,
                expiration=setup.expiration,
                limit_price=setup.put_spread_credit / 4
            )
        ]

        return MultiLegOrder(
            strategy_type="iron_condor",
            legs=legs,
            net_credit=setup.total_credit,
            max_profit=setup.max_profit,
            max_loss=setup.max_loss_per_side * 2  # Both sides
        )

    async def check_exit_conditions(
        self,
        setup: IronCondorSetup,
        current_value: Decimal
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if iron condor should be exited

        Args:
            setup: Original iron condor setup
            current_value: Current market value of the position

        Returns:
            (should_exit, reason)
        """
        try:
            # Exit condition 1: Profit target (50% of max profit)
            profit = setup.total_credit - current_value
            profit_pct = profit / setup.total_credit if setup.total_credit > 0 else 0

            if profit_pct >= PROFIT_TARGET_PCT:
                return True, f"50% profit target reached ({float(profit_pct * 100):.1f}%)"

            # Exit condition 2: Stop loss (2x credit)
            loss = current_value - setup.total_credit
            if loss >= setup.total_credit * STOP_LOSS_MULTIPLE:
                return True, f"2x stop loss hit (${float(loss):.2f} loss)"

            # Exit condition 3: Time-based close (3:50pm ET)
            now_et = datetime.now(EASTERN).time()
            if now_et >= FORCE_CLOSE_TIME:
                return True, "3:50pm force close (10min before market close)"

            # Exit condition 4: Breach detection
            underlying_price = await self.get_current_price(setup.underlying_symbol)
            if underlying_price:
                # Check call side
                call_distance = (setup.short_call_strike - underlying_price) / underlying_price
                if call_distance <= BREACH_BUFFER_PCT:
                    return True, f"Price breached call strike buffer ({float(call_distance * 100):.1f}%)"

                # Check put side
                put_distance = (underlying_price - setup.short_put_strike) / underlying_price
                if put_distance <= BREACH_BUFFER_PCT:
                    return True, f"Price breached put strike buffer ({float(put_distance * 100):.1f}%)"

            return False, None

        except Exception as e:
            logger.error("Failed to check exit conditions", error=str(e))
            return False, None

    async def generate_signal(
        self,
        underlying: str,
        expiration: datetime,
        quantity: int = 1
    ) -> Optional[IronCondorSignal]:
        """
        Generate iron condor entry signal

        Args:
            underlying: Underlying symbol (SPY, QQQ)
            expiration: Expiration date (0DTE)
            quantity: Number of iron condors

        Returns:
            IronCondorSignal if conditions met, None otherwise
        """
        try:
            # Check entry time
            if not await self.should_enter_now():
                logger.debug("Not in entry window")
                return None

            # Build iron condor
            setup = await self.build_iron_condor(underlying, expiration, quantity)
            if not setup:
                return None

            # Validate minimum credit
            if setup.total_credit < MIN_CREDIT * 2:
                logger.warning("Credit too low",
                             credit=float(setup.total_credit),
                             min_credit=float(MIN_CREDIT * 2))
                return None

            # Generate signal
            signal = IronCondorSignal(
                action="open",
                setup=setup,
                timestamp=datetime.utcnow()
            )

            logger.info("Iron condor signal generated",
                       underlying=underlying,
                       credit=float(setup.total_credit),
                       call_spread=f"{setup.short_call_strike}/{setup.long_call_strike}",
                       put_spread=f"{setup.short_put_strike}/{setup.long_put_strike}")

            return signal

        except Exception as e:
            logger.error("Failed to generate iron condor signal", error=str(e))
            return None
