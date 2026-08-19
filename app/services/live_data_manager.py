"""
LIVE DATA MANAGER - Handle JSON file uploads and change detection

Allows users to upload updated production.json with changed actor/equipment status.
Compares new JSON against current state and flags differences for approval.

Use Cases:
1. Actor becomes sick → user uploads updated JSON with actor marked unavailable
2. Equipment fails → user updates JSON to mark equipment as unavailable
3. Location becomes inaccessible → user updates JSON with location marked blocked
4. Weather alert → user updates JSON with weather_alerts section
"""

from typing import Any
import json
from datetime import datetime

from app.tools.format_compat import detect_format, get_scene_title


class LiveDataManager:
    """Manages production data versioning and change tracking."""
    
    def __init__(self):
        self.current_state = {}
        self.previous_state = {}
        self.change_history = []
    
    def load_current_state(self, dataset: dict[str, Any]) -> None:
        """Store reference to current production state."""
        self.current_state = dataset.get("production", {}).copy()
    
    def upload_new_json(self, new_json: dict[str, Any] | str) -> dict[str, Any]:
        """
        User uploads a new production.json file.
        
        Args:
            new_json: dict or JSON string containing updated production data
        
        Returns:
            {
                "status": "json_received",
                "changes_detected": [
                    {
                        "field": "unavailable_cast",
                        "old_value": [],
                        "new_value": ["Arjun Kapoor"],
                        "change_type": "ARRAY_ADD",
                        "affected_scenes": ["sc_42", "sc_18"],
                        "impact_description": "2 scenes now blocking"
                    }
                ],
                "change_summary": "1 actor marked unavailable, impacts 2 scenes",
                "requires_approval": True,
                "upload_token": "upload_xyz",
                "new_production_state": {...}
            }
        """
        
        # Parse JSON if string
        if isinstance(new_json, str):
            try:
                new_json = json.loads(new_json)
            except json.JSONDecodeError as e:
                return {
                    "status": "error",
                    "message": f"Invalid JSON: {str(e)}",
                    "error_type": "JSON_PARSE_ERROR"
                }
        
        # Extract production section
        new_production = new_json.get("production", {})
        
        if not new_production:
            return {
                "status": "error",
                "message": "JSON does not contain 'production' section",
                "error_type": "MISSING_PRODUCTION_SECTION"
            }
        
        # Store for later approval
        self.previous_state = self.current_state.copy()
        
        # Detect changes
        changes = self._detect_changes(self.current_state, new_production)
        
        if not changes:
            return {
                "status": "no_changes",
                "message": "New JSON matches current state. No updates needed.",
                "changes_detected": []
            }
        
        # Generate change summary
        change_summary = self._generate_change_summary(changes)
        
        # Create upload token
        import uuid
        upload_token = f"upload_{uuid.uuid4().hex[:12]}"
        
        return {
            "status": "changes_detected",
            "changes_detected": changes,
            "change_summary": change_summary,
            "requires_approval": len(changes) > 0,
            "upload_token": upload_token,
            "new_production_state": new_production,
            "upload_timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _detect_changes(
        self,
        old_state: dict[str, Any],
        new_state: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Detect all differences between old and new production state.
        Focus on actor/equipment/location availability changes.
        """
        
        changes = []
        
        # Fields to track for changes
        tracked_fields = [
            "unavailable_cast",
            "unavailable_equipment",
            "inaccessible_locations",
            "weather_alerts",
            "current_day",
            "budget",
            "notes"
        ]
        
        for field in tracked_fields:
            old_value = old_state.get(field)
            new_value = new_state.get(field)
            
            # Skip if no change
            if old_value == new_value:
                continue
            
            # Determine change type
            if isinstance(old_value, list) and isinstance(new_value, list):
                added = [x for x in new_value if x not in (old_value or [])]
                removed = [x for x in (old_value or []) if x not in new_value]
                
                if added:
                    changes.append({
                        "field": field,
                        "old_value": old_value or [],
                        "new_value": new_value or [],
                        "change_type": "ARRAY_ADD",
                        "added_items": added,
                        "removed_items": [],
                        "description": f"Added {added} to {field}"
                    })
                
                if removed:
                    changes.append({
                        "field": field,
                        "old_value": old_value or [],
                        "new_value": new_value or [],
                        "change_type": "ARRAY_REMOVE",
                        "added_items": [],
                        "removed_items": removed,
                        "description": f"Removed {removed} from {field}"
                    })
            
            elif isinstance(old_value, dict) and isinstance(new_value, dict):
                # For nested objects like weather_alerts
                added_keys = set(new_value.keys()) - set((old_value or {}).keys())
                removed_keys = set((old_value or {}).keys()) - set(new_value.keys())
                
                if added_keys or removed_keys:
                    changes.append({
                        "field": field,
                        "old_value": old_value or {},
                        "new_value": new_value or {},
                        "change_type": "DICT_UPDATE",
                        "added_keys": list(added_keys),
                        "removed_keys": list(removed_keys),
                        "description": f"Updated {field}: +{added_keys}, -{removed_keys}"
                    })
            
            else:
                # Scalar value changed
                changes.append({
                    "field": field,
                    "old_value": old_value,
                    "new_value": new_value,
                    "change_type": "SCALAR_UPDATE",
                    "description": f"{field}: {old_value} → {new_value}"
                })
        
        return changes
    
    def _generate_change_summary(self, changes: list[dict[str, Any]]) -> str:
        """Generate human-readable change summary."""
        
        summaries = []
        
        for change in changes:
            field = change["field"]
            change_type = change["change_type"]
            
            if change_type == "ARRAY_ADD":
                items = change["added_items"]
                summaries.append(f"{len(items)} item(s) added to {field}: {', '.join(items)}")
            
            elif change_type == "ARRAY_REMOVE":
                items = change["removed_items"]
                summaries.append(f"{len(items)} item(s) removed from {field}: {', '.join(items)}")
            
            elif change_type == "DICT_UPDATE":
                added = change["added_keys"]
                removed = change["removed_keys"]
                if added:
                    summaries.append(f"Added {len(added)} alert(s) in {field}")
                if removed:
                    summaries.append(f"Removed {len(removed)} alert(s) from {field}")
            
            elif change_type == "SCALAR_UPDATE":
                old = change["old_value"]
                new = change["new_value"]
                summaries.append(f"{field} changed: {old} → {new}")
        
        return "; ".join(summaries) if summaries else "No significant changes"
    
    def get_affected_scenes(
        self,
        changes: list[dict[str, Any]],
        dataset: dict[str, Any]
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Determine which scenes are affected by the detected changes.
        
        Returns mapping of change field → list of affected scenes
        """
        
        affected_by_change = {}
        scenes = dataset.get("scenes", [])
        
        for change in changes:
            field = change["field"]
            affected_scenes = []
            
            if field == "unavailable_cast":
                # Find scenes with unavailable actors
                for actor in change.get("added_items", []):
                    for scene in scenes:
                        if actor in scene.get("cast_names", []):
                            affected_scenes.append({
                                "scene_id": scene["scene_id"],
                                "title": get_scene_title(scene, detect_format(self.current_state) == 'new'),
                                "reason": f"Requires {actor} (now unavailable)"
                            })
            
            elif field == "unavailable_equipment":
                # Find scenes needing unavailable equipment
                for equipment in change.get("added_items", []):
                    for scene in scenes:
                        if equipment in scene.get("equipment_names", []):
                            affected_scenes.append({
                                "scene_id": scene["scene_id"],
                                "title": get_scene_title(scene, detect_format(self.current_state) == 'new'),
                                "reason": f"Requires {equipment} (now unavailable)"
                            })
            
            elif field == "inaccessible_locations":
                # Find scenes using inaccessible locations
                for location in change.get("added_items", []):
                    for scene in scenes:
                        if scene.get("location_name") == location:
                            affected_scenes.append({
                                "scene_id": scene["scene_id"],
                                "title": get_scene_title(scene, detect_format(self.current_state) == 'new'),
                                "reason": f"Scheduled at {location} (now inaccessible)"
                            })
            
            elif field == "weather_alerts":
                # Find scenes at alerted locations
                for location in change.get("added_keys", []):
                    for scene in scenes:
                        if scene.get("location_name") == location and scene.get("interior_exterior") == "EXTERIOR":
                            affected_scenes.append({
                                "scene_id": scene["scene_id"],
                                "title": get_scene_title(scene, detect_format(self.current_state) == 'new'),
                                "reason": f"Exterior scene at {location} with weather alert"
                            })
            
            # Deduplicate
            affected_by_change[field] = list({s["scene_id"]: s for s in affected_scenes}.values())
        
        return affected_by_change
    
    def validate_json_schema(self, json_data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate that uploaded JSON has correct structure.
        
        Required fields:
        - production (object)
        
        Optional fields:
        - unavailable_cast (array)
        - unavailable_equipment (array)
        - inaccessible_locations (array)
        - weather_alerts (object)
        """
        
        errors = []
        
        if "production" not in json_data:
            errors.append("Missing 'production' object")
        else:
            production = json_data["production"]
            if not isinstance(production, dict):
                errors.append("'production' must be an object")
        
        # Validate optional arrays
        for field in ["unavailable_cast", "unavailable_equipment", "inaccessible_locations"]:
            if field in json_data:
                value = json_data[field]
                if not isinstance(value, list):
                    errors.append(f"'{field}' must be an array")
        
        # Validate optional object
        if "weather_alerts" in json_data:
            value = json_data["weather_alerts"]
            if not isinstance(value, dict):
                errors.append("'weather_alerts' must be an object")
        
        if errors:
            return {
                "status": "validation_error",
                "valid": False,
                "errors": errors
            }
        
        return {
            "status": "valid",
            "valid": True,
            "errors": []
        }
    
    def apply_changes(
        self,
        new_production_state: dict[str, Any],
        reason: str | None = None
    ) -> dict[str, Any]:
        """
        Apply the detected changes to the live production state.
        
        Should only be called AFTER user approval.
        """
        
        # Log the change
        change_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "old_state": self.previous_state.copy(),
            "new_state": new_production_state.copy(),
            "reason": reason or "User-approved production update",
            "changes": self._detect_changes(self.previous_state, new_production_state)
        }
        
        self.change_history.append(change_record)
        
        # Update current state
        self.current_state = new_production_state.copy()
        
        return {
            "status": "applied",
            "message": "Production state updated successfully",
            "new_state": self.current_state,
            "change_record_id": f"record_{len(self.change_history)}"
        }
    
    def get_change_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent production state changes."""
        return self.change_history[-limit:]
    
    def rollback_to_previous(self) -> dict[str, Any]:
        """Rollback to previous state (undo last change)."""
        
        if not self.change_history:
            return {
                "status": "error",
                "message": "No change history to rollback"
            }
        
        last_change = self.change_history[-1]
        self.current_state = last_change["old_state"].copy()
        
        return {
            "status": "rollback_complete",
            "message": "Rolled back to previous state",
            "previous_state": self.current_state
        }


# Global instance
_live_data_manager = LiveDataManager()


def get_live_data_manager() -> LiveDataManager:
    """Get singleton instance of live data manager."""
    return _live_data_manager
