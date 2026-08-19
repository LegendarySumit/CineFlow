"""
CONSTRAINTS - Scene impact evaluation for production dependencies.

Evaluates how a scene's resources (cast, equipment, location) are affected
by disruptions. Works with both old and new dataset formats.
"""

from typing import Any

from app.tools.format_compat import detect_format, get_scene_cast_ids, get_scene_equipment_ids
from app.tools.production import get_scene_by_id


def evaluate_scene_impact(scene_id: str, dataset: dict[str, Any]) -> dict[str, Any]:
    """
    Evaluate which resources (cast, equipment, location, permits) a scene depends on.
    
    Returns the resources affected, so other scenes can be checked for compatibility.
    """
    
    scene = get_scene_by_id(scene_id, dataset)
    
    if not scene:
        return {
            "error": f"Scene {scene_id} not found",
            "disrupted_scene_id": scene_id,
            "title": "Unknown",
            "location": "Unknown",
            "actors_affected": [],
            "equipment_affected": [],
            "is_exterior": False,
            "weather_dependency": "NONE"
        }
    
    # Get actor names
    is_new_fmt = (detect_format(dataset) == 'new')
    actors = dataset.get("actors", []) or dataset.get("cast", [])
    actor_ids = get_scene_cast_ids(scene, is_new_fmt)
    actor_names = [
        next((a.get("name") for a in actors if a.get("actor_id") == aid), "Unknown")
        for aid in actor_ids
    ]
    
    # Get equipment names
    equipment = dataset.get("equipment", [])
    equipment_ids = get_scene_equipment_ids(scene, is_new_fmt)
    equipment_names = [
        next((e.get("name") for e in equipment if e.get("equipment_id") == eid), "Unknown")
        for eid in equipment_ids
    ]
    
    # Get location
    locations = dataset.get("locations", [])
    location_id = scene.get("location_id")
    location_name = next(
        (l["name"] for l in locations if l["location_id"] == location_id),
        "Unknown"
    )
    
    return {
        "disrupted_scene_id": scene_id,
        "title": scene.get("title", "Unknown"),
        "location": location_name,
        "actors_affected": actor_names,
        "equipment_affected": equipment_names,
        "is_exterior": scene.get("interior_exterior") == "EXTERIOR",
        "weather_dependency": scene.get("weather_dependency", "NONE")
    }


def check_actor_availability(actor_ids: list[str], dataset: dict[str, Any]) -> dict[str, Any]:
    """
    Check if specified actors are available (not already scheduled).
    
    In production, would check against real actor availability systems.
    """
    
    return {
        "status": "success",
        "available": True,
        "actor_ids": actor_ids
    }
