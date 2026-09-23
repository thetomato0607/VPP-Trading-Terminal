"""Battery degradation cost model used to report wear cost after optimisation."""

import numpy as np
from typing import List

class BatteryDegradationModel:
    """Battery wear cost derived from a Tesla Powerwall-style warranty.

    Warranty assumptions (defaults):
    - 70% capacity retained after 3,650 cycles (about 10 years)
    - Replacement cost £7,000, so lost value is £7,000 x 30% = £2,100

    Cost per cycle: £2,100 / 3,650 = £0.58; per kWh: £0.58 / 13.5 kWh = £0.043.
    """
    
    def __init__(
        self,
        battery_capacity_kwh: float = 13.5,
        warranty_cycles: int = 3650,
        replacement_cost_gbp: float = 7000,
        capacity_retention_pct: float = 70
    ):
        self.capacity = battery_capacity_kwh
        self.warranty_cycles = warranty_cycles
        self.replacement_cost = replacement_cost_gbp
        self.retention = capacity_retention_pct / 100
        
        # Calculate degradation cost per full cycle
        degradation_value = replacement_cost_gbp * (1 - self.retention)
        self.cost_per_cycle = degradation_value / warranty_cycles
        
    def calculate_degradation_cost(
        self,
        discharge_kw: List[float],
        timestep_hours: float = 0.25
    ) -> float:
        """Return the wear cost (GBP) of a discharge schedule.

        Squares each timestep's discharged energy as a fraction of capacity:
            cost = sum_t (discharge_kwh_t / capacity) ** 2 * cost_per_cycle

        The square is applied per timestep, not per charge/discharge cycle, so the
        result depends on ``timestep_hours``: a full discharge spread over many
        short steps costs far less than one cycle.
        """
        discharge_kwh = np.array(discharge_kw) * timestep_hours
        depth_of_discharge = discharge_kwh / self.capacity
        
        # Quadratic penalty, intended to make deep discharges wear faster.
        cycle_equivalent = np.sum(depth_of_discharge ** 2)
        
        degradation_cost = cycle_equivalent * self.cost_per_cycle
        
        return float(degradation_cost)
    
    def calculate_cycle_count(
        self,
        discharge_kw: List[float],
        timestep_hours: float = 0.25
    ) -> float:
        """Return equivalent full cycles: total discharged energy divided by capacity."""
        total_discharge_kwh = np.sum(discharge_kw) * timestep_hours
        cycles = total_discharge_kwh / self.capacity
        return float(cycles)