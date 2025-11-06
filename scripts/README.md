# Trade Oracle - Test Scripts

Automated testing scripts for Trade Oracle trading strategies.

## 📜 Available Scripts

### `test_iv_trade.sh` - IV Mean Reversion Trade Test

Automated end-to-end test of the complete IV Mean Reversion trading workflow.

**What it does:**
1. ✅ Checks backend health
2. ✅ Generates IV signal (buy/sell based on IV percentile)
3. ✅ Gets risk approval (validates circuit breakers)
4. ✅ Executes trade via Alpaca (paper trading)
5. ✅ Verifies execution and displays order ID

**Usage:**

```bash
# Default: SPY Dec 19 $600 Call, 1 contract
./scripts/test_iv_trade.sh

# Custom symbol and quantity
./scripts/test_iv_trade.sh SPY251219C00600000 2

# Different option (QQQ)
./scripts/test_iv_trade.sh QQQ251219C00640000 1
```

**Prerequisites:**
- Backend deployed and healthy
- Environment variables configured (ALPACA_API_KEY, SUPABASE_URL, etc.)
- Python 3 installed (for JSON parsing)

**Expected Output:**

```
╔════════════════════════════════════════════════════════════╗
║          Trade Oracle - IV Mean Reversion Test            ║
╚════════════════════════════════════════════════════════════╝

Configuration:
  API Base: https://trade-oracle-production.up.railway.app
  Symbol:   SPY251219C00600000
  Quantity: 1

[1/5] Checking backend health...
✓ Backend healthy

[2/5] Generating IV Mean Reversion signal...
✓ Signal generated: BUY
  Entry:       $12.0
  Stop Loss:   $6.00
  Take Profit: $24.00
  Reasoning:   IV rank 0.00 < 0.30 (underpriced), DTE 43

[3/5] Fetching portfolio state...
✓ Portfolio retrieved
  Balance:    $96927.59
  Daily P&L:  $-2288.00

[4/5] Getting risk approval...
✓ Risk approved
  Approved Qty: 3 contracts
  Max Loss:     $1800.00

[5/5] Executing trade...

╔════════════════════════════════════════════════════════════╗
║                    ✓ TRADE EXECUTED                       ║
╚════════════════════════════════════════════════════════════╝

Trade Details:
  Symbol:      SPY251219C00600000
  Side:        BUY
  Quantity:    1 contract(s)
  Entry:       $12.0
  Stop Loss:   $6.00
  Take Profit: $24.00
  Order ID:    1ddb050f-c1f9-4a90-b7a4-ef3e899d5f00

Next Steps:
  1. Check dashboard: https://trade-oracle-lac.vercel.app
  2. View position: https://trade-oracle-production.up.railway.app/api/execution/positions
  3. Monitor auto-exit at 50% profit or 75% loss
```

**Exit Codes:**
- `0` - Trade executed successfully
- `1` - Error occurred (check output for details)

**Common Errors:**

1. **Backend unhealthy**
   ```
   ✗ Backend unhealthy
   ```
   Solution: Check Railway deployment, verify environment variables

2. **No signal generated**
   ```
   ✗ No valid signal generated
   ```
   Solution: IV conditions not met (check IV rank thresholds)

3. **Trade not approved**
   ```
   ✗ Trade not approved
   ```
   Solution: Circuit breakers triggered (check daily loss limit, consecutive losses)

4. **Order failed**
   ```
   ✗ TRADE FAILED
   Error: options order qty must be <= 1000
   ```
   Solution: Bug in backend (should be fixed in latest deployment)

---

## 🔧 Configuration

### Environment Variables

The script uses the following environment variables:

```bash
# API Base URL (default: Railway production)
export API_BASE="https://trade-oracle-production.up.railway.app"

# Or use localhost for local testing
export API_BASE="http://localhost:8000"
```

---

## 📊 Verification

After running the script, verify the trade:

### 1. Check Dashboard
Open: https://trade-oracle-lac.vercel.app

You should see:
- New position in "Positions" section
- Updated portfolio balance
- Trade logged in "Trade History"

### 2. Check via API

```bash
# View all positions
curl https://trade-oracle-production.up.railway.app/api/execution/positions

# View recent trades
curl 'https://trade-oracle-production.up.railway.app/api/execution/trades?limit=5'

# View portfolio
curl https://trade-oracle-production.up.railway.app/api/execution/portfolio
```

### 3. Check Alpaca

Open: https://app.alpaca.markets/paper/dashboard/portfolio

You should see the new position in your paper account.

---

## 🎯 Testing Workflow

### Daily Testing Routine

```bash
# 1. Check backend health
curl https://trade-oracle-production.up.railway.app/health

# 2. Run IV trade test
./scripts/test_iv_trade.sh

# 3. Verify on dashboard
open https://trade-oracle-lac.vercel.app

# 4. Monitor position (position monitor runs every 60 seconds)
# Position will auto-close at:
# - 50% profit
# - 75% loss
# - 21 DTE
```

### Pre-Market Testing (Before 9:30am ET)

```bash
# Test IV Mean Reversion anytime
./scripts/test_iv_trade.sh

# Iron Condor only works 9:31-9:45am ET
# (Script for this coming soon)
```

---

## 🚀 Future Scripts (TODO)

- `test_iron_condor.sh` - 0DTE iron condor strategy test
- `monitor_positions.sh` - Real-time position monitoring
- `backtest_runner.sh` - Run backtests from CLI
- `deploy_check.sh` - Pre-deployment validation

---

## 📝 Notes

- All trades are **PAPER TRADING ONLY**
- Script validates paper trading before execution
- Position monitor runs automatically in background (60s intervals)
- Dashboard updates every 5 seconds
- Trades log to Supabase for analysis

---

## 🆘 Troubleshooting

**Script not executable:**
```bash
chmod +x scripts/test_iv_trade.sh
```

**Python not found:**
```bash
# Install Python 3
brew install python3  # macOS
```

**Curl not found:**
```bash
# Should be pre-installed on macOS/Linux
# Windows: Use WSL or Git Bash
```

**Backend connection timeout:**
```bash
# Check Railway is deployed
railway status

# Check DNS resolution
ping trade-oracle-production.up.railway.app
```

---

**Last Updated:** 2025-11-06
**Author:** Trade Oracle Team
**License:** MIT
