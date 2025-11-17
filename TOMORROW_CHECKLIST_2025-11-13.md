# Tomorrow's Trading Checklist - 2025-11-13

**Goal:** Validate all 3 strategies with live paper trades

---

## ⏰ Pre-Market (9:00am ET / 6:00am PT)

### System Health Checks
- [ ] Backend healthy: `curl https://trade-oracle-production.up.railway.app/health`
- [ ] Frontend loads: https://trade-oracle-lac.vercel.app
- [ ] Database connected (check Supabase dashboard)
- [ ] No Railway service errors

### Strategy Health Checks
- [ ] IV Mean Reversion: `/api/strategies/health`
- [ ] Iron Condor: `/api/iron-condor/health`
- [ ] Momentum Scalping: `/api/momentum-scalping/health`
- [ ] Position Monitor: `/api/testing/monitor-status`

### Risk Management Verification
- [ ] Circuit breakers active: `/api/risk/health`
- [ ] Daily loss limit: -3% (hardcoded)
- [ ] Max risk per trade: 2% (hardcoded)
- [ ] Consecutive loss limit: 3 (hardcoded)

### Market Conditions Research
- [ ] Check VIX level (use web search or TradingView)
- [ ] Economic calendar (any major announcements today?)
- [ ] SPY pre-market sentiment
- [ ] QQQ pre-market sentiment

---

## 🎯 Iron Condor Window (9:31-9:45am ET / 6:31-6:45am PT)

**ONLY 15 MINUTES - DO NOT MISS THIS WINDOW**

### Setup (9:30am ET)
- [ ] Open frontend: https://trade-oracle-lac.vercel.app
- [ ] Open Railway logs: https://railway.app (monitor for errors)
- [ ] Have terminal ready for manual commands

### Entry Decision (9:31-9:35am ET)
- [ ] Check if entry window active: `/api/iron-condor/should-enter`
- [ ] Generate signal: `/api/iron-condor/signal` (POST with `underlying: "SPY"`)
- [ ] Review signal quality:
  - Entry credit > 0
  - Strikes reasonable (0.15 delta target)
  - Max loss acceptable
- [ ] Approve with risk manager: `/api/risk/approve`

### Execution (9:35-9:45am ET)
**Option A: Auto-Trade (Recommended)**
```bash
curl -X POST https://trade-oracle-production.up.railway.app/api/auto-trade/start \
  -H 'Content-Type: application/json' \
  -d '{"strategy": "iron_condor"}'
```

**Option B: Manual (if auto-trade fails)**
1. Build setup: `/api/iron-condor/build`
2. Execute 4-leg order: `/api/execution/order/multi-leg`
3. Verify in Alpaca dashboard

### Post-Entry (9:45am+ ET)
- [ ] Verify position created in database: `/api/execution/positions`
- [ ] Check position has 4 legs in JSONB
- [ ] Verify position monitor is tracking it
- [ ] Set alert for 50% profit / 2x loss

---

## ⚡ Momentum Scalping Window (9:31-11:30am ET / 6:31-8:30am PT)

**2-HOUR WINDOW - STRICT DISCIPLINE**

### Setup (9:30am ET)
- [ ] Open ScalperPro: https://trade-oracle-lac.vercel.app/scalper
- [ ] Verify entry window shows "OPEN"
- [ ] Check 6-condition system active

### Signal Scanning (9:31-11:30am ET)
**Poll every 5 minutes:**
- [ ] Run scan: `/api/momentum-scalping/scan`
- [ ] Watch for signals with confidence ≥ 80%
- [ ] Check all 6 conditions are met:
  1. ✓ EMA(9) crosses EMA(21)
  2. ✓ RSI confirmation (>30 long, <70 short)
  3. ✓ Volume spike (≥2x average)
  4. ✓ VWAP breakout
  5. ✓ Relative strength
  6. ✓ Time window (9:31-11:30am)

### Entry Decision (When Signal Appears)
- [ ] Verify confidence ≥ 80%
- [ ] Check gamma wall positioning (favorable?)
- [ ] Check unusual options activity (aligned?)
- [ ] Approve with risk manager: `/api/risk/approve`

### Execution
**Option A: Frontend (Recommended)**
- Click "Execute Trade" on signal

**Option B: API**
```bash
curl -X POST https://trade-oracle-production.up.railway.app/api/momentum-scalping/execute \
  -H 'Content-Type: application/json' \
  -d '{"signal_id": "xyz", "quantity": 1}'
```

### Discipline Enforcement
- [ ] **MAX 4 TRADES TODAY** (hardcoded)
- [ ] **2-LOSS RULE** - Stop after 2 consecutive losses
- [ ] **11:30am FORCE CLOSE** - All positions closed (avoid lunch chop)

---

## 📊 IV Mean Reversion (Optional - If VIX > 20)

### Scan for Opportunities
- [ ] Check IVR: `/api/data/latest/{symbol}` (SPY, QQQ, etc.)
- [ ] Look for IV < 30th percentile (buy signal)
- [ ] Look for IV > 70th percentile (sell signal)

### Generate Signal
```bash
curl -X POST https://trade-oracle-production.up.railway.app/api/strategies/signal \
  -H 'Content-Type: application/json' \
  -d '{
    "underlying": "SPY",
    "signal_type": "BUY",
    "expiration_date": "2025-12-20"
  }'
```

### Execution (If Signal Generated)
- [ ] Approve with risk: `/api/risk/approve`
- [ ] Execute: `/api/execution/order`
- [ ] Verify position created

---

## 🔍 Position Monitoring (Throughout Day)

### Every 30 Minutes
- [ ] Check open positions: `/api/execution/positions`
- [ ] Check position monitor status: `/api/testing/monitor-status`
- [ ] Verify unrealized P&L updating

### Exit Conditions to Watch

**Iron Condor:**
- ✓ 50% profit → Auto-close
- ✓ 2x max loss → Auto-close
- ✓ 3:50pm ET → Force close

**Momentum Scalping:**
- ✓ 25% profit → Close 50%
- ✓ 50% profit → Close remaining 50%
- ✓ -50% loss → Stop loss
- ✓ 11:30am ET → Force close all

**IV Mean Reversion:**
- ✓ 50% profit → Auto-close
- ✓ 75% loss → Stop loss

---

## 🚨 Emergency Procedures

### If Position Monitor Fails
```bash
# Manual position check
curl https://trade-oracle-production.up.railway.app/api/execution/positions

# Manual exit (if needed)
curl -X POST https://trade-oracle-production.up.railway.app/api/testing/close-position \
  -H 'Content-Type: application/json' \
  -d '{"position_id": X}'
```

### If Multi-Leg Close Fails
- Check Railway logs for errors
- Verify Alpaca API is responding
- If partial failure, close remaining legs manually in Alpaca dashboard

### If Circuit Breaker Triggered
- **-3% daily loss** → All trading STOPS (hardcoded, cannot override)
- **3 consecutive losses** → All trading STOPS
- Do NOT try to bypass - this is for your protection

---

## 📝 End-of-Day Review (4:00pm ET / 1:00pm PT)

### Database Validation
- [ ] Check trades table: `SELECT * FROM trades WHERE timestamp::date = CURRENT_DATE`
- [ ] **CRITICAL:** Verify `exit_price` and `pnl` are NOT NULL for closed trades
- [ ] Check position status: All should be 'closed' or still 'open'

### P&L Validation (CRITICAL - Testing Today's Fixes)
```sql
-- Verify P&L fix worked
SELECT
  id,
  symbol,
  entry_price,
  exit_price,  -- Should NOT be null
  pnl,         -- Should NOT be null
  signal_type
FROM trades
WHERE
  timestamp::date = CURRENT_DATE
  AND signal_type IN ('close_long', 'close_short')
ORDER BY timestamp DESC;
```

**Expected Result:**
- ✅ `exit_price` has values (not null)
- ✅ `pnl` has values (not null)
- ✅ P&L calculation matches: `(exit_price - entry_price) * quantity * 100`

### Multi-Leg Validation (If Iron Condor Closed)
```sql
-- Verify multi-leg close worked
SELECT
  id,
  symbol,
  legs,        -- Should have 4 legs in JSONB
  entry_price,
  exit_price,  -- Should be aggregated exit cost
  pnl,         -- Should be sum of all 4 legs
  status
FROM positions
WHERE
  strategy = 'iron_condor'
  AND closed_at::date = CURRENT_DATE;
```

**Expected Result:**
- ✅ Position marked as 'closed'
- ✅ All 4 legs present in JSONB
- ✅ Exit price calculated correctly
- ✅ P&L is sum of all legs

### Performance Metrics
- [ ] Portfolio balance: `/api/execution/portfolio`
- [ ] Daily P&L (should match database)
- [ ] Win rate (trades won / total trades)
- [ ] Largest winner
- [ ] Largest loser

### Documentation
- [ ] Update trading journal with:
  - Signals seen
  - Trades executed
  - Exit reasons
  - Lessons learned
- [ ] Screenshot any errors for debugging
- [ ] Note any unexpected behavior

---

## ✅ Success Criteria for Tomorrow

### Must Validate:
1. **P&L Fix Works** - All closed trades show `exit_price` and `pnl` (not null)
2. **Multi-Leg Close Works** - If Iron Condor closes, all 4 legs exit correctly
3. **Position Monitor Works** - Auto-exits trigger as expected
4. **Risk Management Works** - Circuit breakers enforce limits

### Nice to Have:
- At least 1 momentum signal generated (6 conditions are strict)
- Iron Condor entered during 9:31-9:45am window
- All strategies tested in live market

### Red Flags:
- ❌ P&L showing null after position close → Bug still exists
- ❌ Multi-leg position can't close → Implementation failed
- ❌ Position monitor crashes → Monitor needs debugging
- ❌ Circuit breakers don't trigger → Risk management broken

---

## 📞 Quick Reference

**Frontend:**
- Main: https://trade-oracle-lac.vercel.app
- ScalperPro: https://trade-oracle-lac.vercel.app/scalper

**Backend:**
- API: https://trade-oracle-production.up.railway.app
- Docs: https://trade-oracle-production.up.railway.app/docs

**Monitoring:**
- Railway: https://railway.app
- Supabase: https://supabase.com
- Alpaca: https://app.alpaca.markets

**Key Endpoints:**
```bash
# Health
curl https://trade-oracle-production.up.railway.app/health

# Positions
curl https://trade-oracle-production.up.railway.app/api/execution/positions

# Portfolio
curl https://trade-oracle-production.up.railway.app/api/execution/portfolio

# Emergency Exit All
curl -X POST https://trade-oracle-production.up.railway.app/api/testing/force-exit-all
```

---

**Remember:**
- This is PAPER TRADING - no real money at risk
- Focus on validating the TWO CRITICAL FIXES from today
- Document everything for future reference
- Have fun! This is the culmination of weeks of work 🚀
