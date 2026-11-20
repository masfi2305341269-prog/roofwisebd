"""
RoofwiseBD Battery Optimization Service
---------------------------------------
Calculates critical load requirements, usable and nominal battery capacities,
and preliminary dispatch schedules based on user-entered appliance inventories.
"""

from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.schemas.battery import (
    BatteryOptimizationRequest,
    BatteryOptimizationResponse,
    BatteryDispatchHour
)

DEFAULT_DOD = {
    "lifepo4": 0.85,    # 85% Depth of Discharge for Lithium Iron Phosphate
    "lead_acid": 0.50   # 50% Depth of Discharge for Deep-Cycle Tubular
}

DEFAULT_INVERTER_EFF = 0.90  # 90% roundtrip/inverter efficiency

def optimize_battery_storage(req: BatteryOptimizationRequest) -> BatteryOptimizationResponse:
    # 1. Calculate Critical Load in Watts and appliance count
    critical_load_watts = 0.0
    total_appliances = 0
    
    for app in req.appliances:
        count = app.quantity
        total_appliances += count
        if app.is_critical:
            critical_load_watts += (app.wattage * count)
            
    # Default to non-zero fallback if user submitted empty list
    if critical_load_watts <= 0:
        critical_load_watts = 350.0  # Approx: 3 ceiling fans + 4 LED bulbs + 1 router

    # 2. Configurable Depth of Discharge and Inverter Efficiency
    chem = req.battery_chemistry.lower() if req.battery_chemistry.lower() in DEFAULT_DOD else "lifepo4"
    dod = req.custom_dod if req.custom_dod is not None else DEFAULT_DOD[chem]
    inverter_eff = req.custom_inverter_eff if req.custom_inverter_eff is not None else DEFAULT_INVERTER_EFF
    safety_margin = req.safety_margin or 1.15

    # 3. Required Backup Energy (Watt-hours)
    # Energy = Critical Load (W) * Backup Hours * Safety Margin
    backup_hours = req.required_backup_hours
    backup_energy_wh = critical_load_watts * backup_hours * safety_margin

    # 4. Usable Capacity (kWh)
    # Usable = Backup Energy / (Inverter Efficiency * 1000)
    usable_kwh = round(backup_energy_wh / (inverter_eff * 1000.0), 2)

    # 5. Nominal Battery Capacity (kWh)
    # Nominal = Usable / DoD
    nominal_kwh = round(usable_kwh / dod, 2)

    # 6. Cost Estimation in BDT
    if chem == "lifepo4":
        cost_min = round(nominal_kwh * settings.HYBRID_BATTERY_ADDON_PER_KWH_BDT * 0.90, 0)
        cost_max = round(nominal_kwh * settings.HYBRID_BATTERY_ADDON_PER_KWH_BDT * 1.15, 0)
    else:
        cost_min = round(nominal_kwh * settings.LEAD_ACID_ADDON_PER_KWH_BDT * 0.90, 0)
        cost_max = round(nominal_kwh * settings.LEAD_ACID_ADDON_PER_KWH_BDT * 1.15, 0)

    # 7. Preliminary 24-Hour Schedule Profile
    # Generates a typical residential day: Solar charging mid-day, evening peak backup
    schedule: List[BatteryDispatchHour] = []
    for h in range(24):
        solar_active = 9 <= h <= 15
        evening_peak = 18 <= h <= 22
        
        if solar_active:
            soc = min(100.0, round(60.0 + (h - 9) * 6.5, 1))
            mode = "Solar Charging & Grid Offset"
            grid = True
            load = critical_load_watts * 0.8
        elif evening_peak:
            soc = max(100.0 - (dod * 100.0), round(100.0 - (h - 18 + 1) * 12.0, 1))
            mode = "Battery Backup / Peak Shaving"
            grid = False  # Simulating evening load-shedding or intentional peak reduction
            load = critical_load_watts
        else:
            soc = 85.0
            mode = "Float / Standby"
            grid = True
            load = critical_load_watts * 0.5
            
        schedule.append(BatteryDispatchHour(
            hour=h,
            grid_available=grid,
            solar_available=solar_active,
            load_watts=round(load, 1),
            battery_soc_pct=soc,
            mode=mode
        ))

    explanation = (
        f"Configured for {critical_load_watts:.0f}W critical load over {backup_hours} hours backup. "
        f"Using {chem.upper()} chemistry (DoD: {int(dod * 100)}%, Inverter Efficiency: {int(inverter_eff * 100)}%, "
        f"Safety Factor: {safety_margin:.2f})."
    )

    preliminary_notice = (
        "Preliminary Planning Profile: The 24-hour dispatch schedule is an engineering planning model. "
        "Actual dispatch depends on real-time solar yield, grid outage patterns from the local utility, "
        "and sub-metered critical branch circuits."
    )

    return BatteryOptimizationResponse(
        total_critical_load_watts=round(critical_load_watts, 1),
        total_appliance_count=total_appliances,
        required_backup_energy_wh=round(backup_energy_wh, 1),
        usable_capacity_required_kwh=usable_kwh,
        recommended_nominal_capacity_kwh=nominal_kwh,
        battery_chemistry=chem,
        dod_used=dod,
        inverter_eff_used=inverter_eff,
        est_battery_cost_bdt_min=cost_min,
        est_battery_cost_bdt_max=cost_max,
        schedule_profile=schedule,
        optimization_explanation=explanation,
        preliminary_notice=preliminary_notice
    )
