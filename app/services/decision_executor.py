"""
DECISION EXECUTOR - Converts recommendations into actual production changes.

Responsible for:
- Executing approved decisions (scene swaps, reschedules, etc.)
- Updating production schedule
- Tracking decision state
- Logging execution outcomes
"""

from datetime import datetime, timezone
from typing import Any

from app.tools.production import get_scene_by_id, load_dataset


def execute_swap_decision(
    session_id: str,
    source_scene_id: str,
    target_scene_id: str,
    approved_by: str,
    reason: str
) -> dict[str, Any]:
    """
    Execute a scene swap decision: move source_scene to target_scene's slot.
    
    Returns execution confirmation with affected resources.
    """
    
    dataset = load_dataset("data")
    schedule = dataset.get("schedule", [])
    
    # Find scene entries
    source_entry = next((s for s in schedule if s["scene_id"] == source_scene_id), None)
    target_entry = next((s for s in schedule if s["scene_id"] == target_scene_id), None)
    
    if not source_entry or not target_entry:
        return {
            "status": "error",
            "message": "Scene not found in schedule",
            "source_scene": source_scene_id,
            "target_scene": target_scene_id
        }
    
    # Get scene details for notifications
    source_scene = get_scene_by_id(source_scene_id, dataset)
    target_scene = get_scene_by_id(target_scene_id, dataset)
    
    # Swap day/date assignments
    original_source_day = source_entry.get("day_number")
    original_source_date = source_entry.get("date")
    original_target_day = target_entry.get("day_number")
    original_target_date = target_entry.get("date")
    
    # Execute swap (in production, this would update database)
    source_entry["day_number"] = original_target_day
    source_entry["date"] = original_target_date
    target_entry["day_number"] = original_source_day
    target_entry["date"] = original_source_date
    
    # Determine affected resources
    affected_cast = source_scene.get("cast_ids", []) if source_scene else []
    affected_equipment = source_scene.get("equipment_ids", []) if source_scene else []
    
    now = datetime.now(timezone.utc).isoformat()
    return {
        "status": "success",
        "execution_id": f"exec_{session_id}_{now}",
        "decision_type": "SWAP",
        "source_scene": {
            "id": source_scene_id,
            "title": source_scene.get("title") if source_scene else "Unknown",
            "original_date": original_source_date,
            "new_date": original_target_date
        },
        "target_scene": {
            "id": target_scene_id,
            "title": target_scene.get("title") if target_scene else "Unknown",
            "original_date": original_target_date,
            "new_date": original_source_date
        },
        "affected_resources": {
            "cast_count": len(affected_cast),
            "equipment_count": len(affected_equipment),
            "cast_ids": affected_cast,
            "equipment_ids": affected_equipment
        },
        "approval_info": {
            "approved_by": approved_by,
            "approval_time": now,
            "reason": reason
        },
        "schedule_updated": True,
        "execution_timestamp": now
    }


def execute_reschedule_decision(
    session_id: str,
    scene_id: str,
    new_day_number: int,
    new_date: str,
    approved_by: str,
    reason: str
) -> dict[str, Any]:
    """
    Execute a reschedule decision: move scene to new day/date.
    """
    
    dataset = load_dataset("data")
    schedule = dataset.get("schedule", [])
    
    scene_entry = next((s for s in schedule if s["scene_id"] == scene_id), None)
    scene = get_scene_by_id(scene_id, dataset)
    
    if not scene_entry:
        return {
            "status": "error",
            "message": f"Scene {scene_id} not found in schedule"
        }
    
    original_day = scene_entry.get("day_number")
    original_date = scene_entry.get("date")
    
    # Execute reschedule
    scene_entry["day_number"] = new_day_number
    scene_entry["date"] = new_date
    
    now = datetime.now(timezone.utc).isoformat()
    return {
        "status": "success",
        "execution_id": f"exec_{session_id}_{now}",
        "decision_type": "RESCHEDULE",
        "scene": {
            "id": scene_id,
            "title": scene.get("title") if scene else "Unknown",
            "original_date": original_date,
            "new_date": new_date,
            "original_day": original_day,
            "new_day": new_day_number
        },
        "affected_resources": {
            "cast_count": len(scene.get("cast_ids", [])) if scene else 0,
            "equipment_count": len(scene.get("equipment_ids", [])) if scene else 0
        },
        "approval_info": {
            "approved_by": approved_by,
            "approval_time": now,
            "reason": reason
        },
        "schedule_updated": True,
        "execution_timestamp": now
    }


def get_execution_status(execution_id: str) -> dict[str, Any]:
    """
    Retrieve status of a past execution.
    (In production, would query database)
    """
    
    return {
        "execution_id": execution_id,
        "status": "EXECUTED",
        "note": "In production, this would retrieve from database"
    }
