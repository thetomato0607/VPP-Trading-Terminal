"""
VPP Integration Test Suite
===========================
Verifies that the VPP engine is properly integrated and working.
"""

# AI-assisted (Claude, 7f566e9): checks converted from print/return-bool to real
# asserts with Claude.

import sys
import os


def test_vpp_engine():
    """Test VPP optimizer core functionality (using consolidated modules)."""
    print("\n" + "="*70)
    print("TEST 1: VPP Engine Import & Optimization")
    print("="*70)

    # Import from consolidated modules (single source of truth)
    # Add project root to path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

    from modules.optimization import BatteryOptimizer, BatteryAsset
    from modules.market_data import MarketDataGenerator

    print("[PASS] Modules imported (DRY-compliant structure)")

    # Generate market scenario
    market_gen = MarketDataGenerator()
    scenario = market_gen.generate_scenario(
        system_size_kwp=2.5,
        daily_load_kwh=10.0,
        volatility_multiplier=1.0,
        cloud_cover_factor=0.3,
        intervals=96
    )
    print(f"[PASS] Generated {len(scenario.solar_kw)} intervals of test data")

    # Create battery asset
    asset = BatteryAsset(
        capacity_kwh=13.5,
        power_kw=5.0,
        efficiency=0.90,
        initial_soc_pct=50.0
    )
    print("[PASS] Battery asset created")

    # Create optimizer and run
    optimizer = BatteryOptimizer(timestep_minutes=15)
    result = optimizer.optimize(
        asset=asset,
        solar_kw=scenario.solar_kw,
        load_kw=scenario.load_kw,
        price_gbp_kwh=scenario.price_gbp_kwh,
        grid_export_limit_kw=4.0
    )

    print(f"[PASS] Optimization completed successfully")
    print(f"  Revenue: {result.revenue_gbp:.2f} GBP")
    print(f"  Cost: {result.cost_gbp:.2f} GBP")
    print(f"  Net Profit: {result.net_profit_gbp:.2f} GBP")
    print(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")


def test_api_routes():
    """Test that API routes are properly configured."""
    print("\n" + "="*70)
    print("TEST 2: API Route Configuration")
    print("="*70)

    # Ensure backend is in path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from routes import vpp
    print("[PASS] VPP routes module imported")

    # Check router exists
    assert hasattr(vpp, 'router'), "VPP router not found"
    print("[PASS] VPP router exists")

    # Check endpoints
    routes = [r.path for r in vpp.router.routes]
    expected = ['/optimize', '/simulate', '/benchmark', '/health']

    for endpoint in expected:
        assert endpoint in routes, f"Endpoint missing: {endpoint}"
        print(f"[PASS] Endpoint exists: {endpoint}")


def test_models():
    """Test that Pydantic models are properly defined."""
    print("\n" + "="*70)
    print("TEST 3: Pydantic Models")
    print("="*70)

    # Ensure backend is in path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from models import VPPOptimizationRequest

    print("[PASS] All VPP models imported")

    # Test model instantiation
    request = VPPOptimizationRequest(
        solar_forecast_kw=[0.5] * 96,
        battery_capacity_kwh=13.5
    )
    print("[PASS] VPPOptimizationRequest model instantiated")


def test_main_integration():
    """Test that VPP is integrated in main.py."""
    print("\n" + "="*70)
    print("TEST 4: Main App Integration")
    print("="*70)

    # FIX: Add current directory (backend) to path so we can find main.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    try:
        from main import app
    except ImportError:
        print(f"Debug: Current sys.path: {sys.path}")
        raise

    # Check VPP router is included
    routes = [r.path for r in app.routes]
    vpp_routes = [r for r in routes if r.startswith('/vpp')]

    assert len(vpp_routes) > 0, "No VPP routes found in main app"
    print(f"[PASS] Found {len(vpp_routes)} VPP routes in main app")


def run_all_tests():
    """Run complete test suite as a standalone script (`python test_vpp_integration.py`)."""
    print("\n" + "="*70)
    print(" VPP INTEGRATION TEST SUITE ".center(70, "="))
    print("="*70)

    tests = [
        ("VPP Engine", test_vpp_engine),
        ("API Routes", test_api_routes),
        ("Pydantic Models", test_models),
        ("Main Integration", test_main_integration)
    ]

    results = []
    for name, test_func in tests:
        try:
            test_func()
            passed = True
        except AssertionError as e:
            print(f"[FAIL] {e}")
            passed = False
        except Exception as e:
            print(f"[FAIL] Error: {e}")
            import traceback
            traceback.print_exc()
            passed = False
        results.append((name, passed))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed_count = sum(1 for _, passed in results if passed)
    total = len(results)

    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {name}")

    print("="*70)
    print(f"Results: {passed_count}/{total} tests passed")

    if passed_count == total:
        print("\n[SUCCESS] All tests passed! Your VPP is ready to use.")
        return 0
    else:
        print(f"\n[ERROR] {total - passed_count} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
