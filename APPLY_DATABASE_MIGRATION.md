# Apply Database Migration - ACTION REQUIRED

**Status**: ⚠️ **1 Manual Step Required** (5 minutes)
**Date**: November 5, 2025

---

## 🎉 Backend Deployment Complete!

✅ **Railway Backend**: Successfully deployed with iron condor strategy
✅ **GitHub**: All changes committed and pushed
✅ **API Endpoints**: All iron condor endpoints operational

**Current Status**:
- Health: https://trade-oracle-production.up.railway.app/health → ✅ Healthy
- Iron Condor: https://trade-oracle-production.up.railway.app/api/iron-condor/health → ✅ Initialized
- Version: 2.0.0 (both strategies listed)

---

## ⚠️ Required: Apply Database Migration

The backend code is deployed, but the database schema needs a **1-time manual update** to support multi-leg positions.

### Why This Is Needed

Iron condors have **4 legs** (2 call options + 2 put options), but the current `positions` table only supports single-leg positions. We need to add a JSONB column to store all 4 legs.

### Step-by-Step Instructions (5 minutes)

#### Option 1: Supabase SQL Editor (Recommended)

1. **Open Supabase SQL Editor**
   ```
   https://app.supabase.com/project/YOUR_PROJECT_ID/sql
   ```

2. **Copy the migration script**
   - Open file: `backend/migrations/002_multi_leg_positions.sql`
   - Copy entire contents (Cmd+A, Cmd+C)

3. **Paste and Run**
   - Paste into Supabase SQL Editor
   - Click "Run" button (or Cmd+Enter)

4. **Verify Success**
   - You should see: ✅ **"Multi-leg position columns added successfully"**
   - If you see an error, screenshot it and we'll troubleshoot

#### Option 2: psql Command Line

If you have PostgreSQL client installed:

```bash
# From project root
psql "YOUR_SUPABASE_CONNECTION_STRING" -f backend/migrations/002_multi_leg_positions.sql

# Or with environment variable
source .env
psql "$SUPABASE_URL" -f backend/migrations/002_multi_leg_positions.sql
```

---

## What the Migration Does

The migration adds 4 new columns to the `positions` table:

```sql
ALTER TABLE positions ADD COLUMN legs JSONB DEFAULT NULL;
ALTER TABLE positions ADD COLUMN net_credit NUMERIC(10,4) DEFAULT NULL;
ALTER TABLE positions ADD COLUMN max_loss NUMERIC(12,2) DEFAULT NULL;
ALTER TABLE positions ADD COLUMN spread_width NUMERIC(10,2) DEFAULT NULL;
```

**Purpose**:
- `legs`: Stores all 4 option legs as JSON (symbol, side, strike, price)
- `net_credit`: Total credit received for iron condor
- `max_loss`: Maximum loss per position (risk management)
- `spread_width`: Width of spread in dollars (typically $5)

---

## Verify Migration Success

After running the migration, verify columns exist:

### SQL Verification Query

Run this in Supabase SQL Editor:

```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'positions'
AND column_name IN ('legs', 'net_credit', 'max_loss', 'spread_width');
```

**Expected Result** (4 rows):
```
column_name  | data_type
-------------+-----------
legs         | jsonb
net_credit   | numeric
max_loss     | numeric
spread_width | numeric
```

---

## After Migration: Test Iron Condor

Once the database migration is applied, you can test the full iron condor lifecycle:

### 1. Build Iron Condor (during market hours)

```bash
curl -X POST https://trade-oracle-production.up.railway.app/api/iron-condor/build \
  -H "Content-Type: application/json" \
  -d '{"underlying": "SPY", "quantity": 1}'
```

**Expected**: JSON response with 4-leg iron condor setup

### 2. Execute Multi-Leg Order

```bash
# Copy the multi_leg_order from previous response, then:
curl -X POST https://trade-oracle-production.up.railway.app/api/execution/order/multi-leg \
  -H "Content-Type: application/json" \
  -d '{ ... paste multi_leg_order ... }'
```

**Expected**: Success response with position created

### 3. Verify Position Created

```bash
curl -s "https://trade-oracle-production.up.railway.app/api/execution/positions?status=open" | python3 -m json.tool
```

**Expected**: Array with 1 position showing `legs` array with 4 entries

---

## Troubleshooting

### Issue: "Column 'legs' already exists"

**Solution**: Migration was already applied. You're good to go!

### Issue: "Permission denied"

**Solution**:
1. Check you're using service_role key (not anon key)
2. Verify you have admin access to the Supabase project

### Issue: "Syntax error near..."

**Solution**:
1. Make sure you copied the ENTIRE migration file
2. Don't modify the SQL - use it exactly as-is

---

## Current Backend Status

**Railway Deployment**: ✅ Live at https://trade-oracle-production.up.railway.app

**API Endpoints**:
- ✅ `/health` → Healthy
- ✅ `/api/iron-condor/health` → Strategy initialized
- ✅ `/api/iron-condor/should-enter` → Entry window check
- ✅ `/api/iron-condor/build` → Build iron condor setup
- ✅ `/api/execution/order/multi-leg` → Execute 4-leg order
- ✅ `/api/execution/positions` → Query positions

**Position Monitor**: Running in background (60-second polling)

---

## Next Steps After Migration

1. ✅ **Apply database migration** (this document)
2. 🎯 **Test during market hours** (9:30am-4:00pm ET)
3. 📊 **Monitor Railway logs** for position tracking
4. 🔄 **Paper trade 5-10 iron condors** to validate
5. 📈 **Track win rate** vs 70% theoretical

---

## Important Notes

⚠️ **Paper Trading Only**: System uses Alpaca paper trading API
⏰ **Time Sensitive**: Iron condors must close by 3:50pm ET
💵 **Commission**: $5.20 round trip ($2.60 entry + $2.60 exit)
🎯 **Entry Window**: Only 9:31-9:45am ET (first 15 minutes)

---

**Quick Summary**:
1. Open Supabase SQL Editor
2. Copy/paste `backend/migrations/002_multi_leg_positions.sql`
3. Click Run
4. Verify success message
5. Ready to trade iron condors! 🚀
