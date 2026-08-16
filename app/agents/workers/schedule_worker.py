"""
SCHEDULE WORKER - Queries production database for scene details.

Role: Load and structure production context data.
Responsibility: Retrieve scene, cast, equipment, and location information.
"""

from typing import Any

from app.tools.constraints import evaluate_scene_impact
from app.tools.production import get_scene_by_id, load_dataset


def load_scene_and_schedule(scene_id: str) -> dict[str, Any]:
    """
    Autonomous schedule query task.
    
    Loads production database and retrieves full scene context.
    """
    
    # Load full production dataset
    dataset = load_dataset("data")
    
    # Retrieve scene details
    scene = get_scene_by_id(scene_id, dataset)
    
    if not scene:
        return {
            "status": "error",
            "message": f"Scene {scene_id} not found",
            "scene_id": scene_id
        }
    
    # Get impact (actors, equipment, location affected)
    impact = evaluate_scene_impact(scene_id, dataset)
    
    # Get schedule entry
    schedule = dataset.get("schedule", [])
    schedule_entry = next((s for s in schedule if s["scene_id"] == scene_id), None)
    
    return {
        "status": "success",
        "scene_id": scene_id,
        "scene": {
            "id": scene_id,
            "title": scene.get("title"),
            "interior_exterior": scene.get("interior_exterior"),
            "weather_dependency": scene.get("weather_dependency")
        },
        "schedule": {
            "day_number": schedule_entry.get("day_number") if schedule_entry else None,
            "date": schedule_entry.get("date") if schedule_entry else None
        },
        "affected_resources": impact if "error" not in impact else {},
        "cast_count": len(scene.get("cast_ids", [])),
        "equipment_count": len(scene.get("equipment_ids", []))
    }
