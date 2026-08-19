"""
UNIFIED RISK ENGINE - Handles ANY operational failure category

Instead of separate tools for:
- Weather impact
- Cast availability
- Equipment failure
- Permit issues
- Location access

This single engine checks resource conflicts across ANY domain.
Works with both old (data/) and new (projects/) formats.
"""

from typing import Any

from app.tools.format_compat import detect_format, get_scene_dependencies, _get_cast_ids, _get_equipment_ids
from app.tools.production import get_scene_by_id


def detect_crisis_type(user_query: str) -> dict[str, Any]:
    """
    LLM-less heuristic to classify the crisis type.
    In production, Gemini would do this classification.
    
    Returns: {
        "type": "WEATHER" | "CAST" | "EQUIPMENT" | "PERMIT" | "LOCATION",
        "affected_resource": "Puri Beach" | "Arjun Kapoor" | "Drone Kit" | etc,
        "severity": "CRITICAL" | "HIGH" | "MEDIUM"
    }
    """
    
    query_lower = user_query.lower()
    
    # Weather detection
    if any(word in query_lower for word in ["weather", "rain", "monsoon", "storm", "wind", "flood", "heat", "cold"]):
        return {
            "type": "WEATHER",
            "affected_resource": "Outdoor Conditions",
            "severity": "CRITICAL" if "monsoon" in query_lower or "flood" in query_lower else "HIGH"
        }
    
    # Cast/Crew detection
    if any(word in query_lower for word in ["actor", "sick", "injured", "food poison", "accident", "illness", "arjun", "maya", "crew"]):
        return {
            "type": "CAST",
            "affected_resource": extract_actor_name(query_lower),
            "severity": "CRITICAL"
        }
    
    # Equipment detection
    if any(word in query_lower for word in ["equipment", "camera", "lens", "damaged", "broken", "failure", "drone", "rig"]):
        return {
            "type": "EQUIPMENT",
            "affected_resource": extract_equipment_type(query_lower),
            "severity": "HIGH"
        }
    
    # Permit/Legal detection
    if any(word in query_lower for word in ["permit", "revoked", "curfew", "section 144", "restricted", "legal"]):
        return {
            "type": "PERMIT",
            "affected_resource": "Municipal Authorization",
            "severity": "CRITICAL"
        }
    
    # Location detection
    if any(word in query_lower for word in ["location", "flooded", "inaccessible", "road closed", "access denied"]):
        return {
            "type": "LOCATION",
            "affected_resource": "Primary Filming Location",
            "severity": "HIGH"
        }
    
    # Default
    return {
        "type": "UNKNOWN",
        "affected_resource": "Production Schedule",
        "severity": "MEDIUM"
    }


def extract_actor_name(query: str) -> str:
    """Extract actor name from crisis query."""
    if "arjun" in query:
        return "Arjun Kapoor"
    if "maya" in query:
        return "Maya Sen"
    if "irrfan" in query:
        return "Irrfan Khan"
    return "Lead Actor"


def extract_equipment_type(query: str) -> str:
    """Extract equipment type from crisis query."""
    if "anamorphic" in query or "lens" in query:
        return "ANAMORPHIC_LENSES"
    if "drone" in query:
        return "DJI Inspire 3 Drone Kit"
    if "camera" in query:
        return "ARRI Alexa Mini Camera Package"
    if "generator" in query:
        return "Generator/Power"
    return "Equipment Package"


def evaluate_schedule_impact(scene_id: str, affected_resource: str, crisis_type: str, dataset: dict[str, Any]) -> dict[str, Any]:
    """
    GENERALIZED IMPACT EVALUATOR
    
    Instead of checking weather_dependency == HIGH,
    this checks if the affected_resource blocks the scene.
    
    affected_resource can be:
    - An actor name: "Arjun Kapoor"
    - A location: "Puri Beach"
    - Equipment: "ANAMORPHIC_LENSES"
    - A permit: "Puri-Coastal-Zone-A"
    """
    
    target_scene = get_scene_by_id(scene_id, dataset)
    
    if not target_scene:
        return {
            "status": "error",
            "message": f"Scene {scene_id} not found"
        }
    
    # Get dependencies for this scene
    is_new_fmt = (detect_format(dataset) == 'new')
    
    # Handle both old and new formats
    if is_new_fmt:
        # New format: dependencies is a string or null
        # For new format, we need to check scene's cast_required, equipment_required
        cast_blocking = target_scene.get("cast_required", [])
        location_blocking = [target_scene.get("location_id")] if target_scene.get("location_id") else []
        equipment_blocking = target_scene.get("equipment_required", [])
        permit_blocking = []  # Not in new format
    else:
        # Old format: dependencies is a dict
        dependencies = target_scene.get("dependencies", {})
        if isinstance(dependencies, str):
            # Fallback if it's a string
            cast_blocking = []
            location_blocking = []
            equipment_blocking = []
            permit_blocking = []
        else:
            cast_blocking = dependencies.get("cast_blocking", [])
            location_blocking = dependencies.get("location_blocking", [])
            equipment_blocking = dependencies.get("equipment_blocking", [])
            permit_blocking = dependencies.get("permit_blocking", [])
    
    # Check if affected_resource blocks this scene
    is_blocked = False
    blocking_reason = ""
    
    if affected_resource in cast_blocking:
        is_blocked = True
        blocking_reason = f"Scene requires {affected_resource} who is unavailable"
    elif affected_resource in location_blocking:
        is_blocked = True
        blocking_reason = f"Scene location {affected_resource} is blocked"
    elif affected_resource in equipment_blocking:
        is_blocked = True
        blocking_reason = f"Scene requires {affected_resource} which is unavailable"
    elif affected_resource in permit_blocking:
        is_blocked = True
        blocking_reason = f"Scene requires permit {affected_resource} which is revoked"
    elif crisis_type == "WEATHER" and target_scene.get("interior_exterior") == "EXTERIOR":
        is_blocked = True
        blocking_reason = "Scene is exterior and weather-dependent"
    
    return {
        "status": "success",
        "scene_id": scene_id,
        "title": target_scene.get("title"),
        "is_blocked": is_blocked,
        "blocking_reason": blocking_reason if is_blocked else "No conflict",
        "crisis_type": crisis_type,
        "affected_resource": affected_resource,
        "scene_duration": target_scene.get("duration_hours"),
        "location": target_scene.get("location_name"),
        "cast": target_scene.get("cast_names", []),
        "equipment": target_scene.get("equipment_names", [])
    }


def find_compatible_swaps(scene_id: str, affected_resource: str, crisis_type: str, dataset: dict[str, Any]) -> list[dict[str, Any]]:
    """
    UNIVERSAL SWAP ENGINE
    
    Finds scenes that:
    1. Do NOT require the blocked resource
    2. Can be swapped without cascading conflicts
    3. Minimize schedule disruption
    """
    
    scenes = dataset.get("scenes", [])
    
    target_scene = get_scene_by_id(scene_id, dataset)
    if not target_scene:
        return []
    
    target_duration = target_scene.get("duration_hours", 4)
    
    candidates = []
    
    for candidate in scenes:
        if candidate["scene_id"] == scene_id:
            continue
        
        # Check if candidate requires the blocked resource
        is_new_fmt = (detect_format(dataset) == 'new')
        
        if is_new_fmt:
            # New format: dependencies is a string
            cast_blocking = candidate.get("cast_required", [])
            location_blocking = [candidate.get("location_id")] if candidate.get("location_id") else []
            equipment_blocking = candidate.get("equipment_required", [])
            permit_blocking = []
        else:
            # Old format: dependencies is a dict
            dependencies = candidate.get("dependencies", {})
            if isinstance(dependencies, str):
                cast_blocking = []
                location_blocking = []
                equipment_blocking = []
                permit_blocking = []
            else:
                cast_blocking = dependencies.get("cast_blocking", [])
                location_blocking = dependencies.get("location_blocking", [])
                equipment_blocking = dependencies.get("equipment_blocking", [])
                permit_blocking = dependencies.get("permit_blocking", [])
        
        requires_blocked_resource = (
            affected_resource in cast_blocking or
            affected_resource in location_blocking or
            affected_resource in equipment_blocking or
            affected_resource in permit_blocking
        )
        
        if requires_blocked_resource:
            continue  # Skip this candidate
        
        # Calculate compatibility score
        score = 0
        
        # Bonus: Similar duration (fits same time slot)
        if abs(candidate.get("duration_hours", 4) - target_duration) <= 1:
            score += 10
        
        # Bonus: Interior scenes are safer for ANY crisis
        if candidate.get("interior_exterior") == "INTERIOR":
            score += 20
        
        # Bonus: Shares cast with target (already on-set)
        shared_cast = set(_get_cast_ids(target_scene, is_new_fmt)) & set(_get_cast_ids(candidate, is_new_fmt))
        if shared_cast:
            score += 15
        
        # Penalty: Requires additional resources
        if candidate.get("special_requirements"):
            score -= 5
        
        candidates.append({
            "scene_id": candidate["scene_id"],
            "title": candidate.get("title"),
            "location": candidate.get("location_name"),
            "interior_exterior": candidate.get("interior_exterior"),
            "duration_hours": candidate.get("duration_hours"),
            "cast": candidate.get("cast_names", []),
            "compatibility_score": score,
            "reasoning": f"Interior scene with zero conflict for {crisis_type} disruption"
        })
    
    # Sort by score (highest first = best match)
    candidates.sort(key=lambda x: x["compatibility_score"], reverse=True)
    return candidates[:3]  # Return top 3 options
