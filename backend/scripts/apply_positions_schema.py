"""
Apply positions table schema to Supabase

Run this script to add the positions table and indexes to the database.
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# SQL to create positions table
POSITIONS_TABLE_SQL = """
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
"""


def main():
    """Apply positions schema to Supabase"""
    try:
        print("Connecting to Supabase...")
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

        print("Executing SQL to create positions table...")

        # Note: Supabase Python client doesn't have direct SQL execution
        # You need to execute this via the Supabase SQL Editor or using psycopg2
        print("\nSQL to execute:")
        print("=" * 80)
        print(POSITIONS_TABLE_SQL)
        print("=" * 80)
        print("\nPlease execute this SQL in the Supabase SQL Editor:")
        print(f"1. Go to: {SUPABASE_URL.replace('https://', 'https://supabase.com/dashboard/project/')}")
        print("2. Navigate to SQL Editor")
        print("3. Copy and paste the SQL above")
        print("4. Click 'Run'")

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
