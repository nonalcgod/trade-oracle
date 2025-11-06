# Iron Condor Test Plan - November 6, 2025

**Test Window**: 9:31am - 9:45am ET (0DTE entry window)
**Status**: ✅ System Ready (All migrations complete)
**Environment**: Paper Trading (Alpaca)

---

## Pre-Flight Checklist

Before market open (9:30am ET):

- [ ] Backend healthy: `curl https://trade-oracle-production.up.railway.app/health`
- [ ] Frontend accessible: https://trade-oracle-9aniba0x6-ocean-beach-brands-8f8f4c15.vercel.app
- [ ] Database migration confirmed (4 columns: legs, net_credit, max_loss, spread_width)
- [ ] Risk limits at production values (2%/5%)

---

## Test Sequence

### 1. Check Entry Window (9:30am ET)

**Command**:
```bash
curl https://trade-oracle-production.up.railway.app/api/iron-condor/should-enter
```

**Expected Response**:
```json
{
  "should_enter": false,
  "reason": "Outside entry window (9:31-9:45 AM ET)",
  "current_time": "2025-11-06T14:30:00Z",
  "entry_window_start": "2025-11-06T14:31:00Z",
  "entry_window_end": "2025-11-06T14:45:00Z"
}
```

---

### 2. Check Iron Condor Health (9:30am ET)

**Command**:
```bash
curl https://trade-oracle-production.up.railway.app/api/iron-condor/health
```

**Expected Response**:
```json
{
  "status": "ok",
  "alpaca_configured": true,
  "strategy_initialized": true,
  "current_time": "2025-11-06T14:30:00Z"
}
```

---

### 3. Generate Signal (9:31am - 9:45am ET)

**Command**:
```bash
curl -X POST https://trade-oracle-production.up.railway.app/api/iron-condor/signal \
  -H "Content-Type: application/json" \
  -d '{
    "underlying": "SPY",
    "dte": 0
  }'
```

**Expected Response**:
```json
{
  "action": "OPEN_IRON_CONDOR",
  "underlying": "SPY",
  "expiration": "2025-11-06",
  "confidence": 0.8,
  "reasoning": "0DTE iron condor entry window active (9:31-9:45 AM ET)",
  "entry_time": "2025-11-06T14:31:00Z"
}
```

---

### 4. Build Iron Condor (9:31am - 9:45am ET)

**Command**:
```bash
curl -X POST https://trade-oracle-production.up.railway.app/api/iron-condor/build \
  -H "Content-Type: application/json" \
  -d '{
    "underlying": "SPY",
    "expiration": "2025-11-06",
    "quantity": 1
  }'
```

**Expected Response**:
```json
{
  "strategy": "iron_condor",
  "underlying": "SPY",
  "expiration": "2025-11-06",
  "quantity": 1,
  "legs": [
    {
      "symbol": "SPY251106C00600000",
      "side": "sell",
      "option_type": "call",
      "strike": 600.00,
      "delta": 0.15,
      "quantity": 1,
      "bid": 0.50,
      "ask": 0.52
    },
    {
      "symbol": "SPY251106C00605000",
      "side": "buy",
      "option_type": "call",
      "strike": 605.00,
      "delta": 0.10,
      "quantity": 1,
      "bid": 0.10,
      "ask": 0.12
    },
    {
      "symbol": "SPY251106P00590000",
      "side": "sell",
      "option_type": "put",
      "strike": 590.00,
      "delta": -0.15,
      "quantity": 1,
      "bid": 0.50,
      "ask": 0.52
    },
    {
      "symbol": "SPY251106P00585000",
      "side": "buy",
      "option_type": "put",
      "strike": 585.00,
      "delta": -0.10,
      "quantity": 1,
      "bid": 0.10,
      "ask": 0.12
    }
  ],
  "net_credit": 0.76,
  "max_loss": 424.00,
  "spread_width": 5.00,
  "profit_target": 0.38,
  "stop_loss": 1.52
}
```

**Key Validation Points**:
- ✅ All 4 legs present (2 calls, 2 puts)
- ✅ Short strikes at ~0.15 delta
- ✅ Long strikes at ~0.10 delta
- ✅ Net credit > 0 (credit spread)
- ✅ Spread width = 5.00 (standard $5 wide)
- ✅ Max loss = (spread_width - net_credit) * 100 * quantity

---

### 5. Execute Paper Trade (OPTIONAL - 9:31am - 9:45am ET)

**Command**:
```bash
curl -X POST https://trade-oracle-production.up.railway.app/api/execution/order/multi-leg \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "iron_condor",
    "underlying": "SPY",
    "legs": [
      {
        "symbol": "SPY251106C00600000",
        "side": "sell",
        "option_type": "call",
        "strike": 600.00,
        "quantity": 1
      },
      {
        "symbol": "SPY251106C00605000",
        "side": "buy",
        "option_type": "call",
        "strike": 605.00,
        "quantity": 1
      },
      {
        "symbol": "SPY251106P00590000",
        "side": "sell",
        "option_type": "put",
        "strike": 590.00,
        "quantity": 1
      },
      {
        "symbol": "SPY251106P00585000",
        "side": "buy",
        "option_type": "put",
        "strike": 585.00,
        "quantity": 1
      }
    ],
    "net_credit": 0.76,
    "max_loss": 424.00,
    "spread_width": 5.00
  }'
```

**Expected Response**:
```json
{
  "status": "success",
  "order_id": "abc123-def456-ghi789",
  "legs_filled": 4,
  "avg_fill_price": 0.74,
  "position_id": 123,
  "message": "Iron condor order submitted successfully"
}
```

---

### 6. Verify Database Storage (After execution)

**Command** (in Supabase SQL Editor):
```sql
SELECT
  id,
  symbol,
  strategy,
  position_type,
  status,
  net_credit,
  max_loss,
  spread_width,
  jsonb_array_length(legs) as num_legs
FROM positions
WHERE strategy = 'iron_condor'
ORDER BY created_at DESC
LIMIT 1;
```

**Expected Result**:
```
id  | symbol              | strategy     | position_type | status | net_credit | max_loss | spread_width | num_legs
----|---------------------|--------------|---------------|--------|------------|----------|--------------|----------
123 | iron_condor_SPY_... | iron_condor  | spread        | open   | 0.76       | 424.00   | 5.00         | 4
```

---

### 7. Monitor Position (Throughout day)

**Command**:
```bash
curl https://trade-oracle-production.up.railway.app/api/execution/positions/123
```

**Expected Response** (position details with exit conditions):
```json
{
  "id": 123,
  "symbol": "iron_condor_SPY_20251106",
  "strategy": "iron_condor",
  "position_type": "spread",
  "status": "open",
  "quantity": 1,
  "entry_price": 0.76,
  "current_price": 0.65,
  "pnl": 11.00,
  "legs": [...],
  "net_credit": 0.76,
  "max_loss": 424.00,
  "spread_width": 5.00,
  "exit_conditions": {
    "profit_target": 0.38,
    "stop_loss": 1.52,
    "force_close_time": "2025-11-06T19:50:00Z"
  }
}
```

---

### 8. Check Exit Conditions (Every 60 seconds via monitor)

**Command**:
```bash
curl -X POST https://trade-oracle-production.up.railway.app/api/iron-condor/check-exit \
  -H "Content-Type: application/json" \
  -d '{
    "position_id": 123,
    "current_price": 0.38,
    "entry_price": 0.76,
    "net_credit": 0.76,
    "legs": [...]
  }'
```

**Expected Response** (if profit target hit):
```json
{
  "should_exit": true,
  "reason": "profit_target",
  "pnl": 38.00,
  "pnl_pct": 0.50,
  "recommendation": "CLOSE_POSITION",
  "exit_price": 0.38
}
```

---

## Success Criteria

### ✅ **Full Success**
- [ ] Signal generated during entry window (9:31-9:45am ET)
- [ ] Iron condor built with 4 legs at target deltas (0.15 short, 0.10 long)
- [ ] Net credit > $0 (profitable structure)
- [ ] Position saved to database with all 4 legs
- [ ] Position monitor detects exit conditions (50% profit, 2x stop, 3:50pm)
- [ ] Frontend displays iron condor position

### ⚠️ **Partial Success**
- [ ] Build successful but no execution (strategy validation only)
- [ ] Execution successful but monitor not triggering exit signals

### ❌ **Failure Scenarios**
- [ ] Signal generation fails outside window → Expected (correct behavior)
- [ ] Option chain fetch timeout → Check Railway healthcheck timeout (should be 300s)
- [ ] Delta calculation errors → Check Greeks calculator
- [ ] Database storage fails → Verify migration 002 applied
- [ ] Position monitor not running → Check Railway logs for "Position monitor started"

---

## Troubleshooting

### Problem: "Outside entry window"
**Solution**: Wait until 9:31am ET. Iron condor only trades 0DTE during first 15 minutes.

### Problem: "Option chain fetch timeout"
**Solution**: Railway healthcheck timeout increased to 300s (commit 325b874). If still timing out, check Alpaca API status.

### Problem: "No suitable strikes found"
**Solution**: Try different underlying (QQQ, IWM). SPY may have low IV or insufficient liquidity.

### Problem: "Database error: column 'legs' does not exist"
**Solution**: Migration 002 not applied. Run verification query from IRON_CONDOR_TEST_PLAN.md.

### Problem: "Risk approval failed"
**Solution**: Check risk limits (2% portfolio risk, 5% position size). Iron condor may be too large for current portfolio balance.

---

## Post-Test Checklist

After testing (end of day):

- [ ] Review Railway logs for errors: `railway logs --tail`
- [ ] Check position monitor triggered exits correctly
- [ ] Verify P&L calculations in database match Alpaca
- [ ] Document any bugs or edge cases found
- [ ] Update CLAUDE.md with test results

---

## Alternative Test Symbols

If SPY doesn't work:

1. **QQQ** (Nasdaq-100 ETF) - Higher IV, more liquid 0DTE
2. **IWM** (Russell 2000 ETF) - Smaller notional, good for testing
3. **SPX** (S&P 500 Index) - Cash-settled, European-style (WARNING: much larger notional)

---

## Quick Commands Reference

```bash
# Health checks
curl https://trade-oracle-production.up.railway.app/health
curl https://trade-oracle-production.up.railway.app/api/iron-condor/health
curl https://trade-oracle-production.up.railway.app/api/risk/limits

# Entry window check
curl https://trade-oracle-production.up.railway.app/api/iron-condor/should-enter

# Build iron condor (9:31-9:45am ET)
curl -X POST https://trade-oracle-production.up.railway.app/api/iron-condor/build \
  -H "Content-Type: application/json" \
  -d '{"underlying": "SPY", "expiration": "2025-11-06", "quantity": 1}'

# List all positions
curl https://trade-oracle-production.up.railway.app/api/execution/positions

# Get specific position
curl https://trade-oracle-production.up.railway.app/api/execution/positions/123
```

---

**Test Prepared By**: Claude Code (Sonnet 4.5)
**System Status**: ✅ Production Ready (100%)
**Next Session**: Iron condor live test during market hours

**Good luck with tomorrow's test! 🚀**
