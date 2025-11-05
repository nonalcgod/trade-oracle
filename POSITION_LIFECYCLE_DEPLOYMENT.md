# Position Lifecycle Implementation - Deployment Guide

**Status**: Ready for deployment
**Date**: November 5, 2025
**Commit**: cef2cca - FEATURE: Full Position Lifecycle Management

---

## What's New

Trade Oracle can now track and automatically close positions based on exit conditions:

### Features Implemented

1. **Position Tracking**
   - Opens position records on BUY/SELL signals
   - Tracks entry price, quantity, strategy
   - Monitors unrealized P&L in real-time

2. **Automated Exits**
   - ✅ **50% Profit Target** → Automatic close
   - ✅ **75% Stop Loss** → Automatic close
   - ✅ **21 DTE Threshold** → Exit to avoid gamma risk
   - ✅ **Earnings Blackout** → Exit 2 days before earnings (TODO: integrate API)

3. **Signal Types**
   - `BUY` → Open long position
   - `SELL` → Open short position
   - `CLOSE_LONG` → Sell to close long
   - `CLOSE_SHORT` → Buy to close short

4. **Background Monitor**
   - Checks all open positions every 60 seconds
   - Executes automatic exits via Alpaca API
   - Logs all closures with exit reasons

---

## Deployment Steps

### Step 1: Apply Database Schema

The positions table needs to be created in Supabase.

**Option A: Supabase SQL Editor (Recommended)**

1. Go to: https://supabase.com/dashboard/project/zwuqmnzqjkybnbicwbhz/editor/sql
2. Click "New Query"
3. Copy and paste the following SQL:

```sql
-- Table: positions
-- Track open and closed positions with full lifecycle
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    strategy TEXT NOT NULL,
    position_type TEXT NOT NULL,  -- 'long' or 'short'
    quantity INTEGER NOT NULL,
    entry_price NUMERIC(10,4),
    entry_trade_id INTEGER REFERENCES trades(id),
    current_price NUMERIC(10,4),
    unrealized_pnl NUMERIC(12,2),
    opened_at TIMESTAMPTZ DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    exit_trade_id INTEGER REFERENCES trades(id),
    exit_reason TEXT,
    status TEXT DEFAULT 'open'  -- 'open' or 'closed'
);

-- Indexes for position queries
CREATE INDEX IF NOT EXISTS idx_positions_open ON positions(status) WHERE status = 'open';
CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);
CREATE INDEX IF NOT EXISTS idx_positions_opened ON positions(opened_at DESC);
```

4. Click **"Run"**
5. Verify: Should see "Success. No rows returned"

**Option B: Using psql**

```bash
# Get connection string from Supabase dashboard
psql 'postgresql://postgres.[PROJECT-REF]:[PASSWORD]@...' \
  -c "$(cat backend/schema.sql | grep -A 25 'Table: positions')"
```

### Step 2: Deploy to Railway

```bash
# Push to GitHub (Railway auto-deploys)
git push origin main

# Monitor deployment
railway logs
```

**Expected Logs:**
```
Trade Oracle starting up
Position monitor started  ← KEY: Verify this appears
```

### Step 3: Verify Deployment

**Check Health:**
```bash
curl https://trade-oracle-production.up.railway.app/health
# Expected: {"status": "healthy", "services": {...}}
```

**Check API Docs:**
- Visit: https://trade-oracle-production.up.railway.app/docs
- Verify new endpoints:
  - `GET /api/execution/positions`
  - `GET /api/execution/positions/{position_id}`

**Check Positions Endpoint:**
```bash
curl https://trade-oracle-production.up.railway.app/api/execution/positions
# Expected: [] (empty array, no positions yet)
```

---

## Testing Plan

### Test 1: Manual Position Entry

**Goal**: Verify position tracking on BUY signal

1. Generate BUY signal via `/api/strategies/signal`
2. Execute order via `/api/execution/order`
3. Check positions: `GET /api/execution/positions?status=open`

**Expected Result:**
```json
[
  {
    "id": 1,
    "symbol": "QQQ251219C00640000",
    "strategy": "iv_mean_reversion",
    "position_type": "long",
    "quantity": 8,
    "entry_price": 11.96,
    "status": "open",
    "opened_at": "2025-11-05T...",
    "exit_reason": null
  }
]
```

### Test 2: Profit Target Auto-Close

**Goal**: Verify 50% profit triggers automatic exit

**Setup:**
1. Open test position with entry price $10.00
2. Seed tick data with current price $15.00 (50% gain)
3. Wait 60 seconds for monitor to run

**Expected Behavior:**
- Monitor detects 50% profit
- Executes CLOSE_LONG order
- Position marked as closed
- Logs show: "Position closed successfully, exit_reason: 50% profit target reached"

**Verification:**
```bash
# Check closed positions
curl https://trade-oracle-production.up.railway.app/api/execution/positions?status=closed

# Check trades (should have 2: entry and exit)
curl https://trade-oracle-production.up.railway.app/api/execution/trades
```

### Test 3: Stop Loss Auto-Close

**Goal**: Verify 75% loss triggers automatic exit

**Setup:**
1. Open test position with entry price $10.00
2. Seed tick data with current price $2.50 (75% loss)
3. Wait 60 seconds for monitor

**Expected:**
- Position closed with exit_reason: "75% stop loss hit"

### Test 4: DTE Exit

**Goal**: Verify 21 DTE threshold triggers exit

**Setup:**
1. Open position on option expiring in 20 days
2. Wait 60 seconds for monitor

**Expected:**
- Position closed with exit_reason: "21 DTE threshold reached"

### Test 5: Multiple Positions

**Goal**: Verify monitor handles multiple open positions

**Setup:**
1. Open 3 positions on different symbols
2. Set different exit conditions for each
3. Verify all close independently

---

## Monitoring

### Railway Logs

Watch for position monitor activity:
```bash
railway logs --follow
```

**Key Log Messages:**
- `Position monitor started` (startup)
- `Monitoring positions` (every 60s)
- `Exit condition met, closing position` (when triggered)
- `Position closed successfully` (confirmation)

### Supabase Queries

**Open Positions:**
```sql
SELECT * FROM positions WHERE status = 'open';
```

**Recently Closed:**
```sql
SELECT * FROM positions
WHERE status = 'closed'
ORDER BY closed_at DESC
LIMIT 10;
```

**Exit Reasons Distribution:**
```sql
SELECT exit_reason, COUNT(*)
FROM positions
WHERE status = 'closed'
GROUP BY exit_reason;
```

---

## API Reference

### Get Open Positions

```bash
GET /api/execution/positions?status=open&limit=50
```

**Query Parameters:**
- `status`: 'open', 'closed', or 'all' (default: 'open')
- `limit`: Max results (default: 50)

**Response:**
```json
[
  {
    "id": 1,
    "symbol": "QQQ251219C00640000",
    "strategy": "iv_mean_reversion",
    "position_type": "long",
    "quantity": 8,
    "entry_price": 11.96,
    "current_price": 12.50,
    "unrealized_pnl": 432.00,
    "opened_at": "2025-11-05T22:30:00Z",
    "status": "open"
  }
]
```

### Get Position by ID

```bash
GET /api/execution/positions/1
```

**Response:**
```json
{
  "id": 1,
  "symbol": "QQQ251219C00640000",
  "strategy": "iv_mean_reversion",
  "position_type": "long",
  "quantity": 8,
  "entry_price": 11.96,
  "entry_trade_id": 1,
  "current_price": 18.00,
  "unrealized_pnl": 4832.00,
  "opened_at": "2025-11-05T22:30:00Z",
  "closed_at": "2025-11-06T14:22:00Z",
  "exit_trade_id": 2,
  "exit_reason": "50% profit target reached",
  "status": "closed"
}
```

---

## Troubleshooting

### Issue: Position monitor not starting

**Symptoms:**
- Railway logs don't show "Position monitor started"
- Positions never auto-close

**Fix:**
1. Check Railway logs for startup errors
2. Verify asyncio.create_task() in main.py:122
3. Restart Railway service

### Issue: Positions not closing automatically

**Symptoms:**
- Open positions past exit conditions
- No "closing position" logs

**Checks:**
1. Verify tick data exists in database (monitor needs current prices)
2. Check Railway logs for errors in monitor loop
3. Verify position.symbol matches tick data symbol format

**Debug:**
```bash
# Check if tick data exists
curl https://trade-oracle-production.up.railway.app/api/data/latest/QQQ251219C00640000
```

### Issue: "Cannot get current price" error

**Cause:** No tick data in database for position symbol

**Fix:**
1. Fetch latest tick via `/api/data/latest/{symbol}`
2. Verify symbol format matches OCC standard
3. Seed historical data if needed

---

## Performance Considerations

### Monitor Frequency

Current: 60 seconds
- Trade-off: Lower frequency = less resource usage, slower exits
- Can adjust in `backend/monitoring/position_monitor.py:71`

### Database Queries

Monitor runs these queries every 60s:
1. `SELECT * FROM positions WHERE status = 'open'` (indexed)
2. `SELECT * FROM option_ticks WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1` (per position)

**Optimization for scale:**
- If >100 open positions, consider batch fetching ticks
- Add Redis caching for tick data (TTL: 10-30s)

### API Rate Limits

Alpaca paper trading limits:
- 200 requests/minute
- Each position close = 1 request
- Monitor can handle ~3 closes/second safely

---

## Next Steps

### Phase 5 Enhancements (Future)

1. **Earnings Calendar Integration**
   - Replace `is_earnings_blackout()` stub
   - Use Alpaca events API or third-party calendar
   - Fetch earnings dates for all underlying tickers

2. **Position Size Adjustments**
   - Monitor delta exposure across all positions
   - Reduce size if portfolio delta exceeds threshold
   - Implement dynamic position sizing based on IV rank

3. **Real-Time Updates**
   - Replace 60s polling with WebSocket streaming
   - Push position updates to frontend instantly
   - Alpaca WebSocket integration for live quotes

4. **Advanced Exit Logic**
   - Trailing stops (e.g., lock in 80% of profit after 50% gain)
   - Time-based exits (hold max 7 days)
   - IV rank reversals (exit when IV > 70th percentile again)

5. **Frontend Dashboard**
   - Open positions table with real-time P&L
   - Position details modal with Greeks
   - Manual close button for emergency exits

---

## Files Changed

### Core Implementation
- `backend/schema.sql` - Positions table definition
- `backend/models/trading.py` - SignalType enum + Position model
- `backend/api/execution.py` - Position tracking functions (create, close, monitor)
- `backend/monitoring/position_monitor.py` - Background service
- `backend/main.py` - Start monitor on app startup

### Utilities
- `backend/scripts/apply_positions_schema.py` - Schema migration helper
- `backend/scripts/apply_schema_psql.sh` - Shell script for psql execution

---

## Success Metrics

**Deployment Successful If:**
- ✅ Railway logs show "Position monitor started"
- ✅ `/health` returns healthy status
- ✅ `/api/execution/positions` returns 200 OK
- ✅ Supabase has positions table with indexes

**Feature Working If:**
- ✅ BUY signal creates position record
- ✅ Position visible in GET /positions
- ✅ 50% profit triggers automatic close
- ✅ Closed position has exit_reason populated
- ✅ Both entry and exit trades logged

---

**Questions? Check Railway logs or Supabase database for detailed execution traces.**
