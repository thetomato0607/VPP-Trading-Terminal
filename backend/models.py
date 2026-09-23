"""Pydantic request/response schemas for the FastAPI backend."""

from pydantic import BaseModel
from typing import List, Optional

class OnboardingRequest(BaseModel):
    """User onboarding payload; not referenced by any current route."""
    user_id: str
    location: str
    has_panels: bool
    energy_bill: str
    goal: str

class SummaryResponse(BaseModel):
    """Daily savings summary; not referenced by any current route."""
    user_id: str
    daily_saving_gbp: float
    co2_offset_kg: float
    battery_status: str
    message: str

class VPPOptimizationRequest(BaseModel):
    """Request model for VPP optimization."""
    solar_forecast_kw: List[float]
    load_forecast_kw: Optional[List[float]] = None
    price_forecast_gbp_kwh: Optional[List[float]] = None
    battery_capacity_kwh: float = 13.5
    battery_power_kw: float = 5.0
    grid_export_limit_kw: float = 4.0
    initial_soc_pct: float = 50.0

class VPPOptimizationResult(BaseModel):
    """Response model for VPP optimization."""
    battery_charge_kw: List[float]
    battery_discharge_kw: List[float]
    soc_pct: List[float]
    grid_export_kw: List[float]
    revenue_gbp: float
    energy_cost_gbp: float
    net_profit_gbp: float
    success: bool
    message: str

class GridImpactAnalysis(BaseModel):
    """Grid impact metrics."""
    max_voltage_rise_V: float
    max_voltage_rise_pct: float
    peak_grid_stress: float
    times_at_limit: int
    g99_compliant: bool

class VPPSimulationResponse(BaseModel):
    """Complete VPP simulation response."""
    simulation_date: str
    inputs: dict
    forecasts: dict
    optimization: VPPOptimizationResult
    grid_impact: GridImpactAnalysis
    summary: dict
