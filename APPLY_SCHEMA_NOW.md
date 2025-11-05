# Apply Positions Table Schema

**Status**: Railway deployment successful, schema migration needed

---

## Quick Start (2 minutes)

### Step 1: Open Supabase SQL Editor

Click this link:
👉 https://supabase.com/dashboard/project/zwuqmnzqjkybnbicwbhz/editor/sql

### Step 2: Copy This SQL

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

### Step 3: Click "Run"

You should see:
```
Success. No rows returned
```

### Step 4: Verify

Test the API:
```bash
curl https://trade-oracle-production.up.railway.app/api/execution/positions
```

Expected response:
```json
[]
```

If you see an empty array `[]` instead of an error, schema is applied successfully!

---

## What This Does

This creates the `positions` table that tracks:
- Open positions (BUY/SELL)
- Closed positions (CLOSE_LONG/CLOSE_SHORT)
- Entry/exit prices and P&L
- Exit reasons (profit target, stop loss, DTE, earnings)

The position monitor (running every 60 seconds) will automatically:
- Close positions at 50% profit
- Close positions at 75% loss
- Exit at 21 DTE
- Exit before earnings (when integrated)

---

## Troubleshooting

**Error: "relation already exists"**
- Schema already applied, you're done!

**Error: "permission denied"**
- Make sure you're logged into the correct Supabase project
- Check project URL matches: zwuqmnzqjkybnbicwbhz

**Error: "Could not find table 'public.trades'"**
- Run full schema first: `backend/schema.sql`
- Then apply positions table

---

## Next Steps After Schema Applied

1. **Test Position Lifecycle**
   - Follow POSITION_LIFECYCLE_DEPLOYMENT.md
   - Open test position
   - Verify auto-close on 50% profit

2. **Monitor Logs**
   ```bash
   railway logs
   ```
   Look for: "Position monitor started"

3. **View Positions**
   - GET /api/execution/positions?status=open
   - GET /api/execution/positions?status=closed

---

**Ready?** Copy the SQL, paste in Supabase editor, click Run. Done!
