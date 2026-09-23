# coding: utf-8
"""
Battery Arbitrage Optimization Engine
======================================
Linear Programming solver for profit-maximizing battery scheduling.

Used by quant traders and grid operators for VPP coordination.
"""

import numpy as np
from scipy.optimize import linprog
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class BatteryAsset:
    """Battery system configuration."""
    capacity_kwh: float        # Total energy storage (kWh)
    power_kw: float           # Max charge/discharge rate (kW)
    efficiency: float         # Round-trip efficiency (0-1)
    initial_soc_pct: float    # Starting charge level (%)


from .degradation import BatteryDegradationModel

@dataclass
class OptimizationResult:
    """Trading schedule and performance metrics."""
    charge_schedule_kw: List[float]
    discharge_schedule_kw: List[float]
    soc_trajectory_pct: List[float]
    grid_export_kw: List[float]

    # Financial metrics
    revenue_gbp: float
    cost_gbp: float
    net_profit_gbp: float

    # Trading metrics
    sharpe_ratio: float                   # Risk-adjusted return
    max_drawdown_pct: float               # Worst SoC depletion
    utilization_factor: float             # Battery usage efficiency

    # Solver info
    solver_status: str
    solve_time_ms: float

    # Degradation metrics (with defaults - must come last)
    degradation_cost_gbp: float = 0.0
    effective_profit_gbp: float = 0.0  # net_profit - degradation
    cycle_count: float = 0.0


class BatteryOptimizer:
    """
    Linear Programming optimizer for battery arbitrage.

    Solves the constrained optimization problem:
        Maximize: Σ(Grid_Export × Price)
        Subject to:
            - Battery capacity: 0 <= SoC <= Capacity
            - Power limits: |Charge|, |Discharge| <= Power_Max
            - Grid export limit: Net_Export <= Grid_Limit
            - Energy conservation: SoC dynamics with efficiency

    Uses scipy's HiGHS solver (interior-point method) for fast convergence.

    Example:
        >>> optimizer = BatteryOptimizer(timestep_minutes=15)
        >>> asset = BatteryAsset(capacity_kwh=13.5, power_kw=5.0, efficiency=0.9, initial_soc_pct=50)
        >>> result = optimizer.optimize(asset, solar_kw, load_kw, price_gbp_kwh, grid_limit_kw=4.0)
        >>> print(f"Profit: £{result.net_profit_gbp:.2f}")
    """

    def __init__(self, timestep_minutes: int = 15):
        """
        Initialize optimizer.

        Args:
            timestep_minutes: Time resolution (15 = quarter-hourly)
        """
        self.timestep_hours = timestep_minutes / 60.0

    def optimize(
        self,
        asset: BatteryAsset,
        solar_kw: List[float],
        load_kw: List[float],
        price_gbp_kwh: List[float],
        grid_export_limit_kw: float = 4.0,
        degradation_cost_gbp_kwh: float = 0.05
    ) -> OptimizationResult:
        """
        Solve optimal battery schedule with degradation cost.

        Args:
            asset: Battery configuration
            solar_kw: Solar generation forecast (kW) per interval
            load_kw: Load forecast (kW) per interval
            price_gbp_kwh: Electricity price (GBP/kWh) per interval
            grid_export_limit_kw: Maximum grid export (DNO limit)
            degradation_cost_gbp_kwh: Battery wear cost per kWh cycled (default: £0.05)

        Returns:
            OptimizationResult with schedule and performance metrics
        """
        import time
        start_time = time.time()

        N = len(solar_kw)
        solar = np.array(solar_kw)
        load = np.array(load_kw)
        price = np.array(price_gbp_kwh)

        # Decision variables: [charge_0..N-1, discharge_0..N-1, soc_0..N]
        # Total: 3*N + 1 variables

        # Objective: Maximize revenue = Σ(grid_export × price × dt) - Σ(cycles × degradation_cost)
        # grid_export = solar - load + discharge - charge
        # Minimize negative revenue (with degradation penalty)
        # Only battery terms enter the objective: solar - load is fixed. This assumes
        # import and export are both priced at price[t].
        c = np.zeros(3*N + 1)
        for t in range(N):
            # Charging costs: Electricity price + Degradation wear
            c[t] = (price[t] + degradation_cost_gbp_kwh) * self.timestep_hours

            # Discharging revenue: Electricity price - Degradation wear
            # Battery only trades if profit > degradation cost (realistic behavior)
            c[N + t] = -(price[t] - degradation_cost_gbp_kwh) * self.timestep_hours

        # Inequality constraints: A_ub @ x <= b_ub
        A_ub = []
        b_ub = []

        # Power limits
        for t in range(N):
            # Charge limit
            constraint = np.zeros(3*N + 1)
            constraint[t] = 1
            A_ub.append(constraint)
            b_ub.append(asset.power_kw)

            # Discharge limit
            constraint = np.zeros(3*N + 1)
            constraint[N + t] = 1
            A_ub.append(constraint)
            b_ub.append(asset.power_kw)

        # Capacity limits
        for t in range(N + 1):
            constraint = np.zeros(3*N + 1)
            constraint[2*N + t] = 1
            A_ub.append(constraint)
            b_ub.append(asset.capacity_kwh)

        # Grid export limit (THE KEY CONSTRAINT)
        for t in range(N):
            constraint = np.zeros(3*N + 1)
            constraint[N + t] = 1   # discharge
            constraint[t] = -1      # charge (negative)
            A_ub.append(constraint)
            # If solar > load, less discharge headroom
            b_ub.append(grid_export_limit_kw - (solar[t] - load[t]))

        A_ub = np.array(A_ub)
        b_ub = np.array(b_ub)

        # Equality constraints: A_eq @ x = b_eq
        A_eq = []
        b_eq = []

        # Battery dynamics: SoC[t+1] = SoC[t] + (η*charge - discharge/η)*dt
        # Split the round-trip loss evenly between charging and discharging.
        eta_charge = np.sqrt(asset.efficiency)
        eta_discharge = np.sqrt(asset.efficiency)

        for t in range(N):
            constraint = np.zeros(3*N + 1)
            constraint[2*N + t + 1] = 1  # SoC[t+1]
            constraint[2*N + t] = -1     # SoC[t]
            constraint[t] = -eta_charge * self.timestep_hours
            constraint[N + t] = 1/eta_discharge * self.timestep_hours
            A_eq.append(constraint)
            b_eq.append(0)

        # Initial SoC
        initial_soc = np.zeros(3*N + 1)
        initial_soc[2*N] = 1
        A_eq.append(initial_soc)
        b_eq.append((asset.initial_soc_pct / 100) * asset.capacity_kwh)

        A_eq = np.array(A_eq)
        b_eq = np.array(b_eq)

        # Variable bounds: All non-negative
        bounds = [(0, None)] * (3*N + 1)

        # Solve LP
        result = linprog(
            c=c,
            A_ub=A_ub,
            b_ub=b_ub,
            A_eq=A_eq,
            b_eq=b_eq,
            bounds=bounds,
            method='highs'
        )

        solve_time = (time.time() - start_time) * 1000  # ms

        if not result.success:
            raise RuntimeError(f"Optimization failed: {result.message}")

        # Extract solution
        x = result.x
        charge = x[:N]
        discharge = x[N:2*N]
        soc_kwh = x[2*N:2*N+N]
        soc_pct = (soc_kwh / asset.capacity_kwh * 100).tolist()

        grid_export = (solar - load + discharge - charge).tolist()

        # Calculate financial metrics
        grid_import = np.maximum(0, -np.array(grid_export))
        grid_export_pos = np.maximum(0, grid_export)

        cost = np.sum(grid_import * price * self.timestep_hours)
        revenue = np.sum(grid_export_pos * price * self.timestep_hours)
        net_profit = revenue - cost

        # Calculate trading metrics
        sharpe_ratio = self._calculate_sharpe(discharge.tolist(), price.tolist())
        max_drawdown = 100 - np.min(soc_kwh / asset.capacity_kwh * 100)
        utilization = np.sum(discharge) * self.timestep_hours / asset.capacity_kwh

        # Calculate degradation cost
        degradation_model = BatteryDegradationModel(
            battery_capacity_kwh=asset.capacity_kwh
        )

        degradation_cost = degradation_model.calculate_degradation_cost(
            discharge_kw=discharge.tolist(),
            timestep_hours=self.timestep_hours
        )

        cycle_count = degradation_model.calculate_cycle_count(
            discharge_kw=discharge.tolist(),
            timestep_hours=self.timestep_hours
        )

        effective_profit = net_profit - degradation_cost

        return OptimizationResult(
            charge_schedule_kw=charge.tolist(),
            discharge_schedule_kw=discharge.tolist(),
            soc_trajectory_pct=soc_pct,
            grid_export_kw=grid_export,
            revenue_gbp=float(revenue),
            cost_gbp=float(cost),
            net_profit_gbp=float(net_profit),
            sharpe_ratio=float(sharpe_ratio),
            max_drawdown_pct=float(max_drawdown),
            utilization_factor=float(utilization),
            solver_status=result.message,
            solve_time_ms=float(solve_time),
            degradation_cost_gbp=float(degradation_cost),
            effective_profit_gbp=float(effective_profit),
            cycle_count=float(cycle_count)
        )

    def _calculate_sharpe(self, discharge: List[float], price: List[float]) -> float:
        """
        Calculate Sharpe ratio for trading strategy.

        Measures risk-adjusted return:
            Sharpe = mean(returns) / std(returns)

        Higher Sharpe = better risk-adjusted performance.
        """
        returns = np.array(discharge) * np.array(price)
        if len(returns) == 0 or np.std(returns) == 0:
            return 0.0
        return np.mean(returns) / np.std(returns)


def calculate_baseline_cost(
    solar_kw: List[float],
    load_kw: List[float],
    price_gbp_kwh: List[float],
    timestep_hours: float = 0.25
) -> Dict[str, float]:
    """
    Calculate baseline cost without battery (benchmark).

    Args:
        solar_kw: Solar generation
        load_kw: Load consumption
        price_gbp_kwh: Electricity price
        timestep_hours: Time resolution

    Returns:
        Dictionary with cost, revenue, net metrics
    """
    grid_no_battery = np.array(solar_kw) - np.array(load_kw)
    import_no_battery = np.maximum(0, -grid_no_battery)
    export_no_battery = np.maximum(0, grid_no_battery)

    # Use 50% export tariff (typical UK SEG rate vs. import rate)
    cost = np.sum(import_no_battery * np.array(price_gbp_kwh) * timestep_hours)
    revenue = np.sum(export_no_battery * np.array(price_gbp_kwh) * 0.5 * timestep_hours)

    return {
        'cost_gbp': float(cost),
        'revenue_gbp': float(revenue),
        'net_gbp': float(revenue - cost)
    }
