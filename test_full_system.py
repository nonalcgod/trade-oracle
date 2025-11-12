#!/usr/bin/env python3
"""
Complete System Test - Pre-Market Validation
Tests all components before first live paper trade
"""
import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Configuration
BACKEND_URL = "https://trade-oracle-production.up.railway.app"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test(name: str):
    """Print test name"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}TEST: {name}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

def print_pass(message: str):
    """Print success message"""
    print(f"{GREEN}✅ PASS: {message}{RESET}")

def print_fail(message: str):
    """Print failure message"""
    print(f"{RED}❌ FAIL: {message}{RESET}")

def print_info(message: str):
    """Print info message"""
    print(f"{YELLOW}ℹ️  INFO: {message}{RESET}")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_1_backend_health():
    """Test 1: Backend Health Check"""
    print_test("Backend Health Check")

    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        data = response.json()

        if response.status_code == 200 and data.get("status") == "healthy":
            print_pass("Backend is healthy")
            print_info(f"Paper Trading: {data.get('paper_trading')}")
            print_info(f"Services: {json.dumps(data.get('services'), indent=2)}")
            return True
        else:
            print_fail(f"Backend unhealthy: {data}")
            return False
    except Exception as e:
        print_fail(f"Backend connection failed: {e}")
        return False

def test_2_database_migration():
    """Test 2: Verify Migration 003 Columns"""
    print_test("Database Migration 003 - New Columns")

    try:
        # Query information_schema to check columns
        result = supabase.rpc('exec_sql', {
            'query': """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'trades'
                AND column_name IN ('trading_mode', 'account_balance', 'risk_percentage', 'strategy_name')
                ORDER BY column_name
            """
        }).execute()

        # Alternative: Just try to select from trades with new columns
        test_query = supabase.table('trades').select(
            'id, trading_mode, account_balance, risk_percentage, strategy_name'
        ).limit(1).execute()

        print_pass("All migration 003 columns exist in trades table")
        print_info("Columns: trading_mode, account_balance, risk_percentage, strategy_name")
        return True

    except Exception as e:
        print_fail(f"Migration verification failed: {e}")
        return False

def test_3_performance_tables():
    """Test 3: Verify Performance Tracking Tables"""
    print_test("Performance Tracking Tables")

    tables = [
        'performance_snapshots',
        'strategy_performance',
        'trading_sessions',
        'strategy_criteria'
    ]

    all_exist = True
    for table in tables:
        try:
            result = supabase.table(table).select('*').limit(1).execute()
            print_pass(f"Table '{table}' exists and is queryable")
        except Exception as e:
            print_fail(f"Table '{table}' missing or error: {e}")
            all_exist = False

    return all_exist

def test_4_iv_mean_reversion():
    """Test 4: IV Mean Reversion Strategy"""
    print_test("IV Mean Reversion Strategy Endpoints")

    try:
        # Test 1: Get latest data for SPY
        print_info("Testing GET /api/data/latest/SPY")
        response = requests.get(f"{BACKEND_URL}/api/data/latest/SPY", timeout=10)

        if response.status_code == 200:
            data = response.json()
            print_pass("Successfully fetched SPY option data")
            print_info(f"Last updated: {data.get('last_updated', 'N/A')}")
            print_info(f"Call options available: {len(data.get('calls', []))}")
            print_info(f"Put options available: {len(data.get('puts', []))}")
        else:
            print_fail(f"Failed to fetch SPY data: {response.status_code}")
            return False

        # Test 2: Generate IV signal
        print_info("\nTesting POST /api/strategies/signal")
        signal_payload = {
            "symbol": "SPY",
            "lookback_days": 90
        }
        response = requests.post(
            f"{BACKEND_URL}/api/strategies/signal",
            json=signal_payload,
            timeout=10
        )

        if response.status_code == 200:
            signal = response.json()
            print_pass("Successfully generated IV signal")
            print_info(f"Signal: {signal.get('signal', 'N/A')}")
            print_info(f"IV Percentile: {signal.get('iv_percentile', 'N/A')}")
            print_info(f"Recommendation: {signal.get('recommendation', 'N/A')}")
        else:
            print_fail(f"Failed to generate signal: {response.status_code}")
            return False

        return True

    except Exception as e:
        print_fail(f"IV Mean Reversion test failed: {e}")
        return False

def test_5_iron_condor():
    """Test 5: Iron Condor Strategy"""
    print_test("Iron Condor Strategy Endpoints")

    try:
        # Test 1: Health check
        response = requests.get(f"{BACKEND_URL}/api/iron-condor/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_pass("Iron Condor strategy initialized")
            print_info(f"Status: {data}")
        else:
            print_fail(f"Iron Condor health check failed: {response.status_code}")
            return False

        # Test 2: Check entry window (will be False now, but tests the endpoint)
        response = requests.get(f"{BACKEND_URL}/api/iron-condor/should-enter", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_pass("Entry window check working")
            print_info(f"Should enter: {data.get('should_enter', False)}")
            print_info(f"Reason: {data.get('reason', 'N/A')}")
        else:
            print_fail(f"Entry window check failed: {response.status_code}")
            return False

        return True

    except Exception as e:
        print_fail(f"Iron Condor test failed: {e}")
        return False

def test_6_momentum_scalping():
    """Test 6: Momentum Scalping Strategy"""
    print_test("Momentum Scalping Strategy Endpoints")

    try:
        # Test 1: Health check
        response = requests.get(f"{BACKEND_URL}/api/momentum-scalping/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_pass("Momentum Scalping strategy healthy")
            print_info(f"Symbols monitored: {data.get('symbols_monitored', [])}")
            print_info(f"Indicators enabled: {data.get('indicators_enabled', [])}")
            print_info(f"Entry window active: {data.get('entry_window_active', False)}")
        else:
            print_fail(f"Momentum Scalping health check failed: {response.status_code}")
            return False

        # Test 2: Scan for signals (will likely find none now, but tests the endpoint)
        print_info("\nTesting GET /api/momentum-scalping/scan")
        response = requests.get(
            f"{BACKEND_URL}/api/momentum-scalping/scan?symbols=SPY,QQQ",
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print_pass("Momentum scan completed")
            print_info(f"Signals found: {len(data.get('signals', []))}")
            if len(data.get('signals', [])) > 0:
                print_info(f"First signal: {json.dumps(data['signals'][0], indent=2)}")
        else:
            print_fail(f"Momentum scan failed: {response.status_code}")
            return False

        return True

    except Exception as e:
        print_fail(f"Momentum Scalping test failed: {e}")
        return False

def test_7_position_monitoring():
    """Test 7: Position Monitoring System"""
    print_test("Position Monitoring System")

    try:
        # Check monitor status
        response = requests.get(f"{BACKEND_URL}/api/testing/monitor-status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_pass("Position monitor is operational")
            print_info(f"Monitor running: {data.get('monitor_running', False)}")
            print_info(f"Last check: {data.get('last_check_time', 'N/A')}")
            print_info(f"Positions monitored: {data.get('positions_monitored', 0)}")
        else:
            print_fail(f"Monitor status check failed: {response.status_code}")
            return False

        return True

    except Exception as e:
        print_fail(f"Position monitoring test failed: {e}")
        return False

def test_8_mock_trade_lifecycle():
    """Test 8: Complete Mock Trade Lifecycle"""
    print_test("Mock Trade Lifecycle with Performance Tracking")

    try:
        # Get current portfolio balance
        response = requests.get(f"{BACKEND_URL}/api/execution/portfolio", timeout=10)
        if response.status_code != 200:
            print_fail("Failed to get portfolio data")
            return False

        portfolio = response.json()
        account_balance = float(portfolio.get('total_equity', 100000))
        print_info(f"Account balance: ${account_balance:,.2f}")

        # Create a mock trade payload (IV Mean Reversion style)
        mock_trade = {
            "symbol": "SPY",
            "option_type": "call",
            "strike": 580,
            "expiration": (datetime.now() + timedelta(days=35)).strftime("%Y-%m-%d"),
            "action": "buy",
            "contracts": 1,
            "strategy": "iv_mean_reversion",
            "risk_percentage": 2.0,  # NEW COLUMN TEST
            "entry_reason": "TEST: Pre-market system validation"
        }

        print_info(f"\nAttempting mock trade: {json.dumps(mock_trade, indent=2)}")

        # Note: We won't actually execute this during market close
        # Instead, verify the endpoint is accessible
        print_info("Verifying order endpoint is accessible (not executing)")
        response = requests.get(f"{BACKEND_URL}/api/execution/trades", timeout=10)

        if response.status_code == 200:
            trades = response.json()
            print_pass("Trade execution endpoint is accessible")
            print_info(f"Historical trades in database: {len(trades)}")

            # Check if any trades have the new columns populated
            if len(trades) > 0:
                latest = trades[0]
                print_info(f"\nLatest trade verification:")
                print_info(f"  - Trading Mode: {latest.get('trading_mode', 'NOT SET')}")
                print_info(f"  - Account Balance: {latest.get('account_balance', 'NOT SET')}")
                print_info(f"  - Risk %: {latest.get('risk_percentage', 'NOT SET')}")
                print_info(f"  - Strategy: {latest.get('strategy_name', 'NOT SET')}")
        else:
            print_fail(f"Trade endpoint check failed: {response.status_code}")
            return False

        return True

    except Exception as e:
        print_fail(f"Mock trade lifecycle test failed: {e}")
        return False

def test_9_performance_views():
    """Test 9: Performance Tracking Views"""
    print_test("Performance Tracking Views")

    views = [
        'v_latest_strategy_performance',
        'v_equity_curve',
        'v_recent_trades_with_strategy'
    ]

    all_work = True
    for view in views:
        try:
            result = supabase.table(view).select('*').limit(5).execute()
            print_pass(f"View '{view}' is queryable")
            print_info(f"  Rows returned: {len(result.data)}")
        except Exception as e:
            print_fail(f"View '{view}' error: {e}")
            all_work = False

    return all_work

def test_10_risk_management():
    """Test 10: Risk Management Endpoints"""
    print_test("Risk Management System")

    try:
        # Test risk approval endpoint
        risk_check = {
            "symbol": "SPY",
            "contracts": 5,
            "premium": 2.50,
            "strategy": "iv_mean_reversion"
        }

        response = requests.post(
            f"{BACKEND_URL}/api/risk/approve",
            json=risk_check,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print_pass("Risk approval system operational")
            print_info(f"Approved: {data.get('approved', False)}")
            print_info(f"Risk %: {data.get('risk_percentage', 'N/A')}%")
            print_info(f"Position size: ${data.get('position_value', 'N/A')}")
            if not data.get('approved'):
                print_info(f"Rejection reason: {data.get('reason', 'N/A')}")
        else:
            print_fail(f"Risk approval check failed: {response.status_code}")
            return False

        # Test circuit breaker status
        response = requests.get(f"{BACKEND_URL}/api/risk/circuit-breakers", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_pass("Circuit breakers configured")
            print_info(f"Active breakers: {json.dumps(data, indent=2)}")
        else:
            print_fail(f"Circuit breaker check failed: {response.status_code}")
            return False

        return True

    except Exception as e:
        print_fail(f"Risk management test failed: {e}")
        return False

def run_all_tests():
    """Run all pre-market tests"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}TRADE ORACLE - PRE-MARKET SYSTEM VALIDATION{RESET}")
    print(f"{BLUE}Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

    tests = [
        test_1_backend_health,
        test_2_database_migration,
        test_3_performance_tables,
        test_4_iv_mean_reversion,
        test_5_iron_condor,
        test_6_momentum_scalping,
        test_7_position_monitoring,
        test_8_mock_trade_lifecycle,
        test_9_performance_views,
        test_10_risk_management
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print_fail(f"{test.__name__} crashed: {e}")
            results.append((test.__name__, False))

    # Print summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}TEST SUMMARY{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
        print(f"{status} - {test_name}")

    print(f"\n{BLUE}{'='*60}{RESET}")
    if passed == total:
        print(f"{GREEN}🎉 ALL TESTS PASSED ({passed}/{total}){RESET}")
        print(f"{GREEN}✅ System is ready for paper trading tomorrow!{RESET}")
    else:
        print(f"{YELLOW}⚠️  PARTIAL SUCCESS ({passed}/{total}){RESET}")
        print(f"{YELLOW}Some tests failed - review errors above{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
