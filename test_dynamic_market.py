"""Test that market data is now dynamic (not static)."""

from modules.market_data import MarketDataGenerator


def test_market_data_is_dynamic():
    """Random seeds (seed=None) should produce different results between runs."""
    print("\n" + "="*70)
    print("TEST: Market Data is Dynamic (Not Static)")
    print("="*70)

    gen1 = MarketDataGenerator(seed=None)
    s1 = gen1.generate_scenario()

    gen2 = MarketDataGenerator(seed=None)
    s2 = gen2.generate_scenario()

    print(f"\nScenario 1 first price: £{s1.price_gbp_kwh[0]:.4f}/kWh")
    print(f"Scenario 2 first price: £{s2.price_gbp_kwh[0]:.4f}/kWh")

    assert s1.price_gbp_kwh[0] != s2.price_gbp_kwh[0], \
        "Market is static - prices are the same between independent seed=None runs"
    print("\n[PASS] Market is dynamic - prices change between runs")


def test_fixed_seed_is_reproducible():
    """Test 2: Fixed seed still works for testing (reproducibility)."""
    print("\n" + "="*70)
    print("TEST: Fixed Seed Still Works (Reproducibility)")
    print("="*70)

    gen3 = MarketDataGenerator(seed=42)
    s3 = gen3.generate_scenario()

    gen4 = MarketDataGenerator(seed=42)
    s4 = gen4.generate_scenario()

    print(f"\nScenario 3 (seed=42): £{s3.price_gbp_kwh[0]:.4f}/kWh")
    print(f"Scenario 4 (seed=42): £{s4.price_gbp_kwh[0]:.4f}/kWh")

    assert s3.price_gbp_kwh[0] == s4.price_gbp_kwh[0], \
        "Fixed seed doesn't produce reproducible results"
    print("\n[PASS] Fixed seed produces reproducible results")
