"""
Metrics and Impact Calculator for AegisFlow.
Computes quantitative clinical, deprivation, and environmental KPIs.
"""

from typing import Dict, Any

def compute_impact_scorecard(
    baseline_metrics: Dict[str, Any],
    optimized_metrics: Dict[str, Any],
    total_km_traveled: float
) -> Dict[str, Any]:
    """
    Calculates quantifiable impact deltas across healthcare resilience,
    deprivation penalties, and carbon emissions.
    """
    base_stockouts = baseline_metrics.get("stockouts_under_24h", 0)
    opt_stockouts = optimized_metrics.get("stockouts_under_24h", 0)
    stockouts_prevented = max(0, base_stockouts - opt_stockouts)

    base_deprivation = baseline_metrics.get("deprivation_penalty", 10.0)
    opt_deprivation = optimized_metrics.get("deprivation_penalty", 0.0)
    deprivation_reduction = max(0.0, base_deprivation - opt_deprivation)
    deprivation_reduction_pct = (
        (deprivation_reduction / base_deprivation * 100.0) if base_deprivation > 0 else 0.0
    )

    # Transport Environmental Impact (GHG Protocol Scope 1 Mobile Combustion)
    # Diesel freight emission factor ~ 0.78 kg CO2e per vehicle-km (heavy commercial truck)
    estimated_co2_kg = total_km_traveled * 0.782

    # Estimated emergency cost: ₹85 per km heavy transport operating cost
    estimated_fuel_cost_inr = total_km_traveled * 85.0

    return {
        "stockouts_prevented_24h": stockouts_prevented,
        "deprivation_reduction_pct": round(deprivation_reduction_pct, 1),
        "deprivation_points_saved": round(deprivation_reduction, 1),
        "total_transit_km": round(total_km_traveled, 1),
        "estimated_co2_kg": round(estimated_co2_kg, 1),
        "estimated_logistics_cost_inr": round(estimated_fuel_cost_inr, 2)
    }
