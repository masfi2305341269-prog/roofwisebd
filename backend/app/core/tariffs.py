"""
Bangladesh Residential Electricity Tariff Engine
------------------------------------------------
Implements the verified BERC 2026 Tariff Schedule (incorporating the June 4, 2026 correction
which restored the first two residential tiers).

Slab Schedule (Residential):
- Lifeline (0 - 50 kWh): Tk 4.63 / kWh
- First step (up to 75 kWh): Tk 5.26 / kWh
- 76 - 200 kWh: Tk 8.50 / kWh
- 201 - 300 kWh: Tk 9.10 / kWh
- 301 - 400 kWh: Tk 9.62 / kWh
- 401 - 600 kWh: Tk 15.01 / kWh
- Above 600 kWh: Tk 17.03 / kWh

Features:
- Configurable effective date schedule
- Official progressive slab calculation method
- Distinct separation of energy charges, demand charges, meter rent, and configurable VAT
- Savings computation against solar offset
"""

from typing import Dict, Any, List, Optional
from datetime import date

# Configurable Tariff Schedules by Effective Date
BERC_TARIFF_SCHEDULES = {
    "2026-06-04": {
        "version": "BERC 2026 (June 4 Revision)",
        "effective_date": "2026-06-04",
        "lifeline_limit": 50.0,
        "lifeline_rate": 4.63,
        "slabs": [
            {"name": "0-75", "limit": 75.0, "rate": 5.26},
            {"name": "76-200", "limit": 125.0, "rate": 8.50},   # 200 - 75 = 125 units
            {"name": "201-300", "limit": 100.0, "rate": 9.10},  # 300 - 200 = 100 units
            {"name": "301-400", "limit": 100.0, "rate": 9.62},  # 400 - 300 = 100 units
            {"name": "401-600", "limit": 200.0, "rate": 15.01}, # 600 - 400 = 200 units
            {"name": "Above 600", "limit": float("inf"), "rate": 17.03}
        ],
        "default_demand_charge_per_kw": 35.0,
        "default_meter_rent": 40.0,
        "default_vat_rate": 0.05
    }
}

ACTIVE_SCHEDULE_KEY = "2026-06-04"

def get_tariff_schedule(schedule_key: Optional[str] = None) -> Dict[str, Any]:
    key = schedule_key or ACTIVE_SCHEDULE_KEY
    if key not in BERC_TARIFF_SCHEDULES:
        key = ACTIVE_SCHEDULE_KEY
    return BERC_TARIFF_SCHEDULES[key]

def calculate_bangladesh_residential_bill(
    units_kwh: float,
    sanctioned_load_kw: float = 2.0,
    meter_rent: Optional[float] = None,
    vat_rate: Optional[float] = None,
    demand_charge_per_kw: Optional[float] = None,
    schedule_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Computes total residential electricity bill (BDT) given monthly kWh units
    under the active BERC tariff schedule.
    """
    schedule = get_tariff_schedule(schedule_key)
    
    # Use defaults from schedule if not overridden
    meter_rent_val = meter_rent if meter_rent is not None else schedule["default_meter_rent"]
    vat_rate_val = vat_rate if vat_rate is not None else schedule["default_vat_rate"]
    demand_rate_val = demand_charge_per_kw if demand_charge_per_kw is not None else schedule["default_demand_charge_per_kw"]
    
    demand_charge = max(0.0, sanctioned_load_kw * demand_rate_val)
    
    if units_kwh <= 0:
        vat = demand_charge * vat_rate_val
        total = demand_charge + meter_rent_val + vat
        return {
            "schedule_version": schedule["version"],
            "units_kwh": 0.0,
            "energy_charge_bdt": 0.0,
            "demand_charge_bdt": round(demand_charge, 2),
            "meter_rent_bdt": round(meter_rent_val, 2),
            "vat_bdt": round(vat, 2),
            "total_bill_bdt": round(total, 2),
            "effective_rate_per_kwh": 0.0,
            "slab_breakdown": []
        }

    slab_breakdown: List[Dict[str, Any]] = []
    energy_charge = 0.0

    # 1. Lifeline condition: consumption <= 50 units
    if units_kwh <= schedule["lifeline_limit"]:
        lifeline_rate = schedule["lifeline_rate"]
        cost = units_kwh * lifeline_rate
        energy_charge = cost
        slab_breakdown.append({
            "slab": f"0-{int(schedule['lifeline_limit'])} (Lifeline)",
            "units": units_kwh,
            "rate": lifeline_rate,
            "cost_bdt": round(cost, 2)
        })
    else:
        # Standard progressive slab billing
        remaining = units_kwh
        for slab in schedule["slabs"]:
            if remaining <= 0:
                break
            slab_limit = slab["limit"]
            slab_rate = slab["rate"]
            slab_name = slab["name"]
            
            units_in_slab = min(remaining, slab_limit)
            cost_in_slab = units_in_slab * slab_rate
            energy_charge += cost_in_slab
            remaining -= units_in_slab
            
            slab_breakdown.append({
                "slab": slab_name,
                "units": round(units_in_slab, 2),
                "rate": slab_rate,
                "cost_bdt": round(cost_in_slab, 2)
            })

    # Subtotal subject to VAT
    taxable_subtotal = energy_charge + demand_charge
    vat = taxable_subtotal * vat_rate_val
    total_bill = taxable_subtotal + meter_rent_val + vat
    effective_rate = round(energy_charge / units_kwh, 2) if units_kwh > 0 else 0.0

    return {
        "schedule_version": schedule["version"],
        "units_kwh": round(units_kwh, 2),
        "energy_charge_bdt": round(energy_charge, 2),
        "demand_charge_bdt": round(demand_charge, 2),
        "meter_rent_bdt": round(meter_rent_val, 2),
        "vat_rate_percent": round(vat_rate_val * 100, 1),
        "vat_bdt": round(vat, 2),
        "total_bill_bdt": round(total_bill, 2),
        "effective_rate_per_kwh": effective_rate,
        "slab_breakdown": slab_breakdown
    }

def calculate_solar_bill_savings(
    original_units_kwh: float,
    solar_generated_kwh: float,
    sanctioned_load_kw: float = 2.0,
    meter_rent: Optional[float] = None,
    vat_rate: Optional[float] = None,
    schedule_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculates the financial savings in BDT resulting from solar electricity generation.
    Takes into account that solar offsets high-tier tariff units first.
    """
    bill_before = calculate_bangladesh_residential_bill(
        units_kwh=original_units_kwh,
        sanctioned_load_kw=sanctioned_load_kw,
        meter_rent=meter_rent,
        vat_rate=vat_rate,
        schedule_key=schedule_key
    )
    
    net_grid_units = max(0.0, original_units_kwh - solar_generated_kwh)
    solar_surplus_units = max(0.0, solar_generated_kwh - original_units_kwh)
    
    bill_after = calculate_bangladesh_residential_bill(
        units_kwh=net_grid_units,
        sanctioned_load_kw=sanctioned_load_kw,
        meter_rent=meter_rent,
        vat_rate=vat_rate,
        schedule_key=schedule_key
    )
    
    monthly_savings = max(0.0, bill_before["total_bill_bdt"] - bill_after["total_bill_bdt"])
    annual_savings = monthly_savings * 12.0
    
    offset_pct = min(100.0, round((solar_generated_kwh / original_units_kwh) * 100, 1)) if original_units_kwh > 0 else 0.0

    return {
        "original_units_kwh": original_units_kwh,
        "solar_generated_kwh": round(solar_generated_kwh, 1),
        "net_grid_units_kwh": round(net_grid_units, 1),
        "solar_surplus_units_kwh": round(solar_surplus_units, 1),
        "original_bill_bdt": bill_before["total_bill_bdt"],
        "post_solar_bill_bdt": bill_after["total_bill_bdt"],
        "monthly_savings_bdt": round(monthly_savings, 2),
        "annual_savings_bdt": round(annual_savings, 2),
        "offset_percentage": offset_pct,
        "tariff_schedule_used": bill_before["schedule_version"]
    }
