# 🌅 Tomorrow Morning Checklist - November 7, 2025

## ⏰ Alarms to Set Tonight

- **9:15am EST**: Wake up alarm
- **9:25am EST**: Pre-market check (5 minutes before open)
- **9:30am EST**: Market open (1 minute before entry window)
- **9:44am EST**: Last chance alarm (1 minute before window closes)

---

## 📋 Pre-Market Checklist (9:25am - 9:30am EST)

Run these commands in order:

### 1. Backend Health Check
```bash
curl https://trade-oracle-production.up.railway.app/health
```
Expected: `"status": "healthy"`

### 2. Iron Condor Strategy Check
```bash
curl https://trade-oracle-production.up.railway.app/api/iron-condor/health
```
Expected: `"strategy_initialized": true`

### 3. Open Dashboard in Browser
URL: https://trade-oracle-lac.vercel.app
Check: Portfolio balance visible, no error messages

### 4. Check Risk Limits
```bash
curl https://trade-oracle-production.up.railway.app/api/risk/limits
```
Expected:
- `max_portfolio_risk_pct: 5.0` (temporary testing value)
- `max_position_size_pct: 10.0` (temporary testing value)

### 5. Verify Database Migration
Open Supabase SQL Editor: https://supabase.com/dashboard/project/[your-project-id]/editor
Run: `SELECT column_name FROM information_schema.columns WHERE table_name = 'positions';`
Expected columns: id, symbol, quantity, entry_price, current_price, status, created_at, updated_at, closed_at, exit_price, pnl, pnl_pct, exit_conditions, legs, net_credit, max_loss, spread_width

**IF MIGRATION NOT APPLIED**: Open `/Users/joshuajames/Projects/trade-oracle/backend/migrations/002_multi_leg_positions.sql` and paste into Supabase SQL Editor, then click RUN.

---

## 🎯 Entry Window (9:31am - 9:45am EST)

### Step 1: Check Entry Window Status (9:31am)
```bash
curl https://trade-oracle-production.up.railway.app/api/iron-condor/should-enter
```
Expected: `"should_enter": true` (between 9:31-9:45am)

### Step 2: Generate Iron Condor Signal (9:31am - 9:40am)
```bash
curl -X POST https://trade-oracle-production.up.railway.app/api/iron-condor/signal \
  -H "Content-Type: application/json" \
  -d '{"underlying": "SPY", "dte": 0}'
```
Expected: `"action": "OPEN_IRON_CONDOR"`

### Step 3: Build Iron Condor Structure (Immediate)
```bash
curl -X POST https://trade-oracle-production.up.railway.app/api/iron-condor/build \
  -H "Content-Type: application/json" \
  -d '{"underlying": "SPY", "expiration": "2025-11-07", "quantity": 1}'
```

**Review the response carefully:**
- Check `net_credit` (should be $1.00-$2.00 for SPY)
- Check `max_loss` (should be reasonable for your $100K paper account)
- Check all 4 legs have valid bid/ask prices

### Step 4: Get Risk Approval (Immediate)
```bash
# Copy the iron condor build response and use it here
curl -X POST https://trade-oracle-production.up.railway.app/api/risk/approve \
  -H "Content-Type: application/json" \
  -d '{
    "action": "OPEN_IRON_CONDOR",
    "symbol": "SPY",
    "quantity": 1,
    "entry_price": [net_credit from step 3],
    "max_loss": [max_loss from step 3]
  }'
```
Expected: `"approved": true`

### Step 5: Execute Multi-Leg Order (Immediate)
```bash
# Use the order structure from step 3
curl -X POST https://trade-oracle-production.up.railway.app/api/execution/order/multi-leg \
  -H "Content-Type: application/json" \
  -d '[full order JSON from step 3]'
```

**Monitor the response:**
- Alpaca order ID should be returned
- Status should be "filled" or "pending_new"
- Check dashboard for position appearing

---

## 🔍 Post-Entry Monitoring (9:45am - 3:50pm EST)

### Check Position Status Every Hour
```bash
curl https://trade-oracle-production.up.railway.app/api/execution/positions
```

### Monitor Exit Conditions
```bash
curl -X POST https://trade-oracle-production.up.railway.app/api/iron-condor/check-exit \
  -H "Content-Type: application/json" \
  -d '{"position_id": [your position ID from above]}'
```

**Exit triggers:**
- ✅ **50% profit target**: Net credit $1.50 → Close at $0.75 debit (+$75 profit per contract)
- 🛑 **2x stop loss**: Net credit $1.50 → Stop at $4.50 debit (-$450 loss per contract)
- ⏰ **3:50pm force close**: Automatic exit 10 minutes before market close
- 🚨 **2% breach buffer**: Underlying price within 2% of short strikes

---

## 🚨 Emergency Commands

### Force Close All Positions
```bash
curl -X POST https://trade-oracle-production.up.railway.app/api/testing/force-exit-all
```

### Check Monitor Status
```bash
curl https://trade-oracle-production.up.railway.app/api/testing/monitor-status
```

---

## 📊 Expected Outcomes (First Trade)

**Realistic Expectations for Paper Trading:**
- **Win Rate**: 70% theoretical (may vary with 1 trade)
- **Profit Target**: $75-$150 per contract (50% of net credit)
- **Time to Exit**: 1-3 hours (fast theta decay on 0DTE)
- **Max Loss**: $450-$500 per contract (if stop loss hit)

**Key Learning Goals:**
1. Verify all 4 legs execute simultaneously
2. Confirm position tracking in database (legs JSONB column)
3. Validate exit condition monitoring (50% profit, 2x stop, 3:50pm)
4. Check P&L calculation across 4 legs
5. Confirm dashboard displays multi-leg position correctly

---

## 🎓 What to Watch For

**Market Conditions:**
- **VIX**: If VIX < 15, consider skipping (low volatility = tight credit)
- **Overnight News**: Major economic data releases can spike volatility
- **Bid/Ask Spreads**: If spreads > $0.20 per leg, consider waiting for better liquidity

**Technical Issues:**
- Backend latency (Railway cold start can take 10-15 seconds)
- Alpaca API rate limits (60 requests/minute for paper trading)
- Database migration not applied (blocker - MUST apply before entry)

---

## 📝 Notes Section

Use this space to log observations during tomorrow's test:

**9:31am:**


**9:45am:**


**12:00pm:**


**3:50pm:**


**Post-Close Reflection:**


---

**Remember**: This is PAPER TRADING. The goal is to learn, not to rush. If anything feels wrong, skip the trade and troubleshoot. You have unlimited opportunities to practice.

**Good luck tomorrow! Set those alarms and get a good night's sleep.** 🌙
