"""
LAYER 2: COST CALCULATOR

Computes financial impact of disruptions.
This is what makes the agent ECONOMICALLY AWARE.
Works with both old and new dataset formats.
"""

from typing import Any

from app.tools.format_compat import detect_format, get_scene_cast_ids, get_scene_equipment_ids
from app.tools.production import get_scene_by_id

# Production cost baselines (in INR, adjustable per production)
DAILY_CREW_COST = 150000  # Daily crew holding cost
DAILY_EQUIPMENT_COST = 50000  # Daily equipment rental
ACTOR_PER_DIEM = 10000  # Per-day per actor
LOCATION_PERMIT_DAILY = 5000  # Location permit daily fee
OVERHEAD_COST_PER_DAY = 100000  # General overhead (admin, logistics, etc.)

# Total daily production burn
DAILY_PRODUCTION_COST = (
    DAILY_CREW_COST +
    DAILY_EQUIPMENT_COST +
    OVERHEAD_COST_PER_DAY
)


def calculate_disruption_cost(
    affected_scenes: list[dict[str, Any]],
    duration_hours: int,
    dataset: dict[str, Any]
) -> dict[str, Any]:
    """
    Calculate the financial cost of a disruption.
    
    Returns:
    {
        "total_cost_inr": 305000,
        "daily_burn": 305000,
        "hourly_burn": 12708,
        "affected_scene_count": 2,
        "affected_actor_count": 3,
        "breakdown": {...}
    }
    """
    
    # Handle None duration_hours (default to 24 hours = 1 day)
    if duration_hours is None:
        duration_hours = 24
    duration_days = max(1, duration_hours / 8)  # Assume 8-hour shoot day
    
    # Count unique actors affected
    is_new_fmt = (detect_format(dataset) == 'new')
    actors_set = set()
    equipment_set = set()
    for scene in affected_scenes:
        scene_id = scene.get("scene_id")
        scene_obj = get_scene_by_id(scene_id, dataset)
        if scene_obj:
            actors_set.update(get_scene_cast_ids(scene_obj, is_new_fmt))
            equipment_set.update(get_scene_equipment_ids(scene_obj, is_new_fmt))
    
    affected_actor_count = len(actors_set)
    affected_equipment_count = len(equipment_set)
    
    # Calculate costs
    crew_cost = DAILY_CREW_COST * duration_days
    equipment_cost = DAILY_EQUIPMENT_COST * duration_days
    actor_cost = ACTOR_PER_DIEM * affected_actor_count * duration_days
    overhead_cost = OVERHEAD_COST_PER_DAY * duration_days
    
    total_cost = crew_cost + equipment_cost + actor_cost + overhead_cost
    hourly_burn = DAILY_PRODUCTION_COST / 8
    
    return {
        "status": "success",
        "disruption_impact": {
            "total_cost_inr": int(total_cost),
            "daily_burn": int(DAILY_PRODUCTION_COST),
            "hourly_burn": int(hourly_burn),
            "duration_days": duration_days,
            "duration_hours": duration_hours
        },
        "affected_resources": {
            "scene_count": len(affected_scenes),
            "actor_count": affected_actor_count,
            "equipment_count": affected_equipment_count
        },
        "cost_breakdown": {
            "crew_holding_cost": int(crew_cost),
            "equipment_rental": int(equipment_cost),
            "actor_per_diem": int(actor_cost),
            "overhead": int(overhead_cost)
        }
    }


def calculate_recovery_cost(
    source_scene_id: str,
    target_scene_id: str,
    dataset: dict[str, Any]
) -> dict[str, Any]:
    """
    Calculate the cost of a scene swap (recovery action).
    
    Returns the marginal cost difference between swapping vs. stagnating.
    """
    
    scenes = dataset.get("scenes", [])
    source = next((s for s in scenes if s["scene_id"] == source_scene_id), None)
    target = next((s for s in scenes if s["scene_id"] == target_scene_id), None)
    
    if not source or not target:
        return {"error": "Scene not found"}
    
    # Recovery costs (one-time)
    crew_mobilization = 25000  # Crew repositioning
    equipment_setup = 15000  # Camera/light setup at new location
    actor_rework = 5000  # Re-scheduling actors
    logistics = 10000  # Transport, catering adjustments
    
    total_recovery_cost = crew_mobilization + equipment_setup + actor_rework + logistics
    
    # Benefits: reduced idle cost by shooting immediately
    idle_cost_saved = DAILY_PRODUCTION_COST  # Save 1 day of burn
    
    net_benefit = idle_cost_saved - total_recovery_cost
    
    return {
        "status": "success",
        "recovery_action": f"Swap {source_scene_id} ↔ {target_scene_id}",
        "one_time_costs": {
            "crew_mobilization": crew_mobilization,
            "equipment_setup": equipment_setup,
            "actor_rework": actor_rework,
            "logistics": logistics,
            "total": total_recovery_cost
        },
        "benefit": {
            "idle_cost_saved": int(idle_cost_saved),
            "net_economic_benefit": int(net_benefit),
            "roi_percentage": (net_benefit / total_recovery_cost * 100) if total_recovery_cost > 0 else 0
        }
    }
