# coding: utf-8
"""
VPP TRADING TERMINAL
====================
Professional energy arbitrage simulation platform.

Bloomberg-style dashboard for grid-connected battery optimization.
"""

import streamlit as st
from dataclasses import asdict  # AI-assisted (Codex, 442f313 via PR #41): for the violations table.
from modules.optimization import BatteryOptimizer, BatteryAsset, calculate_baseline_cost
from modules.grid_physics import GridConstraintChecker
from modules.market_data import MarketDataGenerator
from modules.visualization import create_price_chart, create_grid_flow_chart

# Page configuration
st.set_page_config(
    page_title="VPP Trading Terminal",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme
st.markdown("""
<style>
    /* Force dark theme */
    .stApp {
        background-color: #0E1117;
    }

    /* Header styling */
    h1 {
        color: #00D9FF !important;
        font-family: 'Courier New', monospace;
        letter-spacing: 2px;
    }

    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 28px !important;
        font-weight: bold !important;
    }

    /* Sidebar */
    .css-1d391kg {
        background-color: #262730;
    }

    /* Remove Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR: SCENARIO CONTROLS
# ============================================================================

st.sidebar.markdown("## SCENARIO CONFIGURATION")
st.sidebar.markdown("---")

st.sidebar.markdown("### ASSET PARAMETERS")
battery_capacity = st.sidebar.slider(
    "Battery Capacity (kWh)",
    min_value=5.0,
    max_value=20.0,
    value=13.5,
    step=0.5,
    help="Total energy storage capacity"
)

battery_power = st.sidebar.slider(
    "Inverter Limit (kW)",
    min_value=2.0,
    max_value=10.0,
    value=5.0,
    step=0.5,
    help="Maximum charge/discharge rate"
)

grid_limit = st.sidebar.slider(
    "Grid Export Limit (kW)",
    min_value=2.0,
    max_value=8.0,
    value=4.0,
    step=0.5,
    help="DNO G99 connection limit"
)

initial_soc = st.sidebar.slider(
    "Initial SoC (%)",
    min_value=0,
    max_value=100,
    value=50,
    step=5
)

st.sidebar.markdown("---")
st.sidebar.markdown("### MARKET PARAMETERS")

# Live price toggle
use_live_prices = st.sidebar.checkbox(
    "Use Live UK Prices (Octopus Agile)",
    value=False,
    help="Fetch real UK electricity prices from Octopus Energy API"
)

if use_live_prices:
    octopus_region = st.sidebar.selectbox(
        "Region",
        options=['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P'],
        index=0,
        help="A=Eastern England, C=South West, etc."
    )
    st.sidebar.info("Fetching live prices from Octopus Energy...")
else:
    octopus_region = 'A'

system_size = st.sidebar.slider(
    "Solar System Size (kWp)",
    min_value=1.0,
    max_value=10.0,
    value=3.5,
    step=0.5
)

volatility = st.sidebar.slider(
    "Price Volatility Multiplier",
    min_value=1.0,
    max_value=5.0,
    value=1.5,
    step=0.5,
    help="1x = normal, 5x = extreme market conditions (synthetic only)"
)

cloud_cover = st.sidebar.slider(
    "Solar Irradiance Noise",
    min_value=0.0,
    max_value=1.0,
    value=0.3,
    step=0.1,
    help="0 = clear sky, 1 = heavy clouds"
)

daily_load = st.sidebar.slider(
    "Daily Load (kWh)",
    min_value=5.0,
    max_value=30.0,
    value=12.0,
    step=1.0
)

# Price alert threshold
alert_threshold = st.sidebar.slider(
    "Low Price Alert (£/kWh)",
    min_value=0.0,
    max_value=0.10,
    value=0.03,
    step=0.01,
    help="Alert when electricity price drops below this"
)

st.sidebar.markdown("---")

# Show live price if available
if use_live_prices:
    from modules.live_data import OctopusEnergyAPI
    from datetime import datetime as dt

    current_price = OctopusEnergyAPI.get_current_price(octopus_region)

    if current_price:
        # Color code based on price
        if current_price < alert_threshold:
            st.sidebar.success(f"CHEAP POWER ALERT! £{current_price:.4f}/kWh")
        elif current_price < 0.05:
            st.sidebar.info(f"Current Price: £{current_price:.4f}/kWh")
        elif current_price < 0.10:
            st.sidebar.warning(f"Current Price: £{current_price:.4f}/kWh")
        else:
            st.sidebar.error(f"HIGH PRICE: £{current_price:.4f}/kWh")

        # Peak pricing warning
        hour = dt.now().hour
        if 17 <= hour <= 20:
            st.sidebar.warning("Peak pricing period (5pm-8pm)")

        # Show statistics
        stats = OctopusEnergyAPI.get_price_statistics(octopus_region, days=7)
        if stats:
            deviation = (current_price - stats['mean_gbp_kwh']) / stats['std_gbp_kwh']
            if abs(deviation) > 2:
                st.sidebar.warning(f"Unusual price! {deviation:.1f}σ from 7-day mean")

# ============================================================================
# SYSTEM PERFORMANCE MONITOR
# ============================================================================

st.sidebar.markdown("---")
st.sidebar.markdown("### SYSTEM STATUS")

# Create metrics container
with st.sidebar.container():
    col1, col2 = st.columns(2)

    with col1:
        # Optimization speed
        if 'result' in st.session_state:
            solve_ms = st.session_state.result.solve_time_ms
            if solve_ms < 500:
                status = "FAST"
            elif solve_ms < 1000:
                status = "OK"
            else:
                status = "SLOW"

            st.metric(
                label="Solve Speed",
                value=f"{solve_ms:.0f}ms",
                delta=status
            )
        else:
            st.metric("Solve Speed", "N/A")

    with col2:
        # Data source
        if 'scenario' in st.session_state:
            scenario = st.session_state.scenario
            if scenario.price_data_source == "octopus_agile":
                st.metric("Data Source", "LIVE")
            else:
                st.metric("Data Source", "SIM")
        else:
            st.metric("Data Source", "N/A")

# API Health Check
if use_live_prices:
    st.sidebar.markdown("#### Live Data Status")

    # Check API availability
    try:
        from modules.live_data import OctopusEnergyAPI
        test_price = OctopusEnergyAPI.get_current_price(octopus_region)
        if test_price:
            st.sidebar.success("API Online")

            # Show last update time
            from datetime import datetime
            last_update = datetime.now().strftime("%H:%M:%S")
            st.sidebar.caption(f"Last checked: {last_update}")
        else:
            st.sidebar.warning("API Slow")
    except:
        st.sidebar.error("API Offline")
        st.sidebar.caption("Using synthetic fallback")

# Performance benchmarks
st.sidebar.markdown("#### Benchmarks")
st.sidebar.markdown("""
<div style='font-size: 12px; color: #888;'>
• Target: <500ms solve time<br>
• HiGHS: O(n²) complexity<br>
• Scale: 1000+ homes possible<br>
</div>
""", unsafe_allow_html=True)

# Quick actions
st.sidebar.markdown("---")
st.sidebar.markdown("### QUICK ACTIONS")

if st.sidebar.button("Download CSV", use_container_width=True):
    if 'result' in st.session_state:
        import pandas as pd
        from datetime import datetime
        result = st.session_state.result
        scenario = st.session_state.scenario

        df = pd.DataFrame({
            'Hour': [ts.strftime("%H:%M") for ts in scenario.timestamps],
            'Price (£/kWh)': scenario.price_gbp_kwh,
            'Solar (kW)': scenario.solar_kw,
            'Load (kW)': scenario.load_kw,
            'Charge (kW)': result.charge_schedule_kw,
            'Discharge (kW)': result.discharge_schedule_kw,
            'SoC (%)': result.soc_trajectory_pct,
            'Grid Export (kW)': result.grid_export_kw
        })

        csv = df.to_csv(index=False)
        st.sidebar.download_button(
            label="Download",
            data=csv,
            file_name=f"vpp_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.sidebar.info("Run optimization first")

st.sidebar.markdown("---")
st.sidebar.markdown("### AUTO-OPTIMIZATION")
st.sidebar.caption("Live mode: Optimization runs automatically when you adjust any parameter above")

# ============================================================================
# MAIN DASHBOARD
# ============================================================================

# Header
st.markdown("""
<div style='text-align: center; padding: 20px 0;'>
    <h1>VPP TRADING TERMINAL</h1>
    <p style='color: #888; font-size: 14px; letter-spacing: 1px;'>
        VIRTUAL POWER PLANT | GRID-CONSTRAINED BATTERY ARBITRAGE
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# SIMULATION ENGINE - AUTO-RUN ON PARAMETER CHANGE
# ============================================================================

# Always run optimization (automatically updates when sliders change)
if True:
    with st.spinner("Running optimization engine..."):
        # AI-assisted (Codex, 442f313 via PR #41): try/except for in-app error reporting; the
        # optimization steps inside predate it and were only re-indented.
        try:
            # Smart caching: Cache market scenario (solar/load/prices) separately from asset optimization
            # Market scenario depends on: region, solar size, load, volatility, clouds
            # Optimization depends on: battery params + scenario

            scenario_cache_key = f"{use_live_prices}_{octopus_region}_{system_size}_{daily_load}_{volatility}_{cloud_cover}"

            if 'scenario_cache_key' not in st.session_state or st.session_state.scenario_cache_key != scenario_cache_key:
                # Generate new market scenario (includes live price fetch if enabled)
                market_gen = MarketDataGenerator(
                    use_live_prices=use_live_prices,
                    octopus_region=octopus_region
                )
                scenario = market_gen.generate_scenario(
                    system_size_kwp=system_size,
                    daily_load_kwh=daily_load,
                    volatility_multiplier=volatility,
                    cloud_cover_factor=cloud_cover
                )
                st.session_state.scenario_cache_key = scenario_cache_key
                st.session_state.cached_scenario = scenario
                using_cache = False
            else:
                # Use cached scenario (fast - no API call needed)
                scenario = st.session_state.cached_scenario
                using_cache = True

            # Show data source
            if scenario.price_data_source == "octopus_agile":
                cache_msg = " (cached)" if using_cache else ""
                st.success(f"Using LIVE UK prices from Octopus Agile (Region {scenario.price_region}){cache_msg}")
            else:
                st.info("Using synthetic price model")

            # Run optimization
            asset = BatteryAsset(
                capacity_kwh=battery_capacity,
                power_kw=battery_power,
                efficiency=0.90,
                initial_soc_pct=initial_soc
            )

            optimizer = BatteryOptimizer(timestep_minutes=15)
            result = optimizer.optimize(
                asset=asset,
                solar_kw=scenario.solar_kw,
                load_kw=scenario.load_kw,
                price_gbp_kwh=scenario.price_gbp_kwh,
                grid_export_limit_kw=grid_limit
            )

            # Check grid violations
            grid_checker = GridConstraintChecker(grid_export_limit_kw=grid_limit)
            grid_analysis = grid_checker.check_violations(result.grid_export_kw)

            # Calculate baseline (no battery)
            baseline = calculate_baseline_cost(
                solar_kw=scenario.solar_kw,
                load_kw=scenario.load_kw,
                price_gbp_kwh=scenario.price_gbp_kwh
            )

            # Store in session state
            st.session_state.result = result
            st.session_state.scenario = scenario
            st.session_state.grid_analysis = grid_analysis
            st.session_state.baseline = baseline
            st.session_state.asset = asset
        except Exception as exc:  # noqa: BLE001 - streamlit-friendly user feedback
            st.error(f"Optimization failed: {exc}")
            st.stop()

# ============================================================================
# METRICS DASHBOARD (Bloomberg-style)
# ============================================================================

if 'result' in st.session_state:
    result = st.session_state.result
    scenario = st.session_state.scenario
    grid_analysis = st.session_state.grid_analysis
    baseline = st.session_state.baseline
    asset = st.session_state.asset

    st.markdown("### PERFORMANCE METRICS")

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric(
            label="GROSS PROFIT",
            value=f"£{result.net_profit_gbp:.2f}",
            delta=f"vs. baseline: +£{result.net_profit_gbp - baseline['net_gbp']:.2f}"
        )

    with col2:
        st.metric(
            label="DEGRADATION",
            value=f"-£{result.degradation_cost_gbp:.2f}",
            delta=f"{result.cycle_count:.2f} cycles",
            delta_color="inverse"
        )

    with col3:
        st.metric(
            label="NET PROFIT",
            value=f"£{result.effective_profit_gbp:.2f}",
            delta="After battery wear"
        )

    with col4:
        annual_effective = result.effective_profit_gbp * 365
        battery_cost = 7000
        payback = battery_cost / annual_effective if annual_effective > 0 else 999
        st.metric(
            label="PAYBACK PERIOD",
            value=f"{payback:.1f} years",
            delta=f"ROI: {(annual_effective/battery_cost*100):.1f}%"
        )

    with col5:
        st.metric(
            label="SHARPE RATIO",
            value=f"{result.sharpe_ratio:.2f}",
            delta="Risk-adjusted"
        )

    with col6:
        violation_status = "PASS" if grid_analysis['violation_count'] == 0 else "FAIL"
        st.metric(
            label="GRID STATUS",
            value=violation_status,
            delta=f"{grid_analysis['peak_grid_stress']*100:.0f}% stress"
        )

    st.markdown("---")

    # ========================================================================
    # CHART 1: FINANCIAL OPTIMIZATION
    # ========================================================================

    st.markdown("### MARKET ENGINE: Price Arbitrage")

    hours = [ts.hour + ts.minute/60 for ts in scenario.timestamps]

    price_chart = create_price_chart(
        hours=hours,
        price_gbp_kwh=scenario.price_gbp_kwh,
        charge_kw=result.charge_schedule_kw,
        discharge_kw=result.discharge_schedule_kw,
        soc_pct=result.soc_trajectory_pct
    )

    st.plotly_chart(price_chart, use_container_width=True)

    # ========================================================================
    # CHART 2: GRID CONSTRAINT ENFORCEMENT
    # ========================================================================

    st.markdown("### GRID ENGINE: Physical Constraints")

    grid_chart = create_grid_flow_chart(
        hours=hours,
        grid_export_kw=result.grid_export_kw,
        grid_limit_kw=grid_limit
    )

    st.plotly_chart(grid_chart, use_container_width=True)

    # AI-assisted (Codex, 442f313 via PR #41): grid-violations table.
    if grid_analysis.get('violations'):
        st.markdown("#### Grid Violations")
        violation_rows = [asdict(v) for v in grid_analysis['violations']]
        st.dataframe(violation_rows, use_container_width=True, hide_index=True)

    # ========================================================================
    # DETAILED ANALYSIS
    # ========================================================================

    st.markdown("---")
    st.markdown("### DETAILED BREAKDOWN")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Financial Summary")
        annual_cycles = result.cycle_count * 365
        years_to_warranty = 3650 / annual_cycles if annual_cycles > 0 else 999
        st.markdown(f"""
        | Metric | Value |
        |--------|-------|
        | **Revenue (Export)** | £{result.revenue_gbp:.2f} |
        | **Cost (Import)** | £{result.cost_gbp:.2f} |
        | **Gross Profit** | £{result.net_profit_gbp:.2f} |
        | **Battery Degradation** | -£{result.degradation_cost_gbp:.2f} |
        | **Net Profit** | £{result.effective_profit_gbp:.2f} |
        | **Baseline (No Battery)** | £{baseline['net_gbp']:.2f} |
        | **Battery Benefit** | £{result.effective_profit_gbp - baseline['net_gbp']:.2f} |
        | **Annual Projection** | £{result.effective_profit_gbp * 365:.0f} |
        | | |
        | **Daily Cycles** | {result.cycle_count:.2f} |
        | **Annual Cycles** | {annual_cycles:.0f} |
        | **Years to Warranty** | {years_to_warranty:.1f} years |
        """)

    with col2:
        st.markdown("#### Grid Impact")
        st.markdown(f"""
        | Metric | Value |
        |--------|-------|
        | **Max Voltage Rise** | {grid_analysis['max_voltage_rise_pct']:.2f}% |
        | **Peak Grid Stress** | {grid_analysis['peak_grid_stress']*100:.0f}% |
        | **Times at Limit** | {grid_analysis['times_at_limit']} intervals |
        | **G99 Compliant** | {'YES' if grid_analysis['g99_compliant'] else 'NO'} |
        | **Violations** | {grid_analysis['violation_count']} |
        """)

    # ========================================================================
    # SOLVER INFO
    # ========================================================================

    with st.expander("Optimization Details"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Solver Status", result.solver_status)
        with col2:
            st.metric("Solve Time", f"{result.solve_time_ms:.1f} ms")
        with col3:
            st.metric("Variables", f"{len(scenario.solar_kw) * 3 + 1}")

        st.markdown(f"""
        **Configuration:**
        - Battery: {asset.capacity_kwh} kWh @ {asset.power_kw} kW ({asset.efficiency*100:.0f}% efficiency)
        - Grid Limit: {grid_limit} kW
        - Timesteps: {len(scenario.solar_kw)} (15-min resolution)
        - Market Volatility: {scenario.volatility_multiplier}x
        - Solar Intermittency: {scenario.cloud_cover_factor*100:.0f}% cloud cover
        """)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #555; font-size: 12px; padding: 20px 0;'>
    <p>VPP Trading Terminal v2.0 | Linear Programming Optimization Engine</p>
    <p>Built with Streamlit + SciPy + Plotly | For quant traders and grid engineers</p>
</div>
""", unsafe_allow_html=True)
