"""
READINESS ANALYZER - Proactive Dashboard Engine

Automatically analyzes ALL scenes for:
- Actor availability conflicts
- Equipment availability issues
- Location accessibility
- Weather impacts
- Budget implications
- Schedule interdependencies

Returns dashboard-ready risk scores and action items.
"""

from typing import Any
from datetime import datetime
import json

from app.tools.format_compat import detect_format
from app.tools.production import load_dataset
from app.tools.unified_risk_engine import (
    detect_crisis_type,
    evaluate_schedule_impact,
    find_compatible_swaps,
)
from app.tools.cost_calculator import calculate_disruption_cost
from app.tools.entity_extractor import find_affected_scenes


def analyze_production_readiness(
    production_state: dict[str, Any] | None = None,
    focus_days: int = 3
) -> dict[str, Any]:
    """
    Comprehensive production readiness analysis.
    
    Args:
        production_state: Current production JSON with actor/equipment status
        focus_days: How many days ahead to analyze
    
    Returns:
        {
            "status": "success",
            "timestamp": "ISO datetime",
            "production_id": str,
            "current_day": int,
            "overall_risk_level": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
            "scenes": [
                {
                    "scene_id": str,
                    "title": str,
                    "scheduled_day": int,
                    "scheduled_date": str,
                    "risk_level": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
                    "risk_score": 0-100,
                    "conflicts": [
                        {
                            "type": "ACTOR_UNAVAILABLE" | "EQUIPMENT_ISSUE" | "LOCATION_ACCESS" | "WEATHER_RISK" | "BUDGET_IMPACT",
                            "severity": "CRITICAL" | "HIGH" | "MEDIUM",
                            "description": str,
                            "affected_resource": str,
                            "can_swap": bool,
                            "suggested_swap_targets": [{"scene_id": str, "title": str, "compatibility_score": int}]
                        }
                    ],
                    "status_icons": {
                        "cast": "🟢" | "🟡" | "🔴",
                        "equipment": "🟢" | "🟡" | "🔴",
                        "location": "🟢" | "🟡" | "🔴",
                        "weather": "🟢" | "🟡" | "🔴",
                        "budget": "🟢" | "🟡" | "🔴"
                    },
                    "action_items": [
                        {
                            "priority": "CRITICAL" | "HIGH" | "MEDIUM",
                            "action": str,
                            "owner": "Producer" | "Assistant" | "Crew Lead",
                            "due_before": str  # ISO datetime
                        }
                    ]
                }
            ],
            "summary": {
                "total_scenes": int,
                "scenes_at_risk": int,
                "critical_conflicts": int,
                "budget_impact": {"daily_burn": float, "total_3day_impact": float},
                "recommended_actions": [
                    {
                        "priority": "CRITICAL",
                        "action": str,
                        "impact": str
                    }
                ]
            }
        }
    """
    
    dataset = load_dataset("data")
    
    if production_state is None:
        production_state = dataset.get("production", {})
    
    current_day = production_state.get("current_day", 1)
    production_id = production_state.get("production_id", "UNKNOWN")
    
    # Analyze all scenes
    scenes = dataset.get("scenes", [])
    scene_analyses = []
    all_conflicts = []
    total_financial_impact = 0
    
    for scene in scenes:
        scene_id = scene.get("scene_id")
        scene_analysis = _analyze_single_scene(
            scene_id,
            scene,
            current_day,
            focus_days,
            production_state,
            dataset
        )
        
        scene_analyses.append(scene_analysis)
        all_conflicts.extend(scene_analysis.get("conflicts", []))
        
        # Track financial impact
        for conflict in scene_analysis.get("conflicts", []):
            if conflict.get("type") == "BUDGET_IMPACT":
                # Extract cost from description if available
                total_financial_impact += 50000  # Default impact per major conflict
    
    # Calculate overall risk
    scenes_at_risk = sum(1 for s in scene_analyses if s.get("risk_level") != "LOW")
    critical_conflicts = sum(len(s.get("conflicts", [])) for s in scene_analyses 
                           if any(c.get("severity") == "CRITICAL" for c in s.get("conflicts", [])))
    
    risk_levels = [s.get("risk_level") for s in scene_analyses]
    if "CRITICAL" in risk_levels:
        overall_risk = "CRITICAL"
    elif "HIGH" in risk_levels:
        overall_risk = "HIGH"
    elif "MEDIUM" in risk_levels:
        overall_risk = "MEDIUM"
    else:
        overall_risk = "LOW"
    
    # Generate recommended actions
    recommended_actions = _generate_recommended_actions(scene_analyses, production_state)
    
    return {
        "status": "success",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "production_id": production_id,
        "current_day": current_day,
        "focus_days": focus_days,
        "overall_risk_level": overall_risk,
        "scenes": scene_analyses,
        "summary": {
            "total_scenes": len(scenes),
            "scenes_at_risk": scenes_at_risk,
            "critical_conflicts": critical_conflicts,
            "budget_impact": {
                "daily_burn": production_state.get("daily_burn_rate", 305000),
                "total_3day_impact": total_financial_impact
            },
            "recommended_actions": recommended_actions
        }
    }


def _analyze_single_scene(
    scene_id: str,
    scene: dict[str, Any],
    current_day: int,
    focus_days: int,
    production_state: dict[str, Any],
    dataset: dict[str, Any]
) -> dict[str, Any]:
    """
    Analyze a single scene for conflicts.
    """
    
    scheduled_day = scene.get("scheduled_day", current_day)
    is_within_focus = (current_day <= scheduled_day <= current_day + focus_days)
    
    conflicts = []
    status_icons = {
        "cast": "🟢",
        "equipment": "🟢",
        "location": "🟢",
        "weather": "🟢",
        "budget": "🟢"
    }
    
    action_items = []
    
    # CHECK 1: ACTOR AVAILABILITY
    cast_conflicts = _check_cast_availability(scene, production_state, dataset)
    if cast_conflicts:
        conflicts.extend(cast_conflicts)
        status_icons["cast"] = "🔴" if any(c["severity"] == "CRITICAL" for c in cast_conflicts) else "🟡"
        
        # Add action item
        action_items.append({
            "priority": "CRITICAL",
            "action": f"Verify cast availability for {scene.get('title')}",
            "owner": "Producer",
            "due_before": _get_due_date(scheduled_day - 1)
        })
    
    # CHECK 2: EQUIPMENT AVAILABILITY
    equipment_conflicts = _check_equipment_availability(scene, production_state, dataset)
    if equipment_conflicts:
        conflicts.extend(equipment_conflicts)
        status_icons["equipment"] = "🔴" if any(c["severity"] == "CRITICAL" for c in equipment_conflicts) else "🟡"
        
        action_items.append({
            "priority": "CRITICAL",
            "action": f"Confirm equipment ready for {scene.get('title')}",
            "owner": "Crew Lead",
            "due_before": _get_due_date(scheduled_day - 1)
        })
    
    # CHECK 3: LOCATION ACCESS
    location_conflicts = _check_location_access(scene, production_state, dataset)
    if location_conflicts:
        conflicts.extend(location_conflicts)
        status_icons["location"] = "🔴" if any(c["severity"] == "CRITICAL" for c in location_conflicts) else "🟡"
        
        action_items.append({
            "priority": "HIGH",
            "action": f"Verify location access for {scene.get('title')}",
            "owner": "Location Manager",
            "due_before": _get_due_date(scheduled_day - 2)
        })
    
    # CHECK 4: WEATHER RISK (for exterior scenes)
    if scene.get("interior_exterior") == "EXTERIOR":
        weather_conflicts = _check_weather_risk(scene, scheduled_day, production_state, dataset)
        if weather_conflicts:
            conflicts.extend(weather_conflicts)
            status_icons["weather"] = "🟡"  # Weather is always caution, never blocking
    
    # CHECK 5: BUDGET IMPACT
    budget_conflicts = _check_budget_impact(scene, production_state, dataset)
    if budget_conflicts:
        conflicts.extend(budget_conflicts)
        status_icons["budget"] = "🟡"
    
    # Determine risk level based on conflicts
    risk_level = "LOW"
    if any(c["severity"] == "CRITICAL" for c in conflicts):
        risk_level = "CRITICAL"
    elif any(c["severity"] == "HIGH" for c in conflicts):
        risk_level = "HIGH"
    elif any(c["severity"] == "MEDIUM" for c in conflicts):
        risk_level = "MEDIUM"
    
    # Calculate risk score (0-100)
    risk_score = _calculate_risk_score(conflicts, is_within_focus)
    
    # For critical/high conflicts, find swap targets
    for conflict in conflicts:
        if conflict["severity"] in ["CRITICAL", "HIGH"] and conflict["type"] != "WEATHER_RISK":
            swap_targets = find_compatible_swaps(
                scene_id,
                conflict.get("affected_resource", ""),
                conflict.get("type", ""),
                dataset
            )
            conflict["suggested_swap_targets"] = [
                {
                    "scene_id": s.get("scene_id"),
                    "title": s.get("title"),
                    "compatibility_score": int(s.get("compatibility_score", 0) * 100)
                }
                for s in swap_targets[:3]  # Top 3 alternatives
            ]
            conflict["can_swap"] = len(swap_targets) > 0
    
    return {
        "scene_id": scene_id,
        "title": scene.get("title", "Unknown"),
        "scheduled_day": scheduled_day,
        "scheduled_date": scene.get("scheduled_date", "TBD"),
        "location": scene.get("location_name", "Unknown"),
        "duration_hours": scene.get("duration_hours", 4),
        "cast": scene.get("cast_names", []),
        "equipment": scene.get("equipment_names", []),
        "interior_exterior": scene.get("interior_exterior", "UNKNOWN"),
        "risk_level": risk_level,
        "risk_score": risk_score,
        "conflicts": conflicts,
        "status_icons": status_icons,
        "action_items": action_items,
        "is_within_focus": is_within_focus
    }


def _check_cast_availability(
    scene: dict[str, Any],
    production_state: dict[str, Any],
    dataset: dict[str, Any]
) -> list[dict[str, Any]]:
    """Check if all required cast is available."""
    
    conflicts = []
    cast_list = scene.get("cast_names", [])
    unavailable_cast = production_state.get("unavailable_cast", [])
    
    for actor in cast_list:
        if actor in unavailable_cast:
            conflicts.append({
                "type": "ACTOR_UNAVAILABLE",
                "severity": "CRITICAL",
                "description": f"Actor '{actor}' is marked unavailable",
                "affected_resource": actor,
                "can_swap": True
            })
    
    return conflicts


def _check_equipment_availability(
    scene: dict[str, Any],
    production_state: dict[str, Any],
    dataset: dict[str, Any]
) -> list[dict[str, Any]]:
    """Check if all required equipment is available."""
    
    conflicts = []
    equipment_list = scene.get("equipment_names", [])
    unavailable_equipment = production_state.get("unavailable_equipment", [])
    
    for equipment in equipment_list:
        if equipment in unavailable_equipment:
            conflicts.append({
                "type": "EQUIPMENT_ISSUE",
                "severity": "CRITICAL",
                "description": f"Equipment '{equipment}' is unavailable",
                "affected_resource": equipment,
                "can_swap": True
            })
    
    return conflicts


def _check_location_access(
    scene: dict[str, Any],
    production_state: dict[str, Any],
    dataset: dict[str, Any]
) -> list[dict[str, Any]]:
    """Check if location is accessible."""
    
    conflicts = []
    location = scene.get("location_name", "")
    inaccessible_locations = production_state.get("inaccessible_locations", [])
    
    if location in inaccessible_locations:
        conflicts.append({
            "type": "LOCATION_ACCESS",
            "severity": "CRITICAL",
            "description": f"Location '{location}' is inaccessible",
            "affected_resource": location,
            "can_swap": True
        })
    
    return conflicts


def _check_weather_risk(
    scene: dict[str, Any],
    scheduled_day: int,
    production_state: dict[str, Any],
    dataset: dict[str, Any]
) -> list[dict[str, Any]]:
    """Check weather risk for exterior scenes."""
    
    conflicts = []
    location = scene.get("location_name", "")
    weather_alerts = production_state.get("weather_alerts", {})
    
    if location in weather_alerts:
        alert = weather_alerts[location]
        conflicts.append({
            "type": "WEATHER_RISK",
            "severity": alert.get("severity", "MEDIUM"),
            "description": f"Weather alert for {location}: {alert.get('description', 'Unknown conditions')}",
            "affected_resource": location,
            "can_swap": False  # Weather issues often resolve; don't force swap
        })
    
    return conflicts


def _check_budget_impact(
    scene: dict[str, Any],
    production_state: dict[str, Any],
    dataset: dict[str, Any]
) -> list[dict[str, Any]]:
    """Check budget implications."""
    
    conflicts = []
    
    # Check if scene has exceptional costs
    budget_overrun = scene.get("estimated_cost", 0)
    daily_burn = production_state.get("daily_burn_rate", 305000)
    
    if budget_overrun > daily_burn * 1.5:  # Scene costs 150% of daily burn
        conflicts.append({
            "type": "BUDGET_IMPACT",
            "severity": "MEDIUM",
            "description": f"Scene has elevated costs: ₹{budget_overrun:,}",
            "affected_resource": "Budget",
            "can_swap": False
        })
    
    return conflicts


def _calculate_risk_score(conflicts: list[dict[str, Any]], is_within_focus: bool) -> int:
    """
    Calculate risk score 0-100 based on conflicts.
    Scores higher if conflicts are within focus window.
    """
    
    score = 0
    
    for conflict in conflicts:
        severity = conflict.get("severity", "MEDIUM")
        if severity == "CRITICAL":
            score += 40
        elif severity == "HIGH":
            score += 25
        elif severity == "MEDIUM":
            score += 10
    
    # Boost score if within focus window
    if is_within_focus:
        score = int(score * 1.3)
    
    return min(score, 100)  # Cap at 100


def _generate_recommended_actions(
    scene_analyses: list[dict[str, Any]],
    production_state: dict[str, Any]
) -> list[dict[str, Any]]:
    """Generate top-priority recommended actions from all scenes."""
    
    all_actions = []
    
    for scene in scene_analyses:
        # Collect highest priority actions
        critical_actions = [a for a in scene.get("action_items", []) if a["priority"] == "CRITICAL"]
        all_actions.extend(critical_actions)
    
    # Sort by priority and due date, return top 5
    all_actions.sort(key=lambda x: (x["priority"] != "CRITICAL", x.get("due_before", "")))
    
    return all_actions[:5]


def _get_due_date(days_from_now: int) -> str:
    """Get ISO datetime for N days from now."""
    from datetime import datetime, timedelta
    future_date = datetime.utcnow() + timedelta(days=days_from_now)
    return future_date.isoformat() + "Z"
