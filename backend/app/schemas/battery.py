from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class ApplianceItem(BaseModel):
    name: str
    wattage: float = Field(..., gt=0, example=75.0)
    quantity: int = Field(1, ge=1, example=3)
    daily_usage_hours: float = Field(..., ge=0, le=24, example=8.0)
    is_critical: bool = True

class BatteryOptimizationRequest(BaseModel):
    appliances: List[ApplianceItem]
    required_backup_hours: float = Field(..., ge=0.5, le=48.0, example=4.0)
    battery_chemistry: str = Field("lifepo4", example="lifepo4") # lifepo4 or lead_acid
    custom_dod: Optional[float] = Field(None, ge=0.3, le=0.95, description="Custom Depth of Discharge fraction")
    custom_inverter_eff: Optional[float] = Field(None, ge=0.70, le=0.98, description="Inverter efficiency fraction")
    safety_margin: Optional[float] = Field(1.15, ge=1.0, le=1.5, description="Surge / safety factor")

class BatteryDispatchHour(BaseModel):
    hour: int
    grid_available: bool
    solar_available: bool
    load_watts: float
    battery_soc_pct: float
    mode: str # "Solar Charging", "Grid Idle", "Discharging Backup"

class BatteryOptimizationResponse(BaseModel):
    total_critical_load_watts: float
    total_appliance_count: int
    required_backup_energy_wh: float
    usable_capacity_required_kwh: float
    recommended_nominal_capacity_kwh: float
    battery_chemistry: str
    dod_used: float
    inverter_eff_used: float
    est_battery_cost_bdt_min: float
    est_battery_cost_bdt_max: float
    schedule_profile: List[BatteryDispatchHour]
    optimization_explanation: str
    preliminary_notice: str
