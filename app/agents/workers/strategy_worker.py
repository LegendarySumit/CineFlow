"""
STRATEGY WORKER - Generalized impact evaluation and recovery planning.

Now uses:
- Entity Extractor (LAYER 1): Dynamic entity mapping
- Unified Risk Engine (Base): Crisis classification
- Cost Calculator (LAYER 2): Financial impact
- Deterministic Resolver (LAYER 3): Actionable output
"""

from typing import Any

from app.tools.cost_calculator import calculate_disruption_cost
from app.tools.deterministic_resolver import resolve_crisis_deterministically
from app.tools.entity_extractor import extract_entities, find_affected_scenes
from app.tools.production import load_dataset
from app.tools.unified_risk_engine import (
    detect_crisis_type,
    evaluate_schedule_impact,
    find_compatible_swaps,
)


def evaluate_impact(scene_id: str, crisis_query: str) -> dict[str, Any]:
    """
    Autonomous impact assessment - works for ANY crisis type.
    
    Now uses LAYER 1 (Entity Extraction) to dynamically map unstructured input
    to database entities, then evaluates ALL affected scenes.
    """
    
    dataset = load_dataset("data")
    
    # LAYER 1: Dynamic Entity Extraction
    # Maps unstructured crisis query to actual database IDs
    extraction = extract_entities(crisis_query, dataset)
    
    # LAYER BASE: Crisis Type Detection
    crisis_info = detect_crisis_type(crisis_query)
    
    # Find all scenes affected by extracted entities
    affected_scenes = find_affected_scenes(extraction["extracted_entities"], dataset)
    
    # Evaluate impact on primary scene
    impact = evaluate_schedule_impact(
        scene_id,
        crisis_info["affected_resource"],
        crisis_info["type"],
        dataset
    )
    
    if "error" in impact:
        return impact
    
    # LAYER 2: Calculate Financial Impact
    duration_hours = extraction["crisis_classification"]["estimated_duration_hours"]
    if duration_hours is None:
        duration_hours = 24  # Default to 24 hours if not specified
    cost_analysis = calculate_disruption_cost(affected_scenes, duration_hours, dataset)
    
    # Determine risk level
    risk_level = "HIGH" if impact.get("is_blocked") else "LOW"
    
    return {
        "status": "success",
        "scene_id": scene_id,
        "crisis_type": crisis_info["type"],
        "affected_resource": crisis_info["affected_resource"],
        "risk_level": risk_level,
        "is_blocked": impact.get("is_blocked"),
        "blocking_reason": impact.get("blocking_reason"),
        "extracted_entities": extraction["extracted_entities"],
        "affected_scenes_count": len(affected_scenes),
        "financial_impact": cost_analysis["disruption_impact"],
        "severity": crisis_info["severity"]
    }


def generate_recovery_options(scene_id: str, crisis_query: str) -> dict[str, Any]:
    """
    Autonomous recovery planning - works for ANY crisis type.
    
    Now uses LAYER 3 (Deterministic Resolver) to output exact actions
    with cost analysis, not just recommendations.
    """
    
    dataset = load_dataset("data")
    
    # Get crisis classification
    extraction = extract_entities(crisis_query, dataset)
    crisis_info = detect_crisis_type(crisis_query)
    
    # Handle None extraction (same as in evaluate_impact)
    if extraction is None:
        extraction = {"crisis_classification": {"estimated_duration_hours": None}}
    
    duration_hours = extraction.get("crisis_classification", {}).get("estimated_duration_hours")
    if duration_hours is None:
        duration_hours = 24
    
    # LAYER 3: Deterministic Resolver
    # Outputs exact scene swaps with financial justification
    resolution = resolve_crisis_deterministically(
        scene_id,
        crisis_info["affected_resource"],
        crisis_info["type"],
        duration_hours,
        dataset
    )
    
    # Also get traditional swap options for comparison
    swap_candidates = find_compatible_swaps(
        scene_id,
        crisis_info["affected_resource"],
        crisis_info["type"],
        dataset
    )
    
    best_option = None
    if swap_candidates and len(swap_candidates) > 0:
        best_option = swap_candidates[0]
    
    return {
        "status": "success",
        "scene_id": scene_id,
        "crisis_type": crisis_info["type"],
        "deterministic_resolution": resolution,
        "alternative_options": [
            {
                "action": f"Swap {scene_id} with {opt['scene_id']} ({opt['title']})",
                "target_scene_id": opt["scene_id"],
                "target_title": opt["title"],
                "compatibility_score": opt["compatibility_score"],
                "reasoning": opt["reasoning"]
            }
            for opt in swap_candidates
        ],
        "option_count": len(swap_candidates),
        "best_option": best_option
    }
