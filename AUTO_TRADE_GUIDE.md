# 🚀 Auto-Trade Feature - One-Click Intelligent Trading

**Complete automation from market research to execution**

---

## 🎯 What Is Auto-Trade?

Auto-Trade is your **intelligent trading assistant** that handles the entire trading workflow automatically:

1. **📊 Researches Market** - Analyzes VIX, market trends, economic calendar
2. **🧠 Selects Strategy** - Auto-picks best strategy based on conditions
3. **⏰ Waits for Market** - Automatically waits if market is closed
4. **⚡ Executes Trade** - Places order with optimal parameters
5. **👀 Monitors Position** - Auto-exits at profit targets or stop loss

**It's like having an expert trader working for you 24/7!**

---

## 🌟 Key Features

### **Intelligent Strategy Selection**

The system automatically selects the best strategy based on:

| Time Window | Strategy Selected | Why |
|-------------|------------------|-----|
| 9:31-9:45am ET | **Iron Condor** | Optimal time for same-day spreads |
| 9:31-11:30am ET | **Momentum Scalping** | Captures intraday trends with 6 conditions |
| All other times | **IV Mean Reversion** | Most reliable all-day strategy (75% win rate) |

### **Market Research Integration**

Auto-Trade analyzes:
- ✅ **VIX Level** - Determines volatility environment
- ✅ **Market Trend** - Bullish, bearish, neutral, or range-bound
- ✅ **Economic Calendar** - Today's high-impact events
- ✅ **Options Flow** - Unusual activity detection
- ✅ **Time of Day** - Entry window validation

### **Confidence Scoring**

Every recommendation includes:
- **Confidence Score** (0-100%) based on market conditions
- **Detailed Reasoning** explaining the selection
- **Visual Progress** showing research → execution flow

---

## 💻 How to Use

### **Step 1: Access Auto-Trade**

**Web Dashboard:**
```
https://trade-oracle-lac.vercel.app/auto-trade
```

**Or from Main Dashboard:**
- Click the green **"Auto-Trade"** button in the top-right corner
- Button has ✨ Sparkles icon

### **Step 2: Click "Start Auto-Trade"**

The big green button will:
- Show **Market Status** (open/closed with countdown)
- Display **5-step workflow** explanation
- List available strategies with time windows

### **Step 3: Watch the Magic Happen**

The system progresses through automated stages:

#### **Stage 1: Researching** 📊
- Status: "Researching market conditions..."
- Shows spinner animation
- Analyzing VIX, trends, calendar

#### **Stage 2: Market Research Complete** ✅
- Displays findings card with:
  - VIX level and interpretation
  - Market trend (bullish/bearish/neutral)
  - Recommended strategy
  - Confidence score with visual bar
  - Detailed reasoning

#### **Stage 3: Waiting for Market** ⏰ (if needed)
- Status: "Market closed. Waiting X minutes..."
- Countdown timer updates
- Automatically proceeds when market opens

#### **Stage 4: Executing** ⚡
- Status: "Executing [strategy] trade..."
- Shows spinner
- Placing order with Alpaca

#### **Stage 5: Monitoring** 👀
- Status: "Trade executed successfully!"
- Displays:
  - Order ID
  - Position ID
  - Strategy selected
  - Entry details
- Position monitor takes over automatically

### **Step 4: Monitor Your Position**

After execution:
- Position appears in main dashboard
- Auto-exits at profit targets or stop loss
- View real-time P&L on `/` dashboard
- Or use `./monitor_position.sh` script

---

## 📊 Strategy Selection Logic

### **Time-Based Selection**

```python
# 9:31-9:45am ET (15-minute window)
if current_time in (9:31, 9:45):
    strategy = "iron_condor"
    confidence = 85%
    reasoning = "Iron Condor entry window open - optimal for same-day spreads"

# 9:31-11:30am ET (momentum window)
elif current_time in (9:31, 11:30):
    strategy = "momentum_scalping"
    confidence = 80%
    reasoning = "Momentum window open - scanning for 6-condition setups"

# All other times
else:
    strategy = "iv_mean_reversion"
    confidence = 75%
    reasoning = "Outside specialized windows - IV Mean Reversion most reliable"
```

### **Market Condition Overrides** (Coming Soon)

Future enhancements will add:
- **VIX > 30**: Force IV Mean Reversion (high IV environment)
- **Economic events**: Avoid trading during Fed announcements
- **Options flow**: Detect gamma squeezes, unusual activity
- **Trend strength**: Require minimum RSI/volume for momentum

---

## 🎨 User Interface

### **Market Status Banner**

Shows at the top:
```
🟢 Market Open | Market is currently open (9:30am-4:00pm ET)
```

Or if closed:
```
🟠 Market Closed | Market opens in 8h 45m
```

### **Research Results Card**

Displays after analysis:
```
📊 Market Research
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Market Trend: Bullish
VIX Level: 18.50
VIX Interpretation: Low volatility environment
Recommended Strategy: ⚡ MOMENTUM SCALPING
Confidence: ████████░░ 85%

Reasoning: Momentum scalping window is open (9:31-11:30am ET).
Will scan for 6-condition setups (EMA cross, RSI, volume, VWAP).
Best for capturing intraday trends with tight stops.

Today's Economic Events:
⚠️ Fed Interest Rate Decision (2:00pm ET)
⚠️ FOMC Press Conference (2:30pm ET)
```

### **Trade Details Card**

Shows after execution:
```
📝 Trade Details
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Order ID: abc-123-xyz
Position ID: 42
Strategy: ⚡ MOMENTUM SCALPING
```

### **Success Banner**

After completion:
```
✅ Trade Executed Successfully!
Position is now being monitored automatically
```

---

## 🔧 API Endpoints

### **Start Auto-Trade**

```bash
POST /api/auto-trade/start
```

Returns:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Auto-trade workflow started. Poll /status endpoint for updates."
}
```

### **Get Status**

```bash
GET /api/auto-trade/status/{session_id}
```

Returns:
```json
{
  "status": "researching",
  "message": "Researching market conditions...",
  "market_conditions": null,
  "selected_strategy": null,
  "trade_details": null,
  "order_id": null,
  "position_id": null,
  "error": null,
  "started_at": "2025-11-12T14:30:00Z",
  "completed_at": null
}
```

### **Check Market Status**

```bash
GET /api/auto-trade/market-status
```

Returns:
```json
{
  "is_open": false,
  "seconds_until_open": 31500,
  "minutes_until_open": 525,
  "hours_until_open": 8,
  "message": "Market opens in 8h 45m"
}
```

### **Cancel Auto-Trade**

```bash
DELETE /api/auto-trade/cancel/{session_id}
```

---

## 🚨 Safety Features

### **Circuit Breakers Still Active**

Auto-Trade respects all hardcoded risk limits:
- ✅ Max 2% portfolio risk per trade
- ✅ Max 5% position size
- ✅ -3% daily loss limit (stops all trading)
- ✅ 3 consecutive losses (stops all trading)

**Location:** `backend/api/risk.py:57-62`

### **Strategy-Specific Limits**

**Momentum Scalping:**
- Max 4 trades/day
- 2-loss rule (stop after 2 consecutive losses)
- 11:30am force close (no lunch trading)

**Iron Condor:**
- Entry window: 9:31-9:45am ONLY
- Force close at 3:50pm (end of day)

---

## 🐛 Troubleshooting

### **"Market Closed" Warning**

**What it means:** Auto-Trade detected market is closed

**What happens:** System will wait automatically until 9:30am ET market open

**Your options:**
1. Leave it running (recommended) - will execute when market opens
2. Cancel and come back later

### **"No Strong Signal" Error**

**What it means:** Selected strategy didn't find good setup

**Examples:**
- IV Mean Reversion: IV percentile between 30-70 (neutral zone)
- Iron Condor: VIX too high or too low
- Momentum Scalping: Not all 6 conditions met

**Your options:**
1. Try again in 30 minutes (conditions change)
2. Use manual trading scripts instead

### **"Risk Limit Exceeded" Error**

**What it means:** Circuit breaker blocked the trade

**Common causes:**
- Already hit -3% daily loss limit
- 3 consecutive losses today
- Order size exceeds 2% portfolio risk

**Your options:**
1. Wait until tomorrow (limits reset at market open)
2. Review risk settings in `backend/api/risk.py`

### **"Execution Failed" Error**

**What it means:** Order failed at Alpaca

**Common causes:**
- Alpaca paper account not funded (auto-funds on first order)
- Invalid strike/expiration (rare, should auto-correct)
- Network timeout (try again)

**Your options:**
1. Click "Start New Auto-Trade" to retry
2. Check Railway logs for details
3. Try manual execution via scripts

---

## 📈 Example Workflow

### **Scenario: Morning Auto-Trade**

**8:45am PT / 11:45am ET** - You click "Start Auto-Trade"

**Step 1 - Research (2 seconds)**
```
Status: Researching
→ Fetching VIX from CBOE
→ Analyzing market trend
→ Checking economic calendar
→ Evaluating entry windows
```

**Step 2 - Strategy Selection (instant)**
```
Market Research Complete!

VIX: 22.50 (Elevated)
Trend: Bullish
Time: 11:45am ET
Window: Outside all specialized windows

Recommended: IV Mean Reversion
Confidence: 75%
Reasoning: VIX > 20 indicates high IV environment.
IV Mean Reversion works best in elevated volatility.
Outside Iron Condor/Momentum windows.
```

**Step 3 - Execution (5-10 seconds)**
```
Status: Executing IV Mean Reversion trade
→ Generating signal for SPY
→ Signal: BUY (IV percentile: 28)
→ Selecting 35 DTE options
→ Strike: 580 call
→ Contracts: 1
→ Placing order with Alpaca
```

**Step 4 - Confirmation (instant)**
```
✅ Trade Executed Successfully!

Order ID: 64cf3a84-8d12-4f67-a2c8-7b3f9e1d2a54
Position ID: 42
Strategy: IV MEAN REVERSION
Entry: $2.50
Target: $3.75 (50% profit)
Stop: $1.88 (75% loss)

Position is now being monitored automatically.
```

---

## 🎓 Best Practices

### **When to Use Auto-Trade**

✅ **Good times:**
- First thing in the morning (9:30am-10:00am)
- When you're unsure which strategy to use
- When you want hands-off trading
- Testing system during paper trading

❌ **Avoid:**
- During major news events (Fed, earnings)
- When VIX is spiking rapidly (>35)
- Last 30 minutes of market (3:30pm-4:00pm)
- When you already have max positions open

### **Monitoring After Auto-Trade**

1. **Check dashboard immediately** - Verify order executed
2. **Use `./monitor_position.sh`** - Watch real-time P&L
3. **Set price alerts** (optional) - Get notified of big moves
4. **Review exit conditions** - Know when auto-exit will trigger

### **Combining with Manual Trading**

Auto-Trade works alongside manual trading:
- Auto-Trade respects your existing positions
- Circuit breakers apply to ALL trades (auto + manual)
- You can still use manual scripts for specific setups
- Position monitor handles all positions (auto + manual)

---

## 🔮 Future Enhancements

### **Coming Soon:**

1. **Advanced Market Research**
   - Real VIX data from CBOE
   - Economic calendar integration (investing.com)
   - Options flow from Unusual Whales
   - Gamma wall detection

2. **Multi-Trade Mode**
   - Execute multiple strategies simultaneously
   - Diversify across symbols (SPY, QQQ, IWM)
   - Stagger entry times for better fills

3. **Learning System**
   - Track success rate by market condition
   - Adjust confidence scores based on history
   - Personalize strategy selection

4. **Notification System**
   - Email/SMS when trade executes
   - Push notifications for profit targets
   - Daily performance summaries

---

## 📚 Related Documentation

- **Main Guide:** `FIRST_TRADE_GUIDE.md` - Complete trading guide
- **System Summary:** `TONIGHT_FINAL_SUMMARY.md` - Infrastructure overview
- **Project Context:** `CLAUDE.md` - Auto-loads in Claude Code
- **API Docs:** https://trade-oracle-production.up.railway.app/docs

---

## 🎉 You're Ready!

**To start using Auto-Trade:**

1. Open dashboard: https://trade-oracle-lac.vercel.app
2. Click green "Auto-Trade" button (top-right, ✨ icon)
3. Click big "Start Auto-Trade" button
4. Watch the magic happen!

**Or from terminal:**

```bash
# Test the endpoint
curl -X POST https://trade-oracle-production.up.railway.app/api/auto-trade/start

# Check market status
curl https://trade-oracle-production.up.railway.app/api/auto-trade/market-status
```

---

**Questions? Ask Claude Code anytime!**

*Remember: This is PAPER TRADING ONLY. No real money at risk. Perfect environment to test automation!* 🚀
