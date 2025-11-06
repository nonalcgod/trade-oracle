# Database Migration Verification Guide

**CRITICAL**: This migration MUST be applied before tomorrow's iron condor trade!

---

## Step 1: Check if Migration Already Applied

Open Supabase SQL Editor:
https://supabase.com/dashboard/project/[your-project-id]/sql

Run this query:
```sql
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'positions' 
ORDER BY ordinal_position;
```

**Look for these 4 columns:**
- `legs`
- `net_credit`
- `max_loss`
- `spread_width`

**If you see all 4 columns**: ✅ Migration already applied! Skip to Step 3.

**If you DON'T see all 4 columns**: ⚠️ Continue to Step 2.

---

## Step 2: Apply Migration (If Needed)

1. Open this file: `/Users/joshuajames/Projects/trade-oracle/backend/migrations/002_multi_leg_positions.sql`

2. Copy the ENTIRE contents (lines 1-97)

3. Paste into Supabase SQL Editor

4. Click "RUN" (or press Cmd+Enter)

5. You should see: ✅ Multi-leg position columns added successfully

---

## Step 3: Verify Migration Success

Run this query in Supabase SQL Editor:
```sql
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'positions' 
AND column_name IN ('legs', 'net_credit', 'max_loss', 'spread_width')
ORDER BY column_name;
```

**Expected Output:**
| column_name   | data_type | is_nullable | column_default |
|---------------|-----------|-------------|----------------|
| legs          | jsonb     | YES         | NULL           |
| max_loss      | numeric   | YES         | NULL           |
| net_credit    | numeric   | YES         | NULL           |
| spread_width  | numeric   | YES         | NULL           |

**If you see this**: ✅ Migration successful!

**If you DON'T see this**: 🚨 Contact support or check Supabase logs for errors.

---

## Step 4: Test Multi-Leg Position Insert (Optional)

This is optional but recommended to verify the migration works:

```sql
-- Insert test iron condor position
INSERT INTO positions (
    symbol,
    strategy,
    position_type,
    quantity,
    entry_price,
    status,
    legs,
    net_credit,
    max_loss,
    spread_width
) VALUES (
    'iron_condor_SPY_test',
    'iron_condor',
    'spread',
    1,
    1.50,
    'open',
    '[
        {"symbol": "SPY251219C00600000", "side": "sell", "option_type": "call", "strike": 600.00, "quantity": 1, "entry_price": 0.60},
        {"symbol": "SPY251219C00605000", "side": "buy", "option_type": "call", "strike": 605.00, "quantity": 1, "entry_price": 0.15},
        {"symbol": "SPY251219P00590000", "side": "sell", "option_type": "put", "strike": 590.00, "quantity": 1, "entry_price": 0.60},
        {"symbol": "SPY251219P00585000", "side": "buy", "option_type": "put", "strike": 585.00, "quantity": 1, "entry_price": 0.15}
    ]'::jsonb,
    1.50,
    350.00,
    5.00
);

-- Query the test position
SELECT * FROM positions WHERE symbol = 'iron_condor_SPY_test';

-- Delete test position (cleanup)
DELETE FROM positions WHERE symbol = 'iron_condor_SPY_test';
```

**If this works**: ✅ Ready for tomorrow's trade!

**If this fails**: 🚨 Migration has issues - check error message.

---

## Common Issues

### Issue 1: "relation 'positions' does not exist"
**Solution**: The `positions` table hasn't been created yet. Run `/Users/joshuajames/Projects/trade-oracle/backend/schema.sql` first.

### Issue 2: "column 'legs' already exists"
**Solution**: Migration already applied! Verify with Step 1 query.

### Issue 3: "permission denied"
**Solution**: Use the Supabase "service_role" key, not the "anon" key. Check your environment variables.

---

## Next Steps After Verification

1. ✅ Mark migration as complete in your notes
2. ✅ Proceed with tomorrow's test plan (MORNING_ALARM_CHECKLIST.md)
3. ✅ Set alarms for 9:15am, 9:25am, 9:30am, 9:44am EST
4. ✅ Get a good night's sleep!

---

**Questions?** Check the migration file for detailed comments: `/Users/joshuajames/Projects/trade-oracle/backend/migrations/002_multi_leg_positions.sql`
