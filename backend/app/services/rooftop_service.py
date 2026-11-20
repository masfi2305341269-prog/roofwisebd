"""
RoofwiseBD Rooftop Analysis Service
-----------------------------------
Calculates usable rooftop area, layout constraints, shading derating factors,
and installable DC capacity for residential buildings in Bangladesh.
"""

from typing import Dict, Any, Optional
from app.core.config import settings
from app.schemas.rooftop import RooftopAnalysisRequest, RooftopAnalysisResponse

SHADING_DERATE_FACTORS = {
    "none": 1.00,
    "low": 0.95,
    "medium": 0.85,
    "heavy": 0.70
}

ROOF_USABLE_RATIOS = {
    "concrete_flat": 0.70,  # 30% allowance for parapet wall setback, water tank, staircase headroom
    "tin_shed": 0.78,       # Sloped tin roof allows higher contiguous coverage
    "tiled": 0.65           # Steeper pitch and weight limitations
}

def analyze_rooftop_potential(req: RooftopAnalysisRequest) -> RooftopAnalysisResponse:
    total_area = req.total_area_sqft
    roof_type = req.roof_type if req.roof_type in ROOF_USABLE_RATIOS else "concrete_flat"
    shading = req.shading_condition if req.shading_condition in SHADING_DERATE_FACTORS else "low"
    
    # 1. Determine usable area
    if req.manual_usable_area_sqft and req.manual_usable_area_sqft > 0:
        usable_area = min(total_area, req.manual_usable_area_sqft)
        usable_ratio = round(usable_area / total_area, 2)
    else:
        usable_ratio = ROOF_USABLE_RATIOS[roof_type]
        usable_area = round(total_area * usable_ratio, 1)

    # 2. Area required per kWp based on roof type
    sqft_per_kwp = settings.DEFAULT_TIN_SQFT_PER_KWP if roof_type == "tin_shed" else settings.DEFAULT_SQFT_PER_KWP
    shading_factor = SHADING_DERATE_FACTORS[shading]

    # 3. Maximum installable DC capacity
    panel_wattage = req.panel_wattage_wp or settings.DEFAULT_PANEL_WATTAGE_WP
    panel_area = settings.DEFAULT_PANEL_AREA_SQFT

    # Spatial layout estimation (accounting for panel rows and inter-row tilt shadow clearance)
    max_panels = int(usable_area / (panel_area * 1.35)) if roof_type == "concrete_flat" else int(usable_area / (panel_area * 1.15))
    max_panels = max(1, max_panels) if usable_area >= 60 else 0
    
    estimated_kwp = round((max_panels * panel_wattage) / 1000.0, 2)

    note = (
        f"Calculated {usable_area} sq ft usable area ({int(usable_ratio * 100)}% of gross). "
        f"Accommodates up to ~{max_panels} monocrystalline panels ({panel_wattage}W each) "
        f"with south-facing orientation and tilt clearance."
    )

    return RooftopAnalysisResponse(
        total_area_sqft=total_area,
        usable_area_sqft=usable_area,
        usable_ratio=usable_ratio,
        roof_type=roof_type,
        shading_condition=shading,
        shading_derate_factor=shading_factor,
        estimated_max_capacity_kwp=estimated_kwp,
        max_panel_count=max_panels,
        panel_specification=f"{panel_wattage}Wp Monocrystalline PERC (~{panel_area} sq ft/panel)",
        structural_disclaimer=settings.STRUCTURAL_DISCLAIMER,
        recommendation_note=note
    )
