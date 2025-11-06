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

### `test_iron_condor.sh` - 0DTE Iron Condor Strategy Test

Automated end-to-end test of the 0DTE iron condor strategy with 4-leg execution.

**What it does:**
1. ✅ Checks backend and iron condor strategy health
2. ✅ Validates entry window (9:31-9:45am ET only)
3. ✅ Generates iron condor signal (0.15 delta strikes)
4. ✅ Builds 4-leg order (call spread + put spread)
5. ✅ Executes all 4 legs via Alpaca
6. ✅ Verifies position tracking
7. ✅ Displays exit conditions (50% profit, 2x stop, 3:50pm close)

**Usage:**

```bash
# Default: SPY, 1 iron condor, 0DTE
./scripts/test_iron_condor.sh

# Custom underlying and quantity
./scripts/test_iron_condor.sh QQQ 2

# Testing mode (bypass entry window check)
MOCK_ENTRY_WINDOW=true ./scripts/test_iron_condor.sh
```

**Prerequisites:**
- Backend deployed and healthy
- **Market hours:** 9:31-9:45am ET (or use MOCK_ENTRY_WINDOW=true)
- Environment variables configured
- Python 3 installed

**Expected Output:**

```
╔════════════════════════════════════════════════════════════╗
║         Trade Oracle - 0DTE Iron Condor Test             ║
╚════════════════════════════════════════════════════════════╝

Configuration:
  API Base:    https://trade-oracle-production.up.railway.app
  Underlying:  SPY
  Quantity:    1 iron condor(s)
  Expiration:  2025-11-06 (0DTE)

[1/9] Checking backend health...
✓ Backend healthy

[2/9] Checking iron condor strategy...
✓ Strategy initialized

[3/9] Checking entry window...
✓ In entry window

[4/9] Generating iron condor signal...
✓ Signal generated: SPY iron condor
  Call Spread:  600/605 (sell/buy)
  Put Spread:   590/585 (sell/buy)
  Total Credit: $1.50
  Max Profit:   $150
  Max Loss:     $350 (per side)

[5/9] Building multi-leg order...
✓ 4-leg order structured

[6/9] Fetching portfolio...
✓ Portfolio retrieved
  Balance:    $100000.00
  Daily P&L:  $0.00

[7/9] Risk validation...
✓ Risk approved (iron condor within limits)

[8/9] Executing iron condor...

╔════════════════════════════════════════════════════════════╗
║              ✓ IRON CONDOR EXECUTED                       ║
╚════════════════════════════════════════════════════════════╝

Trade Details:
  Underlying:    SPY
  Strategy:      0DTE Iron Condor
  Quantity:      1 contract(s)
  Call Spread:   600/605
  Put Spread:    590/585
  Net Credit:    $1.50
  Max Profit:    $150
  Max Loss:      $350 per side

Exit Conditions:
  ✓ 50% profit target
  ✓ 2x credit stop loss
  ✓ 3:50pm ET force close
  ✓ 2% breach detection

Next Steps:
  1. Check dashboard: https://trade-oracle-lac.vercel.app
  2. View position: https://trade-oracle-production.up.railway.app/api/execution/positions
  3. Monitor auto-exit conditions (checked every 60s)

[9/9] Verifying position tracking...
✓ Position tracked in database

Test complete! Check dashboard for real-time updates.
```

**Exit Codes:**
- `0` - Iron condor executed successfully OR gracefully exited (outside entry window)
- `1` - Error occurred (check output for details)

**Common Scenarios:**

1. **Outside Entry Window:**
   ```
   ✗ Not in entry window (current: 10:30am ET)
   Entry window: 9:31am - 9:45am ET
   To test anyway, run: MOCK_ENTRY_WINDOW=true ./scripts/test_iron_condor.sh
   ```
   ✅ **Expected behavior** - gracefully exits with informational message

2. **Testing Mode (Anytime):**
   ```bash
   MOCK_ENTRY_WINDOW=true ./scripts/test_iron_condor.sh
   ```
   ✅ Bypasses entry window check for testing outside market hours

3. **Strategy Not Initialized:**
   ```
   ✗ Iron condor strategy not initialized
   ```
   Solution: Check Railway logs for option chain initialization errors

4. **No Strikes Found:**
   ```
   ✗ Cannot find 0.15 delta strikes for SPY
   ```
   Solution: Try different underlying or check market data availability

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

# 3. Run iron condor test (9:31-9:45am ET)
./scripts/test_iron_condor.sh

# 4. Verify on dashboard
open https://trade-oracle-lac.vercel.app

# 5. Monitor positions (position monitor runs every 60 seconds)
# Positions will auto-close at:
# - 50% profit (IV: 50%, Iron Condor: 50%)
# - Stop loss (IV: 75%, Iron Condor: 2x credit)
# - Time-based (IV: 21 DTE, Iron Condor: 3:50pm ET)
```

### Pre-Market Testing (Before 9:30am ET)

```bash
# Test IV Mean Reversion anytime
./scripts/test_iv_trade.sh

# Test Iron Condor in mock mode (bypass entry window)
MOCK_ENTRY_WINDOW=true ./scripts/test_iron_condor.sh
```

---

## 🚀 Future Scripts (TODO)

- `monitor_positions.sh` - Real-time position monitoring
- `backtest_runner.sh` - Run backtests from CLI
- `deploy_check.sh` - Pre-deployment validation
- `close_position.sh` - Manually close specific position

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
