"""
CASCADE DETECTOR - Identifies secondary crises created by primary decisions.

Problem: Recommending SWAP sc_42 → sc_18 might create a NEW conflict
Example: sc_18 actor is already booked on that day for a different scene

Solution: Analyze decision impact → detect cascades → flag before execution

This enables multi-level crisis planning.
"""

from typing import Any

from app.tools.production import load_dataset


def detect_cascading_crises(
    decision: dict[str, Any],
    dataset: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Analyze a proposed decision and detect if it creates new crises.
    
    Returns:
    {
        "has_cascades": bool,
        "cascades": [
            {
                "type": "CAST_CONFLICT",
                "severity": "HIGH",
                "description": "...",
                "affected_scenes": ["sc_18", "sc_15"],
                "resolution": "..."
            }
        ],
        "safe_to_execute": bool,
        "safe_alternatives": [...]
    }
    """
    
    if dataset is None:
        dataset = load_dataset("data")
    
    cascades = []
    
    # Determine decision type and run appropriate checks
    decision_type = decision.get("decision_type", "UNKNOWN")
    
    if decision_type == "SWAP":
        cascades.extend(_detect_swap_cascades(decision, dataset))
    
    elif decision_type == "RESCHEDULE":
        cascades.extend(_detect_reschedule_cascades(decision, dataset))
    
    return {
        "has_cascades": len(cascades) > 0,
        "cascade_count": len(cascades),
        "cascades": cascades,
        "safe_to_execute": len([c for c in cascades if c.get("severity") == "HIGH"]) == 0,
        "warning": "Cascading crises detected. Review before execution." if cascades else "No secondary impacts detected."
    }


def _detect_swap_cascades(decision: dict[str, Any], dataset: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Detect crises created by swapping two scenes.
    
    Check:
    1. Cast conflicts (actor in both scenes on same day?)
    2. Equipment conflicts (same equipment needed in both scenes?)
    3. Location conflicts (same location can't be used twice in one day?)
    4. Crew conflicts (key crew unavailable?)
    """
    
    cascades = []
    
    source_id = decision.get("source_scene_id")
    target_id = decision.get("target_scene_id")
    
    if not source_id or not target_id:
        return cascades
    
    schedule = dataset.get("schedule", [])
    scenes = dataset.get("scenes", [])
    
    # Get scene data
    source_scene = next((s for s in scenes if s["scene_id"] == source_id), None)
    target_scene = next((s for s in scenes if s["scene_id"] == target_id), None)
    source_schedule = next((s for s in schedule if s["scene_id"] == source_id), None)
    target_schedule = next((s for s in schedule if s["scene_id"] == target_id), None)
    
    if not all([source_scene, target_scene, source_schedule, target_schedule]):
        return cascades
    
    # Type narrowing for linter
    assert source_scene is not None
    assert target_scene is not None
    assert source_schedule is not None
    assert target_schedule is not None
    
    source_actors = source_scene.get("cast_ids", [])
    source_equipment = source_scene.get("equipment_ids", [])
    source_new_date = target_schedule.get("date")
    
    # ════════════════════════════════════════════════════════════════
    # CASCADE 1: CAST CONFLICTS
    # ════════════════════════════════════════════════════════════════
    
    # Check if any source actor is filming target scene's original scene on new date
    conflicting_actors = []
    for actor_id in source_actors:
        # Find all scenes this actor appears in
        actor_scenes = [s for s in scenes if actor_id in s.get("cast_ids", [])]
        actor_scene_ids = [s["scene_id"] for s in actor_scenes]
        
        # Check if actor has OTHER scenes on the new date
        for other_scene_id in actor_scene_ids:
            if other_scene_id != source_id:  # Different scene
                other_schedule = next((s for s in schedule if s["scene_id"] == other_scene_id), None)
                if other_schedule and other_schedule.get("date") == source_new_date:
                    conflicting_actors.append({
                        "actor_id": actor_id,
                        "scene_conflict": other_scene_id,
                        "conflict_date": source_new_date
                    })
    
    if conflicting_actors:
        cascades.append({
            "type": "CAST_CONFLICT",
            "severity": "HIGH",
            "description": f"{len(conflicting_actors)} actor(s) double-booked after swap",
            "details": conflicting_actors,
            "affected_scenes": [source_id, target_id] + [c["scene_conflict"] for c in conflicting_actors],
            "resolution": "Cannot execute: Choose different target scene or reschedule conflicting scenes first"
        })
    
    # ════════════════════════════════════════════════════════════════
    # CASCADE 2: EQUIPMENT CONFLICTS
    # ════════════════════════════════════════════════════════════════
    
    conflicting_equipment = []
    for equipment_id in source_equipment:
        # Check if same equipment is needed by other scenes on new date
        equipment_scenes = [s for s in scenes if equipment_id in s.get("equipment_ids", [])]
        equipment_scene_ids = [s["scene_id"] for s in equipment_scenes]
        
        for other_scene_id in equipment_scene_ids:
            if other_scene_id != source_id:
                other_schedule = next((s for s in schedule if s["scene_id"] == other_scene_id), None)
                if other_schedule and other_schedule.get("date") == source_new_date:
                    conflicting_equipment.append({
                        "equipment_id": equipment_id,
                        "scene_conflict": other_scene_id,
                        "conflict_date": source_new_date
                    })
    
    if conflicting_equipment:
        affected_conflict_scenes = [c.get("scene_conflict") for c in conflicting_equipment if c.get("scene_conflict")]
        cascades.append({
            "type": "EQUIPMENT_CONFLICT",
            "severity": "MEDIUM",
            "description": f"{len(conflicting_equipment)} equipment(s) needed on same day",
            "details": conflicting_equipment,
            "affected_scenes": [source_id, target_id] + affected_conflict_scenes,
            "resolution": "May be solvable with equipment rental or parallel shoots"
        })
    
    # ════════════════════════════════════════════════════════════════
    # CASCADE 3: LOCATION CONFLICTS
    # ════════════════════════════════════════════════════════════════
    
    source_location = source_scene.get("location_id")
    
    if source_location:
        # Check if source location is needed on new date by other scenes
        location_scenes = [s for s in scenes if s.get("location_id") == source_location]
        location_scene_ids = [s["scene_id"] for s in location_scenes]
        
        location_conflicts = []
        for other_scene_id in location_scene_ids:
            if other_scene_id != source_id:
                other_schedule = next((s for s in schedule if s["scene_id"] == other_scene_id), None)
                if other_schedule and other_schedule.get("date") == source_new_date:
                    location_conflicts.append({
                        "location_id": source_location,
                        "scene_conflict": other_scene_id,
                        "conflict_date": source_new_date
                    })
        
        if location_conflicts:
            cascades.append({
                "type": "LOCATION_CONFLICT",
                "severity": "MEDIUM",
                "description": f"Location {source_location} needed on same day",
                "details": location_conflicts,
                "affected_scenes": [source_id, target_id] + [c["scene_conflict"] for c in location_conflicts],
                "resolution": "Schedule sequential shooting or find alternative location"
            })
    
    return cascades


def _detect_reschedule_cascades(decision: dict[str, Any], dataset: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Detect crises created by rescheduling a scene to a new date.
    
    Check:
    1. Cast availability on new date
    2. Location availability on new date
    3. Equipment availability on new date
    """
    
    cascades = []
    
    scene_id = decision.get("scene_id")
    new_date = decision.get("new_date")
    
    if not scene_id or not new_date:
        return cascades
    
    schedule = dataset.get("schedule", [])
    scenes = dataset.get("scenes", [])
    
    scene = next((s for s in scenes if s["scene_id"] == scene_id), None)
    
    if not scene:
        return cascades
    
    # Check if cast is available on new date
    cast_ids = scene.get("cast_ids", [])
    cast_conflicts = []
    
    for actor_id in cast_ids:
        actor_scenes = [s for s in scenes if actor_id in s.get("cast_ids", [])]
        for actor_scene in actor_scenes:
            actor_scene_id = actor_scene["scene_id"]
            if actor_scene_id != scene_id:
                actor_schedule = next((s for s in schedule if s["scene_id"] == actor_scene_id), None)
                if actor_schedule and actor_schedule.get("date") == new_date:
                    cast_conflicts.append({
                        "actor_id": actor_id,
                        "conflicting_scene": actor_scene_id,
                        "date": new_date
                    })
    
    if cast_conflicts:
        cascades.append({
            "type": "CAST_CONFLICT",
            "severity": "HIGH",
            "description": f"Cast member(s) unavailable on new date {new_date}",
            "details": cast_conflicts,
            "affected_scenes": [scene_id] + [c["conflicting_scene"] for c in cast_conflicts],
            "resolution": "Choose different reschedule date"
        })
    
    return cascades


def detect_secondary_cascades(
    primary_decision: dict[str, Any],
    primary_cascades: list[dict[str, Any]],
    dataset: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    MULTI-LEVEL CRISIS HANDLING:
    If primary decision creates cascade, check if safe alternatives create NEW cascades.
    
    Example:
    - sc_42 → sc_18 creates CAST_CONFLICT
    - sc_42 → sc_25 (safe alternative) might create LOCATION_CONFLICT
    - sc_42 → sc_14 (also safe alternative) has no cascades ✓
    
    Returns:
    {
        "safe_alternatives": [...],  # Alternatives with no cascades
        "risky_alternatives": [...],  # Alternatives with mild cascades
        "unsafe_alternatives": [...],  # Alternatives with severe cascades
        "has_truly_safe_option": bool,
        "recommendation": "Use sc_14 - completely safe"
    }
    """
    
    if dataset is None:
        dataset = load_dataset("data")
    
    if not primary_cascades:
        return {
            "safe_alternatives": [],
            "risky_alternatives": [],
            "unsafe_alternatives": [],
            "has_truly_safe_option": True,
            "recommendation": "Primary decision is safe - no cascades detected"
        }
    
    # Get primary decision alternatives
    source_id = primary_decision.get("source_scene_id")
    all_scenes = dataset.get("scenes", [])
    
    safe_alts = []
    risky_alts = []
    unsafe_alts = []
    
    # Test each potential alternative
    for scene in all_scenes:
        candidate_id = scene.get("scene_id")
        
        if candidate_id == source_id:
            continue
        
        # Create test decision for this alternative
        test_decision = {
            "decision_type": primary_decision.get("decision_type"),
            "source_scene_id": source_id,
            "target_scene_id": candidate_id
        }
        
        # Check for cascades with this alternative
        test_result = detect_cascading_crises(test_decision, dataset)
        
        alt_info = {
            "target": candidate_id,
            "title": scene.get("title", "Unknown"),
            "cascade_count": test_result.get("cascade_count", 0),
            "cascades": test_result.get("cascades", [])
        }
        
        # Categorize by severity
        if not test_result.get("has_cascades"):
            safe_alts.append(alt_info)
        else:
            # Count HIGH severity cascades
            high_count = len([c for c in test_result.get("cascades", []) if c.get("severity") == "HIGH"])
            
            if high_count == 0:
                # Only MEDIUM/LOW cascades = risky but manageable
                risky_alts.append(alt_info)
            else:
                # HIGH severity cascades = very risky
                unsafe_alts.append(alt_info)
    
    # Build recommendation
    if safe_alts:
        recommendation = f"Use {safe_alts[0]['target']} ({safe_alts[0]['title']}) - completely safe"
        has_safe = True
    elif risky_alts:
        recommendation = f"Consider {risky_alts[0]['target']} - has manageable conflicts"
        has_safe = False
    else:
        recommendation = "No safe alternatives found. Consider HOLD or RESCHEDULE instead of SWAP."
        has_safe = False
    
    return {
        "safe_alternatives": safe_alts[:3],
        "risky_alternatives": risky_alts[:3],
        "unsafe_alternatives": unsafe_alts[:3],
        "has_truly_safe_option": has_safe,
        "recommendation": recommendation,
        "total_safe": len(safe_alts),
        "total_risky": len(risky_alts),
        "total_unsafe": len(unsafe_alts)
    }


def get_safe_alternatives(
    primary_decision: dict[str, Any],
    cascades: list[dict[str, Any]],
    dataset: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    """
    Given cascading crises, suggest alternative decisions that avoid them.
    Intelligently filters based on scene properties and constraints.
    """
    
    if dataset is None:
        dataset = load_dataset("data")
    
    if not cascades:
        return []  # No cascades, primary decision is safe
    
    alternatives = []
    
    # If SWAP caused cascades, suggest alternative targets
    if primary_decision.get("decision_type") == "SWAP":
        source_id = primary_decision.get("source_scene_id")
        source_scene = next((s for s in dataset.get("scenes", []) if s["scene_id"] == source_id), None)
        
        if not source_scene:
            return alternatives
        
        # Get source scene properties
        source_type = source_scene.get("interior_exterior", "UNKNOWN")
        source_cast = set(source_scene.get("cast_ids", []))
        source_equipment = set(source_scene.get("equipment_ids", []))
        
        all_scenes = dataset.get("scenes", [])
        
        # Try each scene as alternative target
        # Prioritize scenes with similar characteristics
        candidates_by_compatibility = []
        
        for scene in all_scenes:
            candidate_id = scene.get("scene_id")
            
            if candidate_id == source_id:
                continue
            
            test_decision = {
                "decision_type": "SWAP",
                "source_scene_id": source_id,
                "target_scene_id": candidate_id
            }
            
            test_cascades = detect_cascading_crises(test_decision, dataset)
            
            # If no cascades, calculate compatibility score
            if not test_cascades.get("has_cascades"):
                compatibility = 0
                
                # Same interior/exterior = +1
                if scene.get("interior_exterior") == source_type:
                    compatibility += 1
                
                # Similar cast = +1
                candidate_cast = set(scene.get("cast_ids", []))
                cast_overlap = len(source_cast & candidate_cast)
                if cast_overlap == 0:
                    compatibility += 1
                
                # Similar equipment = +1
                candidate_equipment = set(scene.get("equipment_ids", []))
                equipment_overlap = len(source_equipment & candidate_equipment)
                if equipment_overlap == 0:
                    compatibility += 1
                
                candidates_by_compatibility.append({
                    "action": "SWAP",
                    "source": source_id,
                    "target": candidate_id,
                    "target_title": scene.get("title", "Unknown"),
                    "reason": "No cascading crises detected",
                    "safe": True,
                    "compatibility": compatibility
                })
        
        # Sort by compatibility score (higher = better match)
        candidates_by_compatibility.sort(key=lambda x: x["compatibility"], reverse=True)
        alternatives = candidates_by_compatibility[:3]  # Return top 3 alternatives
    
    return alternatives if alternatives else []