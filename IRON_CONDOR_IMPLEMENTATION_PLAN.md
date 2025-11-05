# 0DTE Iron Condor - Implementation Plan & Gap Analysis

**Date**: November 5, 2025
**Status**: ✅ **85% Complete** - Critical Integration Gaps Remain
**Research Document**: `0DTE_IRON_CONDOR_EXPERT_GUIDE.md` (40,000 words, 10+ authoritative sources)

---

## Executive Summary

The 0DTE Iron Condor strategy has been **extensively implemented** with complete strategy logic, API endpoints, and data models. However, **4 critical integration gaps** prevent it from working end-to-end in production:

1. ❌ **Database schema doesn't support multi-leg positions**
2. ❌ **Multi-leg order execution doesn't create positions**
3. ❌ **Position monitor can't calculate spread P&L**
4. ❌ **Frontend has no iron condor UI**

**Estimated Time to Production**: 6-8 hours of focused development

---

## ✅ What's Already Implemented (85% Complete)

### 1. Strategy Module (`backend/strategies/iron_condor.py`)

**Status**: ✅ **Fully Implemented**

**Features**:
- ✅ Delta-based strike selection (0.15 target, ±0.05 tolerance)
- ✅ Time-based entry window (9:31am-9:45am ET)
- ✅ $5 spread width configuration
- ✅ Minimum credit validation ($0.50 per spread)
- ✅ Exit condition checks:
  - 50% profit target
  - 2x credit stop loss
  - 3:50pm force close
  - 2% breach detection

**Key Functions**:
```python
async def should_enter_now() -> bool
async def find_strike_by_delta(...) -> Optional[Decimal]
async def build_iron_condor(...) -> Optional[IronCondorSetup]
def create_multi_leg_order(...) -> MultiLegOrder
async def check_exit_conditions(...) -> Tuple[bool, Optional[str]]
```

**Configuration** (backend/strategies/iron_condor.py:41-58):
```python
TARGET_DELTA = Decimal('0.15')           # 70% success rate
SPREAD_WIDTH = Decimal('5.00')           # $5 wide spreads
MIN_CREDIT = Decimal('0.50')             # $50 per spread minimum
PROFIT_TARGET_PCT = Decimal('0.50')      # 50% profit target
STOP_LOSS_MULTIPLE = Decimal('2.0')      # 2x credit stop loss
BREACH_BUFFER_PCT = Decimal('0.02')      # 2% breach detection
FORCE_CLOSE_TIME = time(15, 50)          # 3:50pm ET
```

---

### 2. API Endpoints (`backend/api/iron_condor.py`)

**Status**: ✅ **Fully Implemented & Registered**

**Routes**:
- ✅ `POST /api/iron-condor/signal` - Generate entry signal
- ✅ `POST /api/iron-condor/build` - Build setup with strike selection
- ✅ `POST /api/iron-condor/check-exit` - Evaluate exit conditions
- ✅ `GET /api/iron-condor/should-enter` - Check entry window
- ✅ `GET /api/iron-condor/health` - Strategy health

**Integration**: Router registered in `backend/main.py:51,59`

**Example Usage**:
```bash
# Check if in entry window
curl https://trade-oracle-production.up.railway.app/api/iron-condor/should-enter

# Build iron condor with automatic strike selection
curl -X POST https://trade-oracle-production.up.railway.app/api/iron-condor/build \
  -H "Content-Type: application/json" \
  -d '{"underlying": "SPY", "quantity": 1}'

# Execute multi-leg order
curl -X POST https://trade-oracle-production.up.railway.app/api/execution/order/multi-leg \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_type": "iron_condor",
    "legs": [
      {"symbol": "SPY251219C00600000", "side": "sell", ...},
      {"symbol": "SPY251219C00605000", "side": "buy", ...},
      {"symbol": "SPY251219P00590000", "side": "sell", ...},
      {"symbol": "SPY251219P00585000", "side": "buy", ...}
    ],
    "net_credit": "1.00"
  }'
```

---

### 3. Data Models (`backend/models/strategies.py`)

**Status**: ✅ **Fully Implemented**

**Models**:
- ✅ `OptionLeg` - Single leg of multi-leg order
- ✅ `MultiLegOrder` - Container for 4-leg iron condor
- ✅ `IronCondorSetup` - Complete configuration with strikes, pricing, risk
- ✅ `IronCondorExitConditions` - Exit rules (50% profit, 2x stop, etc.)
- ✅ `IronCondorSignal` - Entry/exit signal

**Ready for**:
- Earnings straddle strategy (models defined)
- Momentum swing strategy (models defined)

---

### 4. Multi-Leg Order Execution (`backend/api/execution.py`)

**Status**: ✅ **Partially Implemented**

**Implemented**:
- ✅ `place_multi_leg_order()` function (lines 630-726)
- ✅ Sequential leg execution
- ✅ Commission tracking ($0.65/contract × 4 legs = $2.60)
- ✅ Net credit/debit calculation
- ✅ Combined execution record

**Endpoint**:
- ✅ `POST /api/execution/order/multi-leg`

**❌ Gap**: Does NOT create position records in database

---

### 5. Position Monitor (`backend/monitoring/position_monitor.py`)

**Status**: ✅ **Partially Implemented**

**Implemented**:
- ✅ Strategy dispatch system (line 23-66)
- ✅ 60-second polling loop
- ✅ Auto-close on exit conditions
- ✅ Integrated in FastAPI lifespan (main.py:126-128)

**❌ Gap**: Iron condor exit logic is a stub (returns None)

---

## ❌ Critical Integration Gaps (Blocking Production)

### Gap 1: Database Schema - Multi-Leg Position Support

**Problem**: Current `positions` table only supports single-leg positions

**Current Schema** (backend/schema.sql:102-117):
```sql
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,           -- ❌ Only 1 symbol (need 4 for iron condor)
    strategy TEXT NOT NULL,
    position_type TEXT NOT NULL,    -- ❌ 'long'/'short' doesn't fit spreads
    quantity INTEGER NOT NULL,
    entry_price NUMERIC(10,4),      -- ❌ Single price (need net credit)
    -- ... rest of fields
);
```

**Solution**: Add multi-leg support

**Option A: JSONB Column (Recommended)**
```sql
ALTER TABLE positions ADD COLUMN legs JSONB DEFAULT NULL;
ALTER TABLE positions ADD COLUMN net_credit NUMERIC(10,4) DEFAULT NULL;
ALTER TABLE positions ADD COLUMN max_loss NUMERIC(12,2) DEFAULT NULL;
ALTER TABLE positions ADD COLUMN spread_width NUMERIC(10,2) DEFAULT NULL;

-- Example legs structure:
-- [
--   {"symbol": "SPY251219C00600000", "side": "sell", "quantity": 1, "price": 0.50},
--   {"symbol": "SPY251219C00605000", "side": "buy", "quantity": 1, "price": 0.10},
--   {"symbol": "SPY251219P00590000", "side": "sell", "quantity": 1, "price": 0.50},
--   {"symbol": "SPY251219P00585000", "side": "buy", "quantity": 1, "price": 0.10}
-- ]
```

**Option B: Separate Legs Table (Normalized)**
```sql
CREATE TABLE position_legs (
    id SERIAL PRIMARY KEY,
    position_id INTEGER REFERENCES positions(id) ON DELETE CASCADE,
    leg_number INTEGER NOT NULL,    -- 1, 2, 3, 4
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,             -- 'buy' or 'sell'
    option_type TEXT NOT NULL,      -- 'call' or 'put'
    strike NUMERIC(10,2) NOT NULL,
    quantity INTEGER NOT NULL,
    entry_price NUMERIC(10,4),
    current_price NUMERIC(10,4),
    UNIQUE(position_id, leg_number)
);

CREATE INDEX idx_position_legs_position ON position_legs(position_id);
```

**Recommendation**: Use **Option A (JSONB)** for simplicity and faster queries.

---

### Gap 2: Multi-Leg Order Execution - Position Creation

**Problem**: `place_multi_leg_order()` doesn't create position records

**Current Code** (backend/api/execution.py:630-726):
```python
async def place_multi_leg_order(multi_leg: MultiLegOrder) -> OrderResponse:
    # ... submits all 4 legs to Alpaca ...
    # ... calculates commission ...
    # ... creates Execution record ...

    return OrderResponse(
        success=True,
        execution=execution,
        alpaca_order_id=",".join([leg["order_id"] for leg in all_legs_filled]),
        message=f"Multi-leg {multi_leg.strategy_type} placed: {len(multi_leg.legs)} legs"
    )
    # ❌ NO position creation!
```

**Solution**: Add position creation after successful execution

**Implementation** (add to backend/api/execution.py):
```python
async def create_multi_leg_position(
    multi_leg: MultiLegOrder,
    entry_trade_id: Optional[int] = None
) -> Optional[int]:
    """
    Create a multi-leg position in the database

    Args:
        multi_leg: MultiLegOrder with all legs
        entry_trade_id: Trade ID from trades table

    Returns:
        Position ID if successful, None otherwise
    """
    try:
        if not supabase:
            logger.warning("Supabase not configured, skipping position tracking")
            return None

        # Prepare legs data
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

        # Use first leg symbol as representative (e.g., "iron_condor_SPY")
        representative_symbol = f"{multi_leg.strategy_type}_{multi_leg.legs[0].symbol[:3]}"

        data = {
            "symbol": representative_symbol,
            "strategy": multi_leg.strategy_type,
            "position_type": "spread",  # New type for multi-leg
            "quantity": multi_leg.legs[0].quantity,  # Reference quantity
            "entry_price": float(multi_leg.net_credit) if multi_leg.net_credit else 0.0,
            "entry_trade_id": entry_trade_id,
            "current_price": float(multi_leg.net_credit) if multi_leg.net_credit else 0.0,
            "unrealized_pnl": 0.0,
            "opened_at": datetime.utcnow().isoformat(),
            "status": "open",
            "legs": legs_data,  # JSONB column
            "net_credit": float(multi_leg.net_credit) if multi_leg.net_credit else None,
            "max_loss": float(multi_leg.max_loss) if multi_leg.max_loss else None,
            "spread_width": 5.0  # Hardcoded for now
        }

        response = supabase.table("positions").insert(data).execute()

        if response.data:
            position_id = response.data[0]['id']
            logger.info("Created multi-leg position",
                       position_id=position_id,
                       strategy=multi_leg.strategy_type,
                       legs=len(multi_leg.legs))
            return position_id

        return None

    except Exception as e:
        logger.error("Failed to create multi-leg position", error=str(e))
        return None
```

**Then modify `place_multi_leg_order()`** (line 630):
```python
async def place_multi_leg_order(multi_leg: MultiLegOrder) -> OrderResponse:
    # ... existing execution logic ...

    # NEW: Log to Supabase and get trade ID
    trade_id = await log_multi_leg_trade_to_supabase(execution, multi_leg)

    # NEW: Create multi-leg position
    if trade_id:
        await create_multi_leg_position(multi_leg, entry_trade_id=trade_id)
        logger.info("Multi-leg position tracked",
                   strategy=multi_leg.strategy_type,
                   legs=len(multi_leg.legs))

    return OrderResponse(...)
```

---

### Gap 3: Position Monitor - Spread P&L Calculation

**Problem**: Monitor can't calculate iron condor P&L

**Current Code** (backend/monitoring/position_monitor.py:23-66):
```python
async def check_strategy_specific_exit(position, strategy_name: str) -> Optional[str]:
    # ... routing logic ...

    if strategy_name.lower() == "iron_condor" or "condor" in strategy_name.lower():
        # ❌ Placeholder logic
        tick = await get_latest_tick(position.symbol)
        if not tick:
            return None

        current_value = (tick.bid + tick.ask) / 2

        # TODO: Load setup from database or position metadata
        return None  # ❌ Always returns None!
```

**Solution**: Implement full iron condor exit logic

**Implementation** (replace lines 36-54 in position_monitor.py):
```python
if strategy_name.lower() == "iron_condor" or "condor" in strategy_name.lower():
    try:
        # Get legs from position metadata
        if not position.legs:
            logger.warning("Iron condor position missing legs data", position_id=position.id)
            return None

        # Fetch current prices for all 4 legs
        leg_values = []
        for leg_data in position.legs:
            tick = await get_latest_tick(leg_data['symbol'])
            if not tick:
                logger.warning("Cannot get tick for leg", symbol=leg_data['symbol'])
                return None

            current_price = (tick.bid + tick.ask) / 2

            # Calculate leg value (sell = negative, buy = positive)
            if leg_data['side'] == 'sell':
                leg_value = -(current_price * leg_data['quantity'] * 100)
            else:  # buy
                leg_value = current_price * leg_data['quantity'] * 100

            leg_values.append(leg_value)

        # Sum all leg values to get net position value
        current_position_value = sum(leg_values)

        # Original credit received (entry_price stores net credit)
        entry_credit = position.entry_price * position.quantity * 100

        # P&L = Credit Received - Current Position Cost
        # If current_position_value is negative (we owe money), that's a loss
        pnl = entry_credit - abs(current_position_value)
        pnl_pct = pnl / entry_credit if entry_credit > 0 else 0

        # Exit condition 1: 50% profit target
        if pnl_pct >= 0.50:
            return "50% profit target reached"

        # Exit condition 2: 2x credit stop loss
        if pnl <= -(entry_credit * 2):
            return "2x credit stop loss hit"

        # Exit condition 3: 3:50pm force close
        now_et = datetime.now(pytz.timezone('US/Eastern')).time()
        if now_et >= time(15, 50):
            return "3:50pm force close"

        # Exit condition 4: Breach detection (need underlying price)
        # Parse underlying from first leg symbol (e.g., "SPY251219C00600000" -> "SPY")
        first_leg_symbol = position.legs[0]['symbol']
        underlying_symbol = first_leg_symbol[:first_leg_symbol.index(next(filter(str.isdigit, first_leg_symbol)))]

        underlying_tick = await get_latest_tick(underlying_symbol)
        if underlying_tick:
            underlying_price = (underlying_tick.bid + underlying_tick.ask) / 2

            # Get short strikes from legs (legs 0 and 2 are short call/put)
            short_call_strike = position.legs[0]['strike']
            short_put_strike = position.legs[2]['strike']

            # Check 2% breach buffer
            call_distance = (short_call_strike - underlying_price) / underlying_price
            put_distance = (underlying_price - short_put_strike) / underlying_price

            if call_distance <= 0.02:
                return "Price breached call strike (2% buffer)"

            if put_distance <= 0.02:
                return "Price breached put strike (2% buffer)"

        return None  # No exit conditions met

    except Exception as e:
        logger.error("Failed to check iron condor exit",
                    position_id=position.id,
                    error=str(e))
        return None
```

---

### Gap 4: Frontend - Iron Condor UI

**Problem**: No UI to select or display iron condor trades

**Current State**:
- Dashboard shows only IV Mean Reversion trades
- No strategy selector dropdown
- No iron condor-specific P&L display

**Solution**: Add strategy selector and iron condor display

**Component 1: Strategy Selector** (create frontend/src/components/StrategySelector.tsx):
```tsx
import React from 'react';

interface Strategy {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
}

const strategies: Strategy[] = [
  {
    id: 'iv_mean_reversion',
    name: 'IV Mean Reversion',
    description: '30-45 DTE, buy/sell based on IV percentiles',
    enabled: true
  },
  {
    id: 'iron_condor',
    name: '0DTE Iron Condor',
    description: 'Same-day expiration, 4-leg spread for theta decay',
    enabled: true
  },
  {
    id: 'earnings_straddle',
    name: 'Earnings Straddle',
    description: 'Volatility expansion around earnings',
    enabled: false
  }
];

export function StrategySelector() {
  const [selectedStrategy, setSelectedStrategy] = React.useState('iv_mean_reversion');

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200">
      <h3 className="text-xl font-semibold mb-4">Active Strategy</h3>

      <div className="space-y-3">
        {strategies.map((strategy) => (
          <button
            key={strategy.id}
            onClick={() => strategy.enabled && setSelectedStrategy(strategy.id)}
            disabled={!strategy.enabled}
            className={`w-full text-left p-4 rounded-xl border-2 transition-all ${
              selectedStrategy === strategy.id
                ? 'border-teal-500 bg-teal-50'
                : strategy.enabled
                ? 'border-gray-200 hover:border-gray-300'
                : 'border-gray-100 opacity-50 cursor-not-allowed'
            }`}
          >
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-semibold text-gray-900">{strategy.name}</h4>
                <p className="text-sm text-gray-600 mt-1">{strategy.description}</p>
              </div>
              {!strategy.enabled && (
                <span className="text-xs bg-amber-100 text-amber-700 px-2 py-1 rounded-full">
                  Coming Soon
                </span>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
```

**Component 2: Iron Condor Position Card** (add to frontend/src/components/Positions.tsx):
```tsx
function IronCondorCard({ position }: { position: Position }) {
  const legs = position.legs || [];

  // Extract strikes
  const shortCall = legs.find(l => l.option_type === 'call' && l.side === 'sell');
  const longCall = legs.find(l => l.option_type === 'call' && l.side === 'buy');
  const shortPut = legs.find(l => l.option_type === 'put' && l.side === 'sell');
  const longPut = legs.find(l => l.option_type === 'put' && l.side === 'buy');

  return (
    <div className="bg-black rounded-2xl p-6 border-2 border-teal-500">
      <div className="flex items-center justify-between mb-4">
        <div>
          <span className="text-xs uppercase tracking-wide text-gray-400">Iron Condor</span>
          <h3 className="text-xl font-mono text-white">{position.symbol}</h3>
        </div>
        <div className="text-right">
          <p className="text-2xl font-mono text-white">${position.unrealized_pnl.toFixed(2)}</p>
          <p className={`text-sm ${position.unrealized_pnl >= 0 ? 'text-green-400' : 'text-rose-400'}`}>
            {((position.unrealized_pnl / (position.entry_price * position.quantity * 100)) * 100).toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Strike Visualization */}
      <div className="grid grid-cols-2 gap-4 mt-4">
        <div className="bg-rose-950 rounded-lg p-3">
          <p className="text-xs text-rose-400 mb-1">Call Spread</p>
          <p className="font-mono text-white">
            ${shortCall?.strike} / ${longCall?.strike}
          </p>
        </div>
        <div className="bg-green-950 rounded-lg p-3">
          <p className="text-xs text-green-400 mb-1">Put Spread</p>
          <p className="font-mono text-white">
            ${shortPut?.strike} / ${longPut?.strike}
          </p>
        </div>
      </div>

      {/* Exit Progress */}
      <div className="mt-4">
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>Profit Target (50%)</span>
          <span>{Math.min(100, (position.unrealized_pnl / (position.net_credit * 0.5)) * 100).toFixed(0)}%</span>
        </div>
        <div className="w-full bg-gray-800 rounded-full h-2">
          <div
            className="bg-gradient-to-r from-teal-500 to-emerald-500 h-2 rounded-full transition-all"
            style={{ width: `${Math.min(100, (position.unrealized_pnl / (position.net_credit * 0.5)) * 100)}%` }}
          />
        </div>
      </div>

      {/* Risk Metrics */}
      <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-gray-800">
        <div>
          <p className="text-xs text-gray-400">Credit</p>
          <p className="font-mono text-white">${position.net_credit}</p>
        </div>
        <div>
          <p className="text-xs text-gray-400">Max Loss</p>
          <p className="font-mono text-rose-400">${position.max_loss}</p>
        </div>
        <div>
          <p className="text-xs text-gray-400">DTE</p>
          <p className="font-mono text-white">0</p>
        </div>
      </div>
    </div>
  );
}
```

---

## 📋 Implementation Checklist (Prioritized)

### Phase 1: Database Schema (Critical - 1 hour)

- [ ] **Create schema migration file** (`backend/migrations/002_multi_leg_positions.sql`)
  ```sql
  -- Add multi-leg support to positions table
  ALTER TABLE positions ADD COLUMN IF NOT EXISTS legs JSONB DEFAULT NULL;
  ALTER TABLE positions ADD COLUMN IF NOT EXISTS net_credit NUMERIC(10,4) DEFAULT NULL;
  ALTER TABLE positions ADD COLUMN IF NOT EXISTS max_loss NUMERIC(12,2) DEFAULT NULL;
  ALTER TABLE positions ADD COLUMN IF NOT EXISTS spread_width NUMERIC(10,2) DEFAULT NULL;

  -- Add index for querying multi-leg positions
  CREATE INDEX IF NOT EXISTS idx_positions_strategy_type ON positions(strategy) WHERE legs IS NOT NULL;
  ```

- [ ] **Apply schema to Supabase** (SQL Editor or psql)
  ```bash
  psql $SUPABASE_URL -f backend/migrations/002_multi_leg_positions.sql
  ```

- [ ] **Update Position model** (`backend/models/trading.py`)
  ```python
  class Position(BaseModel):
      # ... existing fields ...
      legs: Optional[List[dict]] = None  # JSONB leg data
      net_credit: Optional[Decimal] = None
      max_loss: Optional[Decimal] = None
      spread_width: Optional[Decimal] = None
  ```

- [ ] **Test schema changes**
  ```bash
  # Verify columns exist
  psql $SUPABASE_URL -c "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='positions';"
  ```

---

### Phase 2: Position Creation (Critical - 2 hours)

- [ ] **Add `create_multi_leg_position()` function** (backend/api/execution.py)
  - Takes `MultiLegOrder` and `entry_trade_id`
  - Stores legs as JSONB
  - Returns position ID

- [ ] **Add `log_multi_leg_trade_to_supabase()` function** (backend/api/execution.py)
  - Similar to `log_trade_to_supabase()` but for spreads
  - Stores representative symbol (e.g., "iron_condor_SPY")
  - Stores net credit/debit

- [ ] **Modify `place_multi_leg_order()`** (backend/api/execution.py:630)
  - Call `log_multi_leg_trade_to_supabase()` after execution
  - Call `create_multi_leg_position()` with trade ID
  - Log position creation success

- [ ] **Test multi-leg execution**
  ```bash
  # Build iron condor
  curl -X POST http://localhost:8000/api/iron-condor/build \
    -H "Content-Type: application/json" \
    -d '{"underlying": "SPY", "quantity": 1}'

  # Execute (use output from build)
  curl -X POST http://localhost:8000/api/execution/order/multi-leg \
    -H "Content-Type: application/json" \
    -d '{ ... }'

  # Verify position created
  curl http://localhost:8000/api/execution/positions?status=open
  ```

---

### Phase 3: Position Monitoring (Critical - 2 hours)

- [ ] **Implement iron condor exit logic** (backend/monitoring/position_monitor.py:36-54)
  - Fetch all 4 leg prices
  - Calculate net position value
  - Calculate P&L vs entry credit
  - Check all 4 exit conditions

- [ ] **Add helper function `get_underlying_from_option_symbol()`**
  ```python
  def get_underlying_from_option_symbol(symbol: str) -> str:
      """Extract underlying from OCC option symbol (SPY251219C00600000 -> SPY)"""
      return symbol[:symbol.index(next(filter(str.isdigit, symbol)))]
  ```

- [ ] **Test position monitor**
  ```bash
  # Simulate position with exit condition
  # Monitor logs should show exit check and close
  tail -f logs/position_monitor.log
  ```

---

### Phase 4: Frontend UI (Optional - 3 hours)

- [ ] **Create StrategySelector component** (frontend/src/components/StrategySelector.tsx)
- [ ] **Create IronCondorCard component** (frontend/src/components/IronCondorCard.tsx)
- [ ] **Update Dashboard.tsx to include strategy selector**
- [ ] **Update Positions.tsx to render iron condor cards**
- [ ] **Add iron condor metrics to portfolio summary**
- [ ] **Test on Vercel preview deployment**

---

## 🚀 Deployment Steps

### 1. Deploy Backend (Railway)

```bash
# Commit changes
git add backend/
git commit -m "FEATURE: 0DTE Iron Condor multi-leg position tracking"

# Push to main (Railway auto-deploys)
git push origin main

# Monitor Railway logs
railway logs --tail
```

### 2. Apply Schema Migration (Supabase)

```bash
# Connect to Supabase
psql $SUPABASE_URL

# Apply migration
\i backend/migrations/002_multi_leg_positions.sql

# Verify
SELECT column_name FROM information_schema.columns WHERE table_name='positions';
```

### 3. Test End-to-End

```bash
# 1. Check entry window (should be false outside 9:31-9:45am ET)
curl https://trade-oracle-production.up.railway.app/api/iron-condor/should-enter

# 2. Build iron condor (if in window)
curl -X POST https://trade-oracle-production.up.railway.app/api/iron-condor/build \
  -H "Content-Type: application/json" \
  -d '{"underlying": "SPY", "quantity": 1}'

# 3. Execute order (save output from step 2)
curl -X POST https://trade-oracle-production.up.railway.app/api/execution/order/multi-leg \
  -H "Content-Type: application/json" \
  -d '{ ... output from build ... }'

# 4. Verify position created
curl https://trade-oracle-production.up.railway.app/api/execution/positions?status=open

# 5. Monitor position in Railway logs
railway logs --tail | grep "position_monitor"
```

### 4. Deploy Frontend (Vercel)

```bash
# Commit frontend changes
git add frontend/
git commit -m "UI: Iron condor strategy selector and position display"

# Vercel auto-deploys on push
git push origin main

# Test on Vercel
open https://trade-oracle-lac.vercel.app
```

---

## 📊 Success Metrics

After deployment, validate the following:

### Backend Validation
- [ ] Iron condor positions created in Supabase `positions` table
- [ ] Position has `legs` JSONB with 4 entries
- [ ] Position has `net_credit`, `max_loss`, `spread_width` populated
- [ ] Position monitor logs show iron condor exit checks
- [ ] Position auto-closes at 50% profit or 2x stop

### Frontend Validation
- [ ] Strategy selector displays "0DTE Iron Condor"
- [ ] Iron condor positions display with 4-leg visualization
- [ ] P&L updates every 5 seconds
- [ ] Exit condition progress bars render correctly

### Trading Validation (Paper Trading Only)
- [ ] Iron condor executes between 9:31-9:45am ET
- [ ] All 4 legs fill successfully (check Alpaca dashboard)
- [ ] Commission = $2.60 ($0.65 × 4 legs)
- [ ] Position closes at 3:50pm ET if still open
- [ ] Historical trades show in dashboard

---

## 🎯 Next Steps After Iron Condor

### Immediate (Next 1-2 Weeks)
1. **Earnings Straddle Strategy**
   - Integrate Finnhub API for earnings calendar
   - Implement ATM straddle logic
   - Add earnings blackout to iron condor

2. **Strategy Performance Dashboard**
   - Compare IV Mean Reversion vs Iron Condor
   - Show Sharpe ratio, win rate, P&L by strategy
   - Add strategy recommendations

3. **Backtesting Infrastructure**
   - Replay historical trades
   - Test iron condor with 0DTE data
   - Validate 70% win rate assumption

### Future Enhancements
- Real-time WebSocket streaming (replace REST polling)
- Horizontal scaling (Railway autoscaling)
- Advanced Greeks tracking (portfolio-level delta/theta)
- Machine learning signal optimization

---

## 📚 Reference Files

**Research**:
- `0DTE_IRON_CONDOR_EXPERT_GUIDE.md` - 40,000-word implementation guide

**Backend**:
- `backend/strategies/iron_condor.py` - Strategy logic
- `backend/api/iron_condor.py` - API routes
- `backend/api/execution.py` - Multi-leg execution
- `backend/monitoring/position_monitor.py` - Position monitoring
- `backend/models/strategies.py` - Data models
- `backend/schema.sql` - Database schema

**Testing**:
- `backend/test_iron_condor.py` - Unit tests
- `backend/test_iron_condor_simple.py` - Integration tests

**Documentation**:
- `CLAUDE.md` - Project context (auto-loads in Claude Code)
- `SCALING_PLAN.md` - Performance optimization guide

---

## ⚠️ Important Notes

### Risk Management
- **Paper trading only** - Never use real money without extensive validation
- Circuit breakers apply to ALL strategies (iron condor respects 5% max risk)
- Monitor free tier limits (Supabase: 500MB, Railway: $5/month after trial)

### Time Sensitivity
- Iron condors MUST close by 3:50pm ET (extreme gamma risk)
- Position monitor runs every 60 seconds (Railway resource usage)
- Entry window is 9:31-9:45am ET (first 15 minutes only)

### Commission Impact
- Iron condor = $5.20 round trip ($2.60 entry + $2.60 exit)
- Minimum credit should cover commissions ($1.00+ total)
- Track net profit after commissions in all analysis

---

**Estimated Total Implementation Time**: 6-8 hours
**Difficulty**: Intermediate (requires database migration + multi-leg logic)
**Priority**: High (unlocks daily income strategy with 70% historical win rate)

Ready to start implementing? Begin with **Phase 1: Database Schema** and work through the checklist sequentially.
