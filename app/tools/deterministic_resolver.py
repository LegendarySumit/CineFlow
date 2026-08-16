"""
LAYER 3: DETERMINISTIC RESOLVER

Forces crisis analysis output to be actionable and financially justified.
Returns exact scene IDs and ROI, not vague suggestions.
"""

from typing import Any

from app.tools.cost_calculator import calculate_recovery_cost
from app.tools.unified_risk_engine import find_compatible_swaps


def resolve_crisis_deterministically(
    scene_id: str,
    affected_resource: str,
    crisis_type: str,
    duration_hours: int,
    dataset: dict[str, Any]
) -> dict[str, Any]:
    """
    LAYER 3 OUTPUT: Exact, actionable resolution with financial analysis.
    
    Returns: {
        "action": "SWAP" | "WAIT" | "MODIFY",
        "source_scene": "sc_42",
        "target_scene": "sc_18",
        "action_reason": "Interior scene with zero conflict for WEATHER disruption",
        "cost_analysis": {...},
        "executive_decision": {"recommendation": "EXECUTE_SWAP", "confidence": "HIGH"}
    }
    """
    
    # Find compatible swaps
    compatible_scenes = find_compatible_swaps(
        scene_id,
        affected_resource,
        crisis_type,
        dataset
    )
    
    if not compatible_scenes:
        return {
            "status": "error",
            "message": f"No compatible swap found for {crisis_type} crisis"
        }
    
    # Take the best compatible scene
    best_option = compatible_scenes[0]
    target_scene = best_option["scene_id"]
    
    # Calculate recovery cost
    cost_analysis = calculate_recovery_cost(scene_id, target_scene, dataset)
    
    return {
        "status": "success",
        "action": "SWAP",
        "source_scene": scene_id,
        "target_scene": target_scene,
        "action_reason": best_option.get("reasoning", "Compatible scene swap"),
        "compatibility_score": best_option.get("compatibility_score", 0),
        "cost_analysis": cost_analysis.get("benefit", {}),
        "one_time_costs": cost_analysis.get("one_time_costs", {}),
        "affected_location": affected_resource,
        "duration_hours": duration_hours,
        "timeline": {
            "can_execute_by": "Next available call sheet",
            "expected_completion": "Day TBD"
        },
        "executive_decision": {
            "recommendation": "EXECUTE_SWAP" if cost_analysis.get("benefit", {}).get("net_economic_benefit", 0) > 0 else "REVIEW",
            "confidence": "HIGH",
            "justification": f"Net economic benefit of ₹{cost_analysis.get('benefit', {}).get('net_economic_benefit', 0):,.0f}"
        }
    }
