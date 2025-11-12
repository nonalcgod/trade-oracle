#!/usr/bin/env python3
"""
Quick script to check Supabase database structure
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv('.env')

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

print(f'Connecting to: {supabase_url}')
supabase = create_client(supabase_url, supabase_key)

# Check all tables
print('\n=== TABLES IN DATABASE ===')
try:
    # Query pg_catalog for tables
    result = supabase.rpc('execute_sql', {
        'sql': """
            SELECT tablename
            FROM pg_catalog.pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """
    }).execute()

    if hasattr(result, 'data') and result.data:
        for row in result.data:
            print(f'  ✓ {row}')
    else:
        # Fallback: Try querying known tables directly
        tables = ['trades', 'positions', 'option_ticks', 'reflections', 'portfolio_snapshots']
        for table in tables:
            try:
                result = supabase.table(table).select('*').limit(0).execute()
                print(f'  ✓ {table} (exists)')
            except Exception as e:
                print(f'  ✗ {table} (missing)')
except Exception as e:
    print(f'Error checking tables: {e}')
    # Try direct approach
    print('\nTrying direct table queries...')
    tables = ['trades', 'positions', 'option_ticks', 'reflections', 'portfolio_snapshots',
              'performance_snapshots', 'strategy_performance', 'trading_sessions', 'strategy_criteria']
    for table in tables:
        try:
            result = supabase.table(table).select('*').limit(0).execute()
            print(f'  ✓ {table}')
        except Exception as e:
            print(f'  ✗ {table} ({str(e)[:50]}...)')

# Check trades table structure
print('\n=== TRADES TABLE COLUMNS ===')
try:
    result = supabase.table('trades').select('*').limit(1).execute()
    if result.data and len(result.data) > 0:
        for key in result.data[0].keys():
            print(f'  - {key}')
    else:
        print('  (No data in trades table to show columns)')
        # Try to get column info from schema
        print('  Attempting to infer from schema...')
        result = supabase.table('trades').select('id').limit(0).execute()
        print(f'  Trades table exists but is empty')
except Exception as e:
    print(f'Error: {e}')

# Check for views
print('\n=== CHECKING FOR VIEWS ===')
views_to_check = ['v_latest_strategy_performance', 'v_equity_curve', 'v_recent_trades_with_strategy', 'strategy_performance']
for view in views_to_check:
    try:
        result = supabase.table(view).select('*').limit(0).execute()
        print(f'  ✓ {view} (exists as view or table)')
    except Exception as e:
        if 'does not exist' in str(e):
            print(f'  ✗ {view} (does not exist)')
        else:
            print(f'  ? {view} (error: {str(e)[:40]}...)')

print('\n=== SUMMARY ===')
print('Connection successful!')
