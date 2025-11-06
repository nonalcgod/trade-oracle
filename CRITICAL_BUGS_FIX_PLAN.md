# Critical Backend Bugs - Detailed Fix Plan

**Generated**: 2025-11-05
**Status**: Ready for Implementation
**Estimated Total Effort**: 6-8 hours

This document provides detailed fixes for the 8 critical bugs identified in the comprehensive backend audit. Each fix includes exact file locations, current problematic code, detailed explanations, complete fixed code, test cases, and effort estimates.

---

## Bug #1: OCC Symbol Parsing Vulnerability

**Severity**: CRITICAL 🔴
**File**: `backend/strategies/iron_condor.py`
**Lines**: 131-134
**Priority**: P0 (Blocks production deployment)
**Effort**: 30 minutes

### Current Problematic Code

```python
# Line 131-134 in find_strike_by_delta()
if 'C0' in symbol and option_type == 'call':
    options.append(opt)
elif 'P0' in symbol and option_type == 'put':
    options.append(opt)
```

### Problem Explanation

The current implementation uses substring matching (`'C0' in symbol`) which creates false positives:

**False Positive Examples**:
- `QQQ251205C00640000` → Correctly identified as call
- `ABC0251205P00640000` → **FALSE POSITIVE** (underlying "ABC0" contains "C0")
- `XYZ251205C00100000` → **FALSE POSITIVE** (strike "00100000" contains "C0")

This bug causes incorrect strike selection, leading to mismatched iron condor legs and potential catastrophic losses.

### Root Cause

OCC option symbol format: `UNDERLYING + YYMMDD + C/P + STRIKE`
- The option type indicator (C or P) is **always at position [len(underlying) + 6]**
- Substring matching fails because "C0" or "P0" can appear anywhere in the symbol

### Complete Fix

```python
# backend/strategies/iron_condor.py
# Lines 121-134 (replace entire option filtering block)

# Filter by option type using proper OCC symbol parsing
options = []
for opt in chain.values():
    symbol = opt.symbol

    # Parse OCC symbol format: UNDERLYING + YYMMDD + C/P + STRIKE (8 digits)
    # Find where digits start (beginning of date)
    date_start_idx = next(
        (i for i, char in enumerate(symbol) if char.isdigit()),
        None
    )

    if date_start_idx is None:
        logger.warning("Cannot parse option symbol", symbol=symbol)
        continue

    # Option type is at position: date_start + 6 (after YYMMDD)
    option_type_idx = date_start_idx + 6

    if option_type_idx >= len(symbol):
        logger.warning("Invalid option symbol length", symbol=symbol)
        continue

    symbol_option_type = symbol[option_type_idx]

    # Match option type
    if symbol_option_type == 'C' and option_type == 'call':
        options.append(opt)
    elif symbol_option_type == 'P' and option_type == 'put':
        options.append(opt)
```

### Test Cases

**Test File**: `backend/tests/test_iron_condor_parsing.py`

```python
import pytest
from decimal import Decimal
from datetime import datetime
from strategies.iron_condor import IronCondorStrategy

@pytest.mark.asyncio
async def test_occ_symbol_parsing_accuracy():
    """Verify option type parsing handles edge cases"""

    # Valid symbols
    assert parse_option_type("SPY251205C00600000") == "call"
    assert parse_option_type("QQQ251205P00640000") == "put"

    # Edge case: underlying with "C0" substring
    assert parse_option_type("ABC0251205P00100000") == "put"  # NOT call!

    # Edge case: strike with "P0" substring
    assert parse_option_type("SPY251205C00500000") == "call"  # NOT put!

    # Edge case: 4-letter underlying
    assert parse_option_type("TSLA251205C00250000") == "call"

    # Edge case: 1-letter underlying
    assert parse_option_type("A251205P00150000") == "put"

@pytest.mark.asyncio
async def test_iron_condor_strike_selection_no_false_positives():
    """Integration test: iron condor builder doesn't mix up legs"""

    # Mock option chain with tricky symbols
    mock_chain = {
        "ABC0251205C00100000": create_mock_option("call", Decimal("100"), delta=0.15),
        "ABC0251205P00090000": create_mock_option("put", Decimal("90"), delta=-0.15),
        # ... add more test symbols
    }

    strategy = IronCondorStrategy(mock_option_client, mock_stock_client)
    setup = await strategy.build_iron_condor("ABC0", datetime(2025, 12, 5), 1)

    # Verify all strikes are correct type
    assert setup.short_call_strike > setup.underlying_price_at_entry  # Call above
    assert setup.short_put_strike < setup.underlying_price_at_entry   # Put below
```

### Verification Steps

1. Deploy fix to Railway staging
2. Call `/api/iron-condor/build` with symbol "ABC0" (if available)
3. Verify logs show correct call/put separation
4. Run pytest suite: `pytest backend/tests/test_iron_condor_parsing.py -v`
5. Monitor Railway logs for "Cannot parse option symbol" warnings

---

## Bug #2: Placeholder Credit Values

**Severity**: CRITICAL 🔴
**File**: `backend/strategies/iron_condor.py`
**Lines**: 261-265
**Priority**: P0 (Blocks production deployment)
**Effort**: 2 hours

### Current Problematic Code

```python
# Line 261-265 in build_iron_condor()
# Calculate credits (placeholder - need actual option quotes)
# In production, fetch actual bid/ask for each option
call_spread_credit = MIN_CREDIT  # Placeholder
put_spread_credit = MIN_CREDIT   # Placeholder
total_credit = call_spread_credit + put_spread_credit
```

### Problem Explanation

The iron condor builder uses **hardcoded $0.50 credits** instead of real market quotes:
- **Risk**: Positions may enter with incorrect profit/loss expectations
- **Impact**: Max loss calculations are wrong, risk management approvals are invalid
- **Real-world scenario**: If actual credit is $0.30 but system assumes $0.50, the trade is immediately underwater by $20/contract ($0.20 × 100)

### Root Cause

The `get_option_chain()` API returns Greeks but not live bid/ask prices. We need to:
1. Fetch latest quotes for each strike using `OptionLatestQuoteRequest`
2. Calculate net credit: (short call bid + short put bid) - (long call ask + long put ask)

### Complete Fix

```python
# backend/strategies/iron_condor.py
# Lines 238-298 (replace credit calculation section)

async def build_iron_condor(
    self,
    underlying: str,
    expiration: datetime,
    quantity: int = 1
) -> Optional[IronCondorSetup]:
    """Build iron condor setup with strike selection"""
    try:
        # ... [previous code unchanged until line 259] ...

        long_put_strike = short_put_strike - SPREAD_WIDTH

        # ===== NEW: Fetch real-time option quotes for all 4 legs =====
        from alpaca.data.requests import OptionLatestQuoteRequest

        # Build OCC symbols for all 4 legs
        exp_str = expiration.strftime("%y%m%d")

        def format_occ_symbol(und: str, exp: str, opt_type: str, strike: Decimal) -> str:
            """Format OCC symbol: UNDERLYING + YYMMDD + C/P + STRIKE (8 digits)"""
            strike_str = f"{int(strike * 1000):08d}"
            return f"{und}{exp}{opt_type}{strike_str}"

        short_call_symbol = format_occ_symbol(underlying, exp_str, "C", short_call_strike)
        long_call_symbol = format_occ_symbol(underlying, exp_str, "C", long_call_strike)
        short_put_symbol = format_occ_symbol(underlying, exp_str, "P", short_put_strike)
        long_put_symbol = format_occ_symbol(underlying, exp_str, "P", long_put_strike)

        # Fetch quotes for all legs
        try:
            quote_request = OptionLatestQuoteRequest(
                symbol_or_symbols=[
                    short_call_symbol,
                    long_call_symbol,
                    short_put_symbol,
                    long_put_symbol
                ]
            )
            quotes = self.option_client.get_option_latest_quote(quote_request)

            # Extract bid/ask for each leg
            short_call_bid = Decimal(str(quotes[short_call_symbol].bid_price)) if short_call_symbol in quotes else Decimal('0')
            long_call_ask = Decimal(str(quotes[long_call_symbol].ask_price)) if long_call_symbol in quotes else Decimal('0')
            short_put_bid = Decimal(str(quotes[short_put_symbol].bid_price)) if short_put_symbol in quotes else Decimal('0')
            long_put_ask = Decimal(str(quotes[long_put_symbol].ask_price)) if long_put_symbol in quotes else Decimal('0')

            # Calculate net credits
            # Call spread credit = Sell short call (bid) - Buy long call (ask)
            call_spread_credit = short_call_bid - long_call_ask

            # Put spread credit = Sell short put (bid) - Buy long put (ask)
            put_spread_credit = short_put_bid - long_put_ask

            # Total credit (should be positive for credit spread)
            total_credit = call_spread_credit + put_spread_credit

            # Validate credits are positive and above minimum
            if call_spread_credit <= 0 or put_spread_credit <= 0:
                logger.error("Invalid credit spread - negative or zero credit",
                           call_credit=float(call_spread_credit),
                           put_credit=float(put_spread_credit))
                return None

            if total_credit < MIN_CREDIT * 2:
                logger.warning("Total credit below minimum threshold",
                             total_credit=float(total_credit),
                             min_required=float(MIN_CREDIT * 2))
                return None

            logger.info("Real-time credits calculated",
                       call_credit=float(call_spread_credit),
                       put_credit=float(put_spread_credit),
                       total_credit=float(total_credit))

        except Exception as e:
            logger.error("Failed to fetch option quotes", error=str(e))
            # Fail safe: do not build iron condor without real quotes
            return None

        # Calculate risk metrics with real credits
        max_profit = total_credit * quantity * 100  # Per contract × 100 multiplier
        max_loss_per_side = (SPREAD_WIDTH - total_credit / 2) * quantity * 100

        # ... [rest of function unchanged] ...
```

### Test Cases

**Test File**: `backend/tests/test_iron_condor_credits.py`

```python
import pytest
from decimal import Decimal
from datetime import datetime
from strategies.iron_condor import IronCondorStrategy

@pytest.mark.asyncio
async def test_real_credit_calculation():
    """Verify iron condor uses real market quotes, not placeholders"""

    # Mock option client returning real quotes
    mock_quotes = {
        "SPY251205C00610000": Mock(bid_price=2.50, ask_price=2.55),  # Short call
        "SPY251205C00615000": Mock(bid_price=1.00, ask_price=1.05),  # Long call
        "SPY251205P00590000": Mock(bid_price=2.45, ask_price=2.50),  # Short put
        "SPY251205P00585000": Mock(bid_price=0.95, ask_price=1.00),  # Long put
    }

    strategy = IronCondorStrategy(mock_option_client, mock_stock_client)
    setup = await strategy.build_iron_condor("SPY", datetime(2025, 12, 5), 1)

    # Expected credits
    # Call spread: 2.50 (short bid) - 1.05 (long ask) = $1.45
    # Put spread: 2.45 (short bid) - 1.00 (long ask) = $1.45
    # Total: $2.90

    assert setup.call_spread_credit == Decimal("1.45")
    assert setup.put_spread_credit == Decimal("1.45")
    assert setup.total_credit == Decimal("2.90")
    assert setup.max_profit == Decimal("290.00")  # $2.90 × 1 contract × 100

@pytest.mark.asyncio
async def test_reject_negative_credit():
    """Iron condor should reject debit spreads (negative credit)"""

    # Mock quotes where long leg is more expensive (debit spread)
    mock_quotes = {
        "SPY251205C00610000": Mock(bid_price=1.00, ask_price=1.05),
        "SPY251205C00615000": Mock(bid_price=2.50, ask_price=2.55),  # Inverted!
        # ...
    }

    strategy = IronCondorStrategy(mock_option_client, mock_stock_client)
    setup = await strategy.build_iron_condor("SPY", datetime(2025, 12, 5), 1)

    assert setup is None  # Should reject
```

### Verification Steps

1. Deploy fix to Railway
2. Monitor logs during market hours (9:31-9:45am ET)
3. Call `/api/iron-condor/build` with SPY or QQQ
4. Verify response contains non-placeholder credits:
   ```json
   {
     "call_spread_credit": 1.23,  // NOT 0.50
     "put_spread_credit": 1.34,   // NOT 0.50
     "total_credit": 2.57         // NOT 1.00
   }
   ```
5. Check Railway logs for "Real-time credits calculated" message

---

## Bug #3: Multi-Leg Race Condition

**Severity**: HIGH 🟠
**File**: `backend/api/execution.py`
**Lines**: 772-819
**Priority**: P0 (Data integrity risk)
**Effort**: 1.5 hours

### Current Problematic Code

```python
# Lines 772-819 in place_multi_leg_order()
# For now, submit legs sequentially
all_legs_filled = []
total_cost = Decimal('0')

for leg in multi_leg.legs:
    # Determine order side
    side = OrderSide.BUY if leg.side == "buy" else OrderSide.SELL

    # Create limit order for this leg
    limit_price = float(leg.limit_price) if leg.limit_price else None

    # ... submit order ...

    order = trading_client.submit_order(order_request)

    # ... continue to next leg ...
```

### Problem Explanation

**Race Condition Scenario**:
1. Leg 1 (short call) fills at $2.50
2. Leg 2 (long call) **FAILS** due to insufficient margin
3. Leg 3 (short put) fills at $2.45
4. Leg 4 (long put) **FAILS** due to Alpaca rate limit

**Result**: Position in database shows "open" iron condor, but only 2 of 4 legs executed. The position is naked and exposed to unlimited risk.

**Database State**:
```sql
positions:
  id: 123
  status: 'open'
  legs: [{leg1}, {leg2}, {leg3}, {leg4}]  -- All marked as filled!

trades:
  id: 456
  symbol: 'iron_condor_SPY'
  -- No indication of partial fill
```

### Root Cause

1. **No atomic transaction**: Legs submitted one-by-one without rollback
2. **No validation**: Position created before verifying all legs filled
3. **No state tracking**: Database doesn't track which legs actually executed

### Complete Fix

```python
# backend/api/execution.py
# Lines 754-866 (replace entire place_multi_leg_order function)

async def place_multi_leg_order(multi_leg: MultiLegOrder) -> OrderResponse:
    """
    Place a multi-leg options order with atomic execution guarantees

    Strategy:
    1. Submit all legs as limit orders
    2. Wait for all fills or timeout
    3. If any leg fails, cancel all pending and close filled legs
    4. Only create position record if all legs successfully filled

    Args:
        multi_leg: MultiLegOrder with all legs configured

    Returns:
        OrderResponse with execution details
    """
    try:
        if not trading_client:
            raise HTTPException(status_code=500, detail="Trading client not initialized")

        logger.info("Starting multi-leg order execution",
                   strategy=multi_leg.strategy_type,
                   legs=len(multi_leg.legs))

        # Phase 1: Submit all leg orders
        submitted_orders = []

        for i, leg in enumerate(multi_leg.legs):
            try:
                side = OrderSide.BUY if leg.side == "buy" else OrderSide.SELL
                limit_price = float(leg.limit_price) if leg.limit_price else None

                if not limit_price:
                    raise ValueError(f"Limit price required for leg {i+1}/{len(multi_leg.legs)}: {leg.symbol}")

                order_request = LimitOrderRequest(
                    symbol=leg.symbol,
                    qty=leg.quantity,
                    side=side,
                    time_in_force=TimeInForce.DAY,
                    limit_price=limit_price
                )

                order = trading_client.submit_order(order_request)

                submitted_orders.append({
                    "leg_index": i,
                    "symbol": leg.symbol,
                    "side": leg.side,
                    "quantity": leg.quantity,
                    "limit_price": leg.limit_price,
                    "order_id": str(order.id),
                    "order": order,
                    "filled": False,
                    "actual_price": None
                })

                logger.info("Multi-leg order leg submitted",
                           leg=f"{i+1}/{len(multi_leg.legs)}",
                           symbol=leg.symbol,
                           side=side.value,
                           order_id=order.id)

                # Brief delay to avoid rate limiting (50ms)
                await asyncio.sleep(0.05)

            except Exception as e:
                logger.error("Failed to submit leg",
                           leg=f"{i+1}/{len(multi_leg.legs)}",
                           symbol=leg.symbol,
                           error=str(e))

                # Rollback: Cancel all previously submitted orders
                await _cancel_orders(submitted_orders)

                return OrderResponse(
                    success=False,
                    message=f"Failed to submit leg {i+1}: {str(e)}"
                )

        # Phase 2: Wait for all fills (timeout: 30 seconds)
        import time
        timeout = 30
        start_time = time.time()

        while time.time() - start_time < timeout:
            all_filled = True

            for submitted in submitted_orders:
                if not submitted["filled"]:
                    try:
                        # Check order status
                        order_status = trading_client.get_order_by_id(submitted["order_id"])

                        if order_status.status == "filled":
                            submitted["filled"] = True
                            submitted["actual_price"] = Decimal(str(order_status.filled_avg_price))
                            logger.info("Leg filled",
                                       symbol=submitted["symbol"],
                                       price=float(submitted["actual_price"]))
                        elif order_status.status in ["canceled", "rejected", "expired"]:
                            logger.error("Leg order failed",
                                       symbol=submitted["symbol"],
                                       status=order_status.status)

                            # Rollback: Cancel pending, close filled
                            await _rollback_multi_leg_order(submitted_orders, trading_client)

                            return OrderResponse(
                                success=False,
                                message=f"Leg {submitted['leg_index']+1} {order_status.status}"
                            )
                        else:
                            all_filled = False

                    except Exception as e:
                        logger.error("Failed to check order status",
                                   order_id=submitted["order_id"],
                                   error=str(e))
                        all_filled = False

            if all_filled:
                break

            await asyncio.sleep(1)  # Poll every second

        # Phase 3: Verify all legs filled
        if not all(s["filled"] for s in submitted_orders):
            logger.error("Multi-leg order timeout - not all legs filled")

            # Rollback: Cancel pending, close filled
            await _rollback_multi_leg_order(submitted_orders, trading_client)

            return OrderResponse(
                success=False,
                message="Order timeout: not all legs filled within 30 seconds"
            )

        # Phase 4: Calculate execution details
        total_cost = Decimal('0')
        for i, leg in enumerate(multi_leg.legs):
            actual_price = submitted_orders[i]["actual_price"]

            if leg.side == "sell":
                total_cost -= actual_price * leg.quantity * 100
            else:  # buy
                total_cost += actual_price * leg.quantity * 100

        total_contracts = sum(leg.quantity for leg in multi_leg.legs)
        commission = Decimal('0.65') * total_contracts

        first_leg = multi_leg.legs[0]
        execution = Execution(
            symbol=f"{multi_leg.strategy_type}_{first_leg.symbol[:3]}",
            quantity=first_leg.quantity,
            entry_price=abs(total_cost / (first_leg.quantity * 100)),
            commission=commission,
            slippage=Decimal('0'),  # TODO: Calculate from limit vs actual
            timestamp=datetime.utcnow()
        )

        # Phase 5: Log to database (only after successful execution)
        trade_id = await log_multi_leg_trade_to_supabase(execution, multi_leg)

        if trade_id:
            position_id = await create_multi_leg_position(multi_leg, entry_trade_id=trade_id)
            if position_id:
                logger.info("Multi-leg position successfully tracked",
                           position_id=position_id,
                           trade_id=trade_id,
                           strategy=multi_leg.strategy_type,
                           all_legs_filled=True)
            else:
                logger.error("CRITICAL: All legs filled but failed to create position record")

        return OrderResponse(
            success=True,
            execution=execution,
            alpaca_order_id=",".join([s["order_id"] for s in submitted_orders]),
            message=f"Multi-leg {multi_leg.strategy_type} executed: all {len(multi_leg.legs)} legs filled"
        )

    except Exception as e:
        logger.error("Fatal error in multi-leg order execution",
                    strategy=multi_leg.strategy_type,
                    error=str(e))
        return OrderResponse(
            success=False,
            message=f"Multi-leg order failed: {str(e)}"
        )


async def _cancel_orders(submitted_orders: list):
    """Cancel all submitted orders (rollback helper)"""
    for submitted in submitted_orders:
        try:
            trading_client.cancel_order_by_id(submitted["order_id"])
            logger.info("Canceled order (rollback)",
                       order_id=submitted["order_id"],
                       symbol=submitted["symbol"])
        except Exception as e:
            logger.error("Failed to cancel order",
                        order_id=submitted["order_id"],
                        error=str(e))


async def _rollback_multi_leg_order(submitted_orders: list, client):
    """
    Rollback partial multi-leg order:
    1. Cancel all pending orders
    2. Close any filled legs with market orders
    """
    logger.warning("Rolling back multi-leg order")

    for submitted in submitted_orders:
        try:
            if submitted["filled"]:
                # Close filled leg with opposite market order
                opposite_side = OrderSide.SELL if submitted["side"] == "buy" else OrderSide.BUY

                close_request = MarketOrderRequest(
                    symbol=submitted["symbol"],
                    qty=submitted["quantity"],
                    side=opposite_side,
                    time_in_force=TimeInForce.DAY
                )

                close_order = client.submit_order(close_request)
                logger.info("Closed filled leg (rollback)",
                           symbol=submitted["symbol"],
                           close_order_id=close_order.id)
            else:
                # Cancel pending order
                client.cancel_order_by_id(submitted["order_id"])
                logger.info("Canceled pending leg (rollback)",
                           order_id=submitted["order_id"])

        except Exception as e:
            logger.error("CRITICAL: Failed to rollback leg",
                        symbol=submitted["symbol"],
                        error=str(e))
```

### Test Cases

```python
@pytest.mark.asyncio
async def test_multi_leg_atomic_execution():
    """All legs fill or none fill"""

    # Simulate leg 3 failure
    mock_trading_client = Mock()
    mock_trading_client.submit_order.side_effect = [
        Mock(id="order1"),  # Leg 1 success
        Mock(id="order2"),  # Leg 2 success
        Exception("Insufficient margin"),  # Leg 3 failure
        Mock(id="order4")   # Leg 4 never reached
    ]

    result = await place_multi_leg_order(mock_iron_condor)

    assert result.success == False
    assert "Failed to submit leg 3" in result.message
    # Verify rollback called
    assert mock_trading_client.cancel_order_by_id.call_count == 2  # Cancel leg 1 & 2

@pytest.mark.asyncio
async def test_multi_leg_position_only_created_after_all_fills():
    """Position record only created if all legs filled"""

    # Simulate timeout (partial fill)
    mock_trading_client = Mock()
    mock_trading_client.get_order_by_id.return_value = Mock(status="pending")

    result = await place_multi_leg_order(mock_iron_condor)

    assert result.success == False
    # Verify NO position created in database
    positions = await supabase.table("positions").select("*").execute()
    assert len(positions.data) == 0
```

### Verification Steps

1. Add integration test with mock Alpaca API
2. Simulate failure scenarios:
   - Leg 2 rejected
   - Leg 3 timeout
   - Network error after leg 1
3. Verify database integrity:
   - No orphan positions
   - Trades table only has complete multi-leg executions
4. Test rollback: manually cancel leg during execution, verify others cancel

---

## Bug #4: Float Precision Loss

**Severity**: MEDIUM 🟡
**File**: `backend/api/data.py`
**Lines**: 76-89
**Priority**: P1 (Financial accuracy)
**Effort**: 20 minutes

### Current Problematic Code

```python
# Lines 76-89 in log_tick_to_supabase()
data = {
    "timestamp": tick.timestamp.isoformat(),
    "symbol": tick.symbol,
    "underlying_price": float(tick.underlying_price),
    "strike": float(tick.strike),
    "bid": float(tick.bid),
    "ask": float(tick.ask),
    "delta": float(tick.delta),
    "gamma": float(tick.gamma),
    "theta": float(tick.theta),
    "vega": float(tick.vega),
    "iv": float(tick.iv)
}
```

### Problem Explanation

**Precision Loss Example**:
```python
# OptionTick uses Decimal for precision
tick.underlying_price = Decimal("605.12345678")  # 10 decimal places

# Convert to float for database
float(tick.underlying_price) = 605.1234567800001  # IEEE 754 rounding error

# After multiple conversions (read from DB, calculate, write back)
final_value = 605.1234500000  # Lost 3 decimal places
```

**Impact**:
- Options pricing calculations drift over time
- Greeks calculations become inaccurate
- IV rank percentiles shift incorrectly
- **Real-world example**: $0.01 error × 100 multiplier × 1000 contracts = $1,000 P&L error

### Root Cause

Python `Decimal` → `float` conversion loses precision due to IEEE 754 binary representation. Financial data should stay as `Decimal` through entire pipeline.

### Complete Fix

```python
# backend/api/data.py
# Lines 73-93 (replace log_tick_to_supabase function)

async def log_tick_to_supabase(tick: OptionTick):
    """
    Log option tick to Supabase for historical analysis

    Uses str() conversion instead of float() to preserve Decimal precision
    """
    try:
        if supabase:
            data = {
                "timestamp": tick.timestamp.isoformat(),
                "symbol": tick.symbol,
                # Convert Decimal to string to preserve precision
                # Supabase NUMERIC type handles strings correctly
                "underlying_price": str(tick.underlying_price),
                "strike": str(tick.strike),
                "bid": str(tick.bid),
                "ask": str(tick.ask),
                "delta": str(tick.delta),
                "gamma": str(tick.gamma),
                "theta": str(tick.theta),
                "vega": str(tick.vega),
                "iv": str(tick.iv)
            }
            supabase.table("option_ticks").insert(data).execute()
            logger.debug("Logged tick to Supabase",
                        symbol=tick.symbol,
                        precision="decimal")  # Marker for monitoring
    except Exception as e:
        logger.error("Failed to log tick to Supabase", error=str(e), symbol=tick.symbol)
```

**Also update execution.py** (lines 326-337 in `log_trade_to_supabase`):

```python
data = {
    "timestamp": execution.timestamp.isoformat(),
    "symbol": execution.symbol,
    "strategy": signal.strategy,
    "signal_type": signal.signal.value,
    # Use str() instead of float() to preserve Decimal precision
    "entry_price": str(execution.entry_price),
    "exit_price": str(execution.exit_price) if execution.exit_price else None,
    "quantity": execution.quantity,
    "pnl": str(execution.pnl) if execution.pnl else None,
    "commission": str(execution.commission),
    "slippage": str(execution.slippage),
    "reasoning": signal.reasoning
}
```

### Test Cases

```python
import pytest
from decimal import Decimal

def test_decimal_precision_preserved():
    """Verify Decimal precision maintained through database round-trip"""

    # Create tick with high-precision values
    tick = OptionTick(
        symbol="SPY251205C00605123",  # Strike with decimals
        underlying_price=Decimal("605.12345678"),
        strike=Decimal("605.123"),
        bid=Decimal("2.12345678"),
        ask=Decimal("2.14567890"),
        delta=Decimal("0.51234567"),
        # ... other fields
    )

    # Log to database
    await log_tick_to_supabase(tick)

    # Read back from database
    result = supabase.table("option_ticks") \
        .select("*") \
        .eq("symbol", tick.symbol) \
        .order("timestamp", desc=True) \
        .limit(1) \
        .execute()

    row = result.data[0]

    # Verify precision preserved (no float rounding errors)
    assert Decimal(row['underlying_price']) == tick.underlying_price
    assert Decimal(row['bid']) == tick.bid
    assert Decimal(row['delta']) == tick.delta

    # Calculate difference (should be zero)
    diff = abs(Decimal(row['underlying_price']) - tick.underlying_price)
    assert diff == Decimal('0'), f"Precision loss detected: {diff}"

def test_float_conversion_loses_precision():
    """Document the bug: show float() loses precision"""

    original = Decimal("605.12345678")
    via_float = Decimal(str(float(original)))  # Convert to float and back
    via_string = Decimal(original)  # Direct string conversion

    # Float loses precision
    assert via_float != original
    assert abs(via_float - original) > Decimal('0.00000001')

    # String preserves precision
    assert via_string == original
```

### Verification Steps

1. Deploy fix to Railway
2. Seed historical data with high-precision values
3. Calculate IV rank and verify no drift
4. Monitor logs for "precision=decimal" marker
5. Run `SELECT underlying_price, LENGTH(underlying_price::text) FROM option_ticks LIMIT 100` to verify 8+ decimal places stored

---

## Bug #5: Database Position Type Mismatch

**Severity**: MEDIUM 🟡
**File**: `backend/api/execution.py`
**Lines**: 158-193 (create_multi_leg_position)
**Priority**: P1 (Data integrity)
**Effort**: 30 minutes

### Current Problematic Code

```python
# Line 180 in create_multi_leg_position()
"position_type": "spread",  # Generic type for multi-leg positions
```

### Problem Explanation

The `position_type` column is hardcoded to `"spread"` for all multi-leg positions:
- Iron condors → "spread"
- Butterflies → "spread"
- Calendars → "spread"
- Straddles → "spread"

**Issues**:
1. Cannot filter positions by specific strategy type
2. Exit monitoring logic cannot dispatch to strategy-specific checkers
3. Performance analytics cannot segment by strategy
4. Frontend cannot display strategy-specific UI

**Example Query Failure**:
```sql
-- User wants to see only iron condor positions
SELECT * FROM positions WHERE strategy = 'iron_condor' AND position_type = 'spread';
-- Returns: Iron condors, butterflies, calendars all mixed together!
```

### Root Cause

The code uses:
- `strategy` column: Correctly stores "iron_condor", "butterfly", etc.
- `position_type` column: Incorrectly hardcoded to "spread"

The `position_type` should match `strategy` or be removed entirely (redundant).

### Complete Fix

**Option A: Match position_type to strategy** (Recommended)

```python
# backend/api/execution.py
# Lines 158-193 (replace create_multi_leg_position function)

async def create_multi_leg_position(
    multi_leg: MultiLegOrder,
    entry_trade_id: Optional[int] = None
) -> Optional[int]:
    """
    Create a multi-leg position in the database (iron condor, spreads, etc.)

    Args:
        multi_leg: MultiLegOrder with all legs configured
        entry_trade_id: Trade ID from trades table

    Returns:
        Position ID if successful, None otherwise
    """
    try:
        if not supabase:
            logger.warning("Supabase not configured, skipping position tracking")
            return None

        # Prepare legs data for JSONB storage
        legs_data = [
            {
                "symbol": leg.symbol,
                "side": leg.side,
                "option_type": leg.option_type,
                "strike": float(leg.strike),
                "quantity": leg.quantity,
                "entry_price": float(leg.limit_price) if leg.limit_price else None
            }
            for leg in multi_leg.legs
        ]

        # Extract underlying from first leg symbol
        first_symbol = multi_leg.legs[0].symbol
        underlying = first_symbol[:first_symbol.index(next(filter(str.isdigit, first_symbol)))]
        representative_symbol = f"{multi_leg.strategy_type}_{underlying}"

        # Map strategy type to position type
        # FIXED: Use strategy-specific position types instead of generic "spread"
        position_type_map = {
            "iron_condor": "iron_condor",
            "butterfly": "butterfly",
            "calendar": "calendar",
            "straddle": "straddle",
            "strangle": "strangle",
            "vertical_spread": "vertical_spread",
            "diagonal_spread": "diagonal_spread",
        }

        position_type = position_type_map.get(
            multi_leg.strategy_type.lower(),
            "multi_leg"  # Fallback for unknown strategies
        )

        # Prepare position data
        data = {
            "symbol": representative_symbol,
            "strategy": multi_leg.strategy_type,
            "position_type": position_type,  # FIXED: Strategy-specific type
            "quantity": multi_leg.legs[0].quantity,
            "entry_price": float(multi_leg.net_credit) if multi_leg.net_credit else 0.0,
            "entry_trade_id": entry_trade_id,
            "current_price": float(multi_leg.net_credit) if multi_leg.net_credit else 0.0,
            "unrealized_pnl": 0.0,
            "opened_at": datetime.utcnow().isoformat(),
            "status": "open",
            # Multi-leg specific fields
            "legs": legs_data,
            "net_credit": float(multi_leg.net_credit) if multi_leg.net_credit else None,
            "max_loss": float(multi_leg.max_loss) if multi_leg.max_loss else None,
            "spread_width": 5.0  # TODO: Extract from legs dynamically
        }

        response = supabase.table("positions").insert(data).execute()

        if response.data:
            position_id = response.data[0]['id']
            logger.info("Created multi-leg position",
                       position_id=position_id,
                       strategy=multi_leg.strategy_type,
                       position_type=position_type,  # Log for verification
                       legs=len(multi_leg.legs),
                       underlying=underlying)
            return position_id

        return None

    except Exception as e:
        logger.error("Failed to create multi-leg position", error=str(e))
        return None
```

**Option B: Remove position_type column** (Simpler)

```sql
-- Migration: Remove redundant position_type column
ALTER TABLE positions DROP COLUMN position_type;

-- Update all queries to use strategy column instead
-- backend/api/execution.py: get_open_positions()
-- backend/monitoring/position_monitor.py: check_strategy_specific_exit()
```

### Test Cases

```python
@pytest.mark.asyncio
async def test_position_type_matches_strategy():
    """Verify position_type correctly identifies multi-leg strategy"""

    # Create iron condor
    iron_condor = MultiLegOrder(
        strategy_type="iron_condor",
        legs=[...],
        # ...
    )

    position_id = await create_multi_leg_position(iron_condor, trade_id=1)

    # Fetch position
    result = supabase.table("positions").select("*").eq("id", position_id).execute()
    position = result.data[0]

    # Verify position_type matches strategy
    assert position['strategy'] == "iron_condor"
    assert position['position_type'] == "iron_condor"  # NOT "spread"!

    # Verify query filtering works
    iron_condors = supabase.table("positions") \
        .select("*") \
        .eq("position_type", "iron_condor") \
        .execute()

    assert len(iron_condors.data) == 1
    assert iron_condors.data[0]['id'] == position_id
```

### Verification Steps

1. Deploy fix to Railway
2. Create test iron condor position
3. Query database:
   ```sql
   SELECT id, strategy, position_type, legs
   FROM positions
   WHERE status = 'open';
   ```
4. Verify `position_type = 'iron_condor'` (not 'spread')
5. Test monitoring dispatch:
   ```bash
   # Should route to iron condor exit checker
   curl https://trade-oracle-production.up.railway.app/api/testing/check-exit-conditions
   ```

---

## Bug #6: Missing Null Check in Breach Detection

**Severity**: LOW 🟢
**File**: `backend/monitoring/position_monitor.py`
**Lines**: 110-134
**Priority**: P2 (Robustness)
**Effort**: 15 minutes

### Current Problematic Code

```python
# Lines 110-134 in check_strategy_specific_exit()
# Get underlying price
underlying_tick = await get_latest_tick(underlying_symbol)
if underlying_tick:
    underlying_price = (underlying_tick.bid + underlying_tick.ask) / 2

    # Identify short strikes
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
```

### Problem Explanation

**Crash Scenario**:
1. Underlying tick fetch fails (network error, market closed)
2. `underlying_tick` is `None`
3. Code enters `if underlying_tick:` block
4. **BUG**: If underlying fetch succeeds but bid/ask are `None`
   - `underlying_price = (None + None) / 2` → **TypeError**

**Example from Alpaca**:
```python
# During pre-market or post-market
quote = {
    "symbol": "SPY",
    "bid_price": None,  # No bid
    "ask_price": 605.00  # Only ask
}

# Code crashes:
underlying_price = (None + 605.00) / 2  # TypeError: unsupported operand type(s)
```

### Root Cause

Missing null checks for `tick.bid` and `tick.ask` before arithmetic operations.

### Complete Fix

```python
# backend/monitoring/position_monitor.py
# Lines 110-136 (replace breach detection section)

# Exit condition 4: Breach detection (2% buffer)
# Extract underlying symbol from first leg
first_leg_symbol = position.legs[0]['symbol']
underlying_symbol = first_leg_symbol[:first_leg_symbol.index(next(filter(str.isdigit, first_leg_symbol)))]

# Get underlying price
underlying_tick = await get_latest_tick(underlying_symbol)

# FIXED: Add null checks for tick and bid/ask
if underlying_tick and underlying_tick.bid and underlying_tick.ask:
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

    # Check 2% breach buffer (only if strikes found)
    if short_call_strike:
        call_distance = (short_call_strike - float(underlying_price)) / float(underlying_price)
        if call_distance <= 0.02:
            return f"Price breached call strike (distance: {call_distance*100:.1f}%)"

    if short_put_strike:
        put_distance = (float(underlying_price) - short_put_strike) / float(underlying_price)
        if put_distance <= 0.02:
            return f"Price breached put strike (distance: {put_distance*100:.1f}%)"
else:
    # Log warning if cannot check breach condition
    logger.warning("Cannot check breach condition - no underlying tick data",
                  position_id=position.id,
                  underlying_symbol=underlying_symbol,
                  has_tick=bool(underlying_tick),
                  has_bid=bool(underlying_tick.bid) if underlying_tick else False,
                  has_ask=bool(underlying_tick.ask) if underlying_tick else False)

return None  # No exit conditions met
```

### Test Cases

```python
@pytest.mark.asyncio
async def test_breach_detection_handles_none_bid_ask():
    """Monitor doesn't crash when bid/ask are None"""

    # Mock tick with None bid (pre-market scenario)
    mock_tick = Mock(
        symbol="SPY",
        bid=None,
        ask=Decimal("605.00"),
        timestamp=datetime.utcnow()
    )

    # Should not crash, should log warning
    exit_reason = await check_strategy_specific_exit(mock_position, "iron_condor")

    assert exit_reason is None  # Cannot determine breach without bid
    # Verify warning logged
    assert "Cannot check breach condition" in caplog.text

@pytest.mark.asyncio
async def test_breach_detection_during_market_hours():
    """Normal case: both bid and ask available"""

    mock_tick = Mock(
        bid=Decimal("604.50"),
        ask=Decimal("604.60"),
        # ...
    )

    # Position with short call at 605
    mock_position.legs = [
        {"side": "sell", "option_type": "call", "strike": 605.00},
        # ...
    ]

    # Should detect breach (underlying 604.55 within 2% of 605)
    exit_reason = await check_strategy_specific_exit(mock_position, "iron_condor")

    assert exit_reason is not None
    assert "breached call strike" in exit_reason
```

### Verification Steps

1. Deploy fix to Railway
2. Test during pre-market (before 9:30am ET):
   ```bash
   curl https://trade-oracle-production.up.railway.app/api/testing/check-exit-conditions
   ```
3. Verify no crashes in Railway logs
4. Verify warning: "Cannot check breach condition - no underlying tick data"
5. Test during market hours - breach detection should work normally

---

## Bug #7: Paper Trading Key Validation

**Severity**: LOW 🟢
**File**: `backend/api/data.py`
**Lines**: 32-43
**Priority**: P2 (Safety net)
**Effort**: 10 minutes

### Current Problematic Code

```python
# Lines 32-43 in data.py initialization
# CRITICAL: Validate paper trading only
if ALPACA_BASE_URL and "paper-api" not in ALPACA_BASE_URL:
    logger.critical(
        "CRITICAL SAFETY WARNING: ALPACA_BASE_URL should use paper-api.alpaca.markets",
        current_url=ALPACA_BASE_URL
    )

if ALPACA_API_KEY and not ALPACA_API_KEY.startswith("PK"):
    logger.critical(
        "CRITICAL SAFETY WARNING: ALPACA_API_KEY should be a paper trading key (starts with 'PK')",
        current_prefix=ALPACA_API_KEY[:2]
    )
```

### Problem Explanation

**Safety Issue**:
The code **logs a warning** but **does not prevent execution**:
1. User accidentally sets `ALPACA_BASE_URL=https://api.alpaca.markets` (live trading)
2. Warning logged: "CRITICAL SAFETY WARNING..."
3. **System continues running and places live trades**
4. User loses real money

**Current behavior**:
```python
if ALPACA_API_KEY.startswith("SK"):  # Live trading key!
    logger.critical("WARNING! Using live trading key!")
    # ... but execution continues anyway
    trading_client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)  # LIVE TRADES!
```

### Root Cause

Validation is **defensive logging** instead of **fail-fast enforcement**. The system should refuse to start if live trading credentials are detected.

### Complete Fix

```python
# backend/api/data.py
# Lines 27-60 (replace validation and initialization section)

import os
import sys
from typing import Optional
from alpaca.data.historical.option import OptionHistoricalDataClient
from supabase import create_client, Client
import structlog

logger = structlog.get_logger()

# Initialize Alpaca clients
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

# CRITICAL: Enforce paper trading only - FAIL FAST if live credentials detected
def validate_paper_trading_only():
    """
    Validate that only paper trading credentials are configured

    Raises SystemExit if live trading credentials detected
    """
    errors = []

    # Check 1: Base URL must contain "paper-api"
    if ALPACA_BASE_URL and "paper-api" not in ALPACA_BASE_URL:
        errors.append(
            f"❌ ALPACA_BASE_URL uses LIVE trading endpoint: {ALPACA_BASE_URL}\n"
            f"   Must be: https://paper-api.alpaca.markets"
        )

    # Check 2: API key must start with "PK" (paper key prefix)
    if ALPACA_API_KEY:
        if ALPACA_API_KEY.startswith("SK"):
            errors.append(
                f"❌ ALPACA_API_KEY is a LIVE trading key (starts with 'SK')\n"
                f"   Must be: PK... (paper trading key)"
            )
        elif not ALPACA_API_KEY.startswith("PK"):
            errors.append(
                f"❌ ALPACA_API_KEY has unknown prefix: {ALPACA_API_KEY[:2]}\n"
                f"   Expected: PK... (paper trading key)"
            )

    # If any errors, refuse to start
    if errors:
        logger.critical(
            "🚨 CRITICAL SAFETY VIOLATION: Live trading credentials detected!",
            errors=errors
        )

        print("\n" + "="*80)
        print("🚨 CRITICAL SAFETY VIOLATION: LIVE TRADING CREDENTIALS DETECTED!")
        print("="*80)
        for error in errors:
            print(error)
        print("="*80)
        print("\nThis system is configured for PAPER TRADING ONLY.")
        print("Using live trading credentials could result in REAL MONEY LOSS.")
        print("\nFix your environment variables and restart.")
        print("="*80 + "\n")

        # FAIL FAST: Exit immediately
        sys.exit(1)

    # Success: paper trading validated
    logger.info(
        "✅ Paper trading validated",
        api_key_prefix=ALPACA_API_KEY[:2] if ALPACA_API_KEY else "not set",
        base_url=ALPACA_BASE_URL
    )

# Run validation before initializing any clients
validate_paper_trading_only()

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not all([ALPACA_API_KEY, ALPACA_SECRET_KEY, SUPABASE_URL, SUPABASE_KEY]):
    logger.warning("Missing environment variables for data service")

supabase: Optional[Client] = None
option_client: Optional[OptionHistoricalDataClient] = None

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    option_client = OptionHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)
    logger.info("Clients initialized successfully (PAPER TRADING MODE)")
except Exception as e:
    logger.error("Failed to initialize clients", error=str(e))
```

**Also update execution.py** (lines 31-49):

```python
# backend/api/execution.py
# Lines 27-56 (replace validation and initialization section)

# CRITICAL: Validate paper trading API keys
def validate_paper_trading_only():
    """Enforce paper trading only - same implementation as data.py"""
    # ... [copy same validation logic] ...

# Run validation BEFORE initializing trading client
validate_paper_trading_only()

# Initialize Alpaca Trading Client (PAPER TRADING ONLY)
trading_client: Optional[TradingClient] = None
supabase: Optional[Client] = None

try:
    if ALPACA_API_KEY and ALPACA_SECRET_KEY:
        # paper=True ensures we only use paper trading
        trading_client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=True)
        logger.info("Alpaca trading client initialized (PAPER TRADING)")

    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized")
except Exception as e:
    logger.error("Failed to initialize clients", error=str(e))
```

### Test Cases

```python
def test_refuse_live_trading_base_url():
    """System exits if live trading URL detected"""

    # Set live trading URL
    os.environ["ALPACA_BASE_URL"] = "https://api.alpaca.markets"
    os.environ["ALPACA_API_KEY"] = "PKxxxxxx"  # Even with paper key

    # Should raise SystemExit
    with pytest.raises(SystemExit) as exc_info:
        validate_paper_trading_only()

    assert exc_info.value.code == 1
    assert "LIVE trading endpoint" in caplog.text

def test_refuse_live_trading_api_key():
    """System exits if live trading key detected"""

    # Set live trading key (starts with "SK")
    os.environ["ALPACA_API_KEY"] = "SKxxxxxx"
    os.environ["ALPACA_BASE_URL"] = "https://paper-api.alpaca.markets"

    with pytest.raises(SystemExit):
        validate_paper_trading_only()

    assert "LIVE trading key" in caplog.text

def test_accept_paper_trading_credentials():
    """System starts normally with paper trading credentials"""

    os.environ["ALPACA_API_KEY"] = "PKxxxxxx"
    os.environ["ALPACA_BASE_URL"] = "https://paper-api.alpaca.markets"

    # Should not raise
    validate_paper_trading_only()

    assert "Paper trading validated" in caplog.text
```

### Verification Steps

1. Test failure case locally:
   ```bash
   export ALPACA_API_KEY="SKxxxxxx"
   python backend/main.py
   # Should immediately exit with error message
   ```

2. Test success case:
   ```bash
   export ALPACA_API_KEY="PKxxxxxx"
   python backend/main.py
   # Should start normally
   ```

3. Deploy to Railway
4. Verify Railway logs show "✅ Paper trading validated" on startup

---

## Bug #8: Incomplete Option Symbol Parsing

**Severity**: LOW 🟢
**File**: `backend/api/execution.py`
**Lines**: 420-453
**Priority**: P2 (Robustness)
**Effort**: 20 minutes

### Current Problematic Code

```python
# Lines 420-453 in parse_option_symbol()
def parse_option_symbol(symbol: str) -> dict:
    """
    Parse OCC option symbol format: AAPL251219C00150000

    Returns:
        dict with underlying, expiration, option_type, strike
    """
    try:
        # Extract components from OCC format
        underlying = symbol[:symbol.index(str(next(filter(str.isdigit, symbol))))]
        date_start = len(underlying)
        expiration_str = symbol[date_start:date_start+6]
        option_type = symbol[date_start+6]
        strike_str = symbol[date_start+7:]

        # Parse expiration (YYMMDD)
        from datetime import datetime
        year = 2000 + int(expiration_str[:2])
        month = int(expiration_str[2:4])
        day = int(expiration_str[4:6])
        expiration = datetime(year, month, day)

        # Parse strike (8 digits, divide by 1000)
        strike = Decimal(strike_str) / 1000

        return {
            'underlying': underlying,
            'expiration': expiration,
            'option_type': option_type,
            'strike': strike
        }
    except Exception as e:
        logger.error("Failed to parse option symbol", symbol=symbol, error=str(e))
        return {}
```

### Problem Explanation

**Edge Cases Not Handled**:

1. **Invalid strike length**: `symbol[date_start+7:]` assumes exactly 8 digits
   - `SPY251205C0060000` (7 digits) → crash
   - `SPY251205C000600000` (9 digits) → wrong strike

2. **Invalid expiration date**: No validation for impossible dates
   - `SPY251399C00600000` (month 13, day 99) → `ValueError` crash
   - `SPY250229C00600000` (Feb 29 in non-leap year) → crash

3. **Empty return**: Returns `{}` on error, but caller expects all keys
   - `parsed = parse_option_symbol("INVALID")`
   - `parsed['strike']` → `KeyError`

### Root Cause

Parser assumes perfect OCC format with no validation. Real-world data can have:
- Malformed symbols from data providers
- Historical symbols with different formats
- User input errors

### Complete Fix

```python
# backend/api/execution.py
# Lines 420-470 (replace entire parse_option_symbol function)

def parse_option_symbol(symbol: str) -> dict:
    """
    Parse OCC option symbol format with comprehensive validation

    Format: UNDERLYING + YYMMDD + C/P + STRIKE (8 digits)
    Example: AAPL251219C00150000

    Args:
        symbol: OCC option symbol

    Returns:
        dict with 'underlying', 'expiration', 'option_type', 'strike'
        Returns None if parsing fails

    Raises:
        ValueError: If symbol format is invalid
    """
    try:
        # Validate minimum length (shortest: A251205C00100000 = 16 chars)
        if len(symbol) < 16:
            raise ValueError(f"Symbol too short (min 16 chars): {symbol}")

        # Extract underlying (everything before first digit)
        date_start_idx = next(
            (i for i, char in enumerate(symbol) if char.isdigit()),
            None
        )

        if date_start_idx is None or date_start_idx == 0:
            raise ValueError(f"No underlying found in symbol: {symbol}")

        underlying = symbol[:date_start_idx]

        # Extract expiration (YYMMDD - 6 digits)
        expiration_str = symbol[date_start_idx:date_start_idx+6]

        if len(expiration_str) != 6 or not expiration_str.isdigit():
            raise ValueError(f"Invalid expiration format: {expiration_str}")

        # Parse expiration with validation
        from datetime import datetime
        year = 2000 + int(expiration_str[:2])
        month = int(expiration_str[2:4])
        day = int(expiration_str[4:6])

        # Validate month and day ranges
        if not (1 <= month <= 12):
            raise ValueError(f"Invalid month: {month}")
        if not (1 <= day <= 31):
            raise ValueError(f"Invalid day: {day}")

        try:
            expiration = datetime(year, month, day, 16, 0, 0)  # Market close at 4pm
        except ValueError as e:
            raise ValueError(f"Invalid expiration date {year}-{month}-{day}: {e}")

        # Extract option type (C or P)
        option_type_idx = date_start_idx + 6

        if option_type_idx >= len(symbol):
            raise ValueError(f"Symbol too short for option type: {symbol}")

        option_type = symbol[option_type_idx]

        if option_type not in ('C', 'P'):
            raise ValueError(f"Invalid option type: {option_type} (must be C or P)")

        # Extract strike (8 digits after option type)
        strike_str = symbol[option_type_idx+1:]

        if len(strike_str) != 8:
            raise ValueError(f"Invalid strike length: {len(strike_str)} (must be 8 digits)")

        if not strike_str.isdigit():
            raise ValueError(f"Strike contains non-digits: {strike_str}")

        # Parse strike (divide by 1000 for decimal price)
        strike = Decimal(strike_str) / Decimal('1000')

        # Validate strike is reasonable (0.001 to 99,999)
        if strike < Decimal('0.001') or strike > Decimal('99999'):
            raise ValueError(f"Strike out of range: {strike}")

        result = {
            'underlying': underlying,
            'expiration': expiration,
            'option_type': option_type,
            'strike': strike
        }

        logger.debug("Successfully parsed option symbol",
                    symbol=symbol,
                    underlying=underlying,
                    expiration=expiration.date(),
                    option_type=option_type,
                    strike=float(strike))

        return result

    except ValueError as e:
        logger.error("Failed to parse option symbol",
                    symbol=symbol,
                    error=str(e),
                    error_type="ValueError")
        raise  # Re-raise to caller
    except Exception as e:
        logger.error("Unexpected error parsing option symbol",
                    symbol=symbol,
                    error=str(e),
                    error_type=type(e).__name__)
        raise ValueError(f"Failed to parse option symbol: {e}")
```

### Test Cases

```python
import pytest
from decimal import Decimal
from datetime import datetime

def test_parse_valid_occ_symbols():
    """Test various valid OCC symbol formats"""

    # Standard 3-letter underlying
    result = parse_option_symbol("SPY251205C00600000")
    assert result['underlying'] == "SPY"
    assert result['expiration'] == datetime(2025, 12, 5, 16, 0, 0)
    assert result['option_type'] == "C"
    assert result['strike'] == Decimal("600.000")

    # 1-letter underlying
    result = parse_option_symbol("A251205P00150000")
    assert result['underlying'] == "A"
    assert result['strike'] == Decimal("150.000")

    # 4-letter underlying
    result = parse_option_symbol("TSLA251205C00250000")
    assert result['underlying'] == "TSLA"
    assert result['strike'] == Decimal("250.000")

    # 5-letter underlying
    result = parse_option_symbol("AAPL251205P00175500")
    assert result['underlying'] == "AAPL"
    assert result['strike'] == Decimal("175.500")

def test_reject_invalid_symbols():
    """Test validation catches malformed symbols"""

    # Too short
    with pytest.raises(ValueError, match="too short"):
        parse_option_symbol("SPY")

    # Invalid expiration (month 13)
    with pytest.raises(ValueError, match="Invalid month"):
        parse_option_symbol("SPY251305C00600000")

    # Invalid expiration (day 32)
    with pytest.raises(ValueError, match="Invalid day"):
        parse_option_symbol("SPY251232C00600000")

    # Invalid option type
    with pytest.raises(ValueError, match="Invalid option type"):
        parse_option_symbol("SPY251205X00600000")

    # Strike wrong length (7 digits instead of 8)
    with pytest.raises(ValueError, match="Invalid strike length"):
        parse_option_symbol("SPY251205C0060000")

    # Strike contains letters
    with pytest.raises(ValueError, match="non-digits"):
        parse_option_symbol("SPY251205C00600ABC")

    # Strike out of range (negative)
    with pytest.raises(ValueError, match="out of range"):
        parse_option_symbol("SPY251205C99999999")

def test_parse_symbol_integration_with_position():
    """Verify parsed symbols work in position tracking"""

    symbol = "QQQ251219C00640000"
    parsed = parse_option_symbol(symbol)

    # Create position using parsed data
    position = Position(
        symbol=symbol,
        strike=parsed['strike'],
        expiration=parsed['expiration'],
        # ...
    )

    # Verify DTE calculation works
    dte = (parsed['expiration'] - datetime.now()).days
    assert dte > 0
```

### Verification Steps

1. Add unit tests to `backend/tests/test_symbol_parsing.py`
2. Run test suite: `pytest backend/tests/test_symbol_parsing.py -v`
3. Test with real symbols from Alpaca:
   ```bash
   curl "https://trade-oracle-production.up.railway.app/api/data/latest/SPY251205C00600000"
   ```
4. Monitor Railway logs for parse errors:
   ```bash
   railway logs --tail | grep "Failed to parse"
   ```
5. Verify no crashes in position monitor

---

## Implementation Checklist

### Phase 1: Critical Blockers (Day 1)
- [ ] **Bug #1**: OCC symbol parsing vulnerability
- [ ] **Bug #2**: Placeholder credit values
- [ ] **Bug #3**: Multi-leg race condition

**Deployment**: Test individually, then deploy all 3 together

### Phase 2: Data Integrity (Day 2)
- [ ] **Bug #4**: Float precision loss
- [ ] **Bug #5**: Database position type mismatch

**Deployment**: Requires database verification, can deploy together

### Phase 3: Robustness (Day 3)
- [ ] **Bug #6**: Missing null check in breach detection
- [ ] **Bug #7**: Paper trading key validation
- [ ] **Bug #8**: Incomplete option symbol parsing

**Deployment**: Low risk, can deploy all together

### Testing Strategy

1. **Unit Tests**: Write tests for each bug before fixing
2. **Integration Tests**: Test end-to-end iron condor flow
3. **Staging Deployment**: Deploy to Railway staging first
4. **Canary Deployment**: Test with 1 contract during market hours
5. **Production Deployment**: Full rollout after 1-week canary

### Monitoring

After deployment, monitor Railway logs for:
```bash
# Bug #1: Verify correct option type parsing
railway logs --tail | grep "Found strike by delta"

# Bug #2: Verify real credits (not $0.50)
railway logs --tail | grep "Real-time credits calculated"

# Bug #3: Verify atomic execution
railway logs --tail | grep "Multi-leg position successfully tracked"

# Bug #4: Verify decimal precision marker
railway logs --tail | grep "precision=decimal"

# Bug #7: Verify paper trading validation
railway logs --tail | grep "Paper trading validated"
```

### Rollback Plan

If any bug fix causes issues:

1. **Immediate**: Revert to previous Railway deployment
   ```bash
   railway rollback
   ```

2. **Database**: No schema changes required (all fixes are code-only)

3. **Data Integrity**: Run verification query
   ```sql
   -- Check for orphan positions (multi-leg race condition)
   SELECT * FROM positions
   WHERE legs IS NOT NULL
   AND status = 'open'
   AND entry_trade_id NOT IN (SELECT id FROM trades);
   ```

---

## Estimated Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| **Phase 1** | 4 hours | Bugs #1, #2, #3 (critical blockers) |
| **Phase 2** | 1 hour | Bugs #4, #5 (data integrity) |
| **Phase 3** | 1 hour | Bugs #6, #7, #8 (robustness) |
| **Testing** | 1 hour | Unit + integration tests |
| **Deployment** | 1 hour | Staging → canary → production |
| **TOTAL** | **8 hours** | Complete fix implementation |

---

## Success Criteria

✅ All 8 bugs fixed and deployed
✅ 100% test coverage for bug fixes
✅ Zero crashes in position monitor (24hr test)
✅ Iron condor positions tracked correctly in database
✅ Real-time credits displayed (not placeholders)
✅ No partial multi-leg executions
✅ System refuses to start with live trading keys

---

**Next Steps**: Would you like me to:
1. Implement these fixes directly (edit files)
2. Generate Railway deployment fixes as PR
3. Create frontend error boundary + ESLint config
4. Create production readiness checklist
