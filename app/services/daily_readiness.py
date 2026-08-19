"""
Daily Readiness Report - Shows production crew what to expect TODAY
before they start shooting. Combines project data + Parallel MCP data
+ Gemini synthesis for smart recommendations.

Answers: "Can we shoot today? Any issues? What should we prepare?"
"""

import json
import os
import warnings
from typing import Any
from datetime import datetime
from dotenv import load_dotenv

# Suppress FutureWarning from deprecated google.generativeai package
warnings.filterwarnings('ignore', category=FutureWarning, module='google.generativeai')
import google.generativeai as genai

from app.agents.workers.external_info_worker import gather_external_context
from app.tools.production import load_project

load_dotenv()
# Use gemini-2.5-flash for free tier - higher quota (10 RPM, 250 RPD)
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def generate_daily_readiness_report(project_id_or_dict: str | dict, shoot_date: str = None) -> dict[str, Any]:
    """
    Generate daily readiness report for production crew.
    
    Shows:
    - Today's scheduled scenes
    - Any issues (weather, permits, cast, equipment)
    - Recommendations (proceed, reschedule, contingency)
    - Scene-by-scene go/no-go decisions
    
    Args:
        project_id_or_dict: Project ID (e.g., "prod_monsoon_arc_01") or full project dict
        shoot_date: Date to check (default: today)
    
    Returns:
        {
            "date": "2026-09-01",
            "project_name": "Monsoon Arc",
            "overall_status": "PROCEED_WITH_CAUTION",
            "scenes": [
                {
                    "scene_id": "sc_001",
                    "title": "Monsoon Arrives at Arambol Beach",
                    "scheduled_time": "DAWN",
                    "status": "GO",
                    "risk_level": "HIGH",
                    "issues": ["Weather: Heavy monsoon rain expected", "Location: Beach permits valid"],
                    "recommendations": "Move indoor studio as backup. Beach shoot risky.",
                    "external_context": {...}
                }
            ],
            "summary": "2 scenes GO, 1 scene CONDITIONAL, 0 scenes NO-GO",
            "daily_briefing": "Formatted briefing for crew"
        }
    """
    
    # Load project - handle both string ID and dict
    if isinstance(project_id_or_dict, dict):
        project = project_id_or_dict
        project_id = project.get("metadata", {}).get("project_id", "UNKNOWN")
    else:
        project_id = project_id_or_dict
        project = load_project(project_id)
    
    if not project:
        return {
            "status": "error",
            "message": f"Project not found: {project_id_or_dict}"
        }
    
    # Use provided date or use first scheduled scene date
    if not shoot_date:
        # Get first scene's shoot date instead of today's date
        all_scenes = project.get("scenes", [])
        if all_scenes:
            first_scene_date = all_scenes[0].get("shooting_schedule", {}).get("shoot_date")
            shoot_date = first_scene_date if first_scene_date else datetime.now().strftime("%Y-%m-%d")
        else:
            shoot_date = datetime.now().strftime("%Y-%m-%d")
    
    # Find scenes scheduled for this date
    scenes = project.get("scenes", [])
    today_scenes = [s for s in scenes if s.get("shooting_schedule", {}).get("shoot_date") == shoot_date]
    
    if not today_scenes:
        return {
            "status": "success",
            "date": shoot_date,
            "project_name": project.get("metadata", {}).get("project_name"),
            "message": "No scenes scheduled for this date",
            "scenes": []
        }
    
    # Get external context for each scene
    scene_reports = []
    for scene in today_scenes:
        scene_id = scene.get("scene_id")
        location_id = scene.get("location_id")
        
        # Gather external context (weather, permits, alerts, etc.)
        print(f"\n  [Analyzing Scene {scene_id}...]")
        external_context = gather_external_context(
            scene_id,
            f"Check conditions for {scene.get('scene_title')}",
            project_data=project
        )
        
        # Display external context findings
        if external_context.get("status") == "success":
            ext_data = external_context.get("external_context", {})
            print(f"    [External Context Gathered]")
            for query_type, results in ext_data.items():
                if results.get("status") == "success" and results.get("results"):
                    print(f"      {query_type}: {len(results.get('results', []))} findings")
                    for i, result in enumerate(results.get("results", [])[:2]):
                        print(f"        - {result.get('title', 'N/A')[:60]}")
        
        # Analyze scene readiness
        scene_report = _analyze_scene_readiness(scene, external_context, project)
        scene_reports.append(scene_report)
    
    # Get overall status
    overall_status = _calculate_overall_status(scene_reports)
    
    # Generate daily briefing via Gemini
    daily_briefing = _generate_gemini_briefing(project, shoot_date, scene_reports)
    
    # Compile report
    report = {
        "status": "success",
        "date": shoot_date,
        "project_name": project.get("metadata", {}).get("project_name"),
        "director": project.get("metadata", {}).get("director"),
        "overall_status": overall_status,
        "scenes_count": len(scene_reports),
        "go_count": sum(1 for s in scene_reports if s["status"] == "GO"),
        "conditional_count": sum(1 for s in scene_reports if s["status"] == "CONDITIONAL"),
        "nogo_count": sum(1 for s in scene_reports if s["status"] == "NO_GO"),
        "scenes": scene_reports,
        "daily_briefing": daily_briefing,
        "generated_at": datetime.now().isoformat()
    }
    
    return report


def _analyze_scene_readiness(scene: dict[str, Any], external_context: dict[str, Any], project: dict[str, Any]) -> dict[str, Any]:
    """
    Analyze if a scene is ready to shoot based on project data + external data.
    
    Returns go/no-go decision with reasoning.
    """
    
    scene_id = scene.get("scene_id")
    title = scene.get("scene_title", "Unknown")
    cast_required = scene.get("cast_required", [])
    equipment_required = scene.get("equipment_required", [])
    location_id = scene.get("location_id")
    interior_exterior = scene.get("interior_exterior", "INTERIOR")
    
    issues = []
    risk_factors = []
    
    # Check 1: Cast Availability
    cast_data = project.get("cast", [])
    for cast_id in cast_required:
        actor = next((c for c in cast_data if c.get("actor_id") == cast_id), None)
        if actor:
            avail_status = actor.get("availability", {}).get("status", "UNKNOWN")
            if avail_status != "AVAILABLE":
                issues.append(f"Cast: {actor.get('name')} {avail_status}")
                risk_factors.append("CAST_UNAVAILABLE")
    
    # Check 2: Equipment Status
    equipment_data = project.get("equipment", [])
    for eq_id in equipment_required:
        equipment = next((e for e in equipment_data if e.get("equipment_id") == eq_id), None)
        if equipment:
            eq_status = equipment.get("status", "UNKNOWN")
            if eq_status != "AVAILABLE":
                issues.append(f"Equipment: {equipment.get('name')} {eq_status}")
                risk_factors.append("EQUIPMENT_UNAVAILABLE")
    
    # Check 3: Location/Weather (from external context)
    if external_context.get("status") == "success":
        ext_ctx = external_context.get("external_context", {})
        
        # Weather check
        if interior_exterior == "EXTERIOR":
            weather_data = ext_ctx.get("WEATHER", {}).get("results", [])
            if weather_data:
                for w in weather_data[:2]:
                    snippet = w.get("snippet", "")
                    if "rain" in snippet.lower() or "storm" in snippet.lower():
                        issues.append(f"Weather: {snippet}")
                        risk_factors.append("WEATHER_RISK")
                        break
        
        # Alerts check
        alerts_data = ext_ctx.get("PUBLIC_ALERTS", {}).get("results", [])
        for alert in alerts_data[:2]:
            snippet = alert.get("snippet", "")
            if "warning" in snippet.lower() or "alert" in snippet.lower() or "closed" in snippet.lower():
                issues.append(f"Alert: {snippet}")
                risk_factors.append("PUBLIC_ALERT")
                break
        
        # Location access
        access_data = ext_ctx.get("LOCATION_ACCESS", {}).get("results", [])
        for access in access_data[:1]:
            snippet = access.get("snippet", "")
            if "blocked" in snippet.lower() or "closed" in snippet.lower():
                issues.append(f"Access: {snippet}")
                risk_factors.append("LOCATION_BLOCKED")
    
    # Determine status
    if len(issues) == 0:
        status = "GO"
        risk_level = "LOW"
    elif len(issues) <= 2 and "LOCATION_BLOCKED" not in risk_factors and "CAST_UNAVAILABLE" not in risk_factors:
        status = "CONDITIONAL"
        risk_level = "MEDIUM" if "WEATHER_RISK" in risk_factors else "LOW"
    else:
        status = "NO_GO"
        risk_level = "CRITICAL" if "LOCATION_BLOCKED" in risk_factors or "CAST_UNAVAILABLE" in risk_factors else "HIGH"
    
    return {
        "scene_id": scene_id,
        "scene_title": title,
        "scheduled_time": scene.get("shooting_schedule", {}).get("time_of_day", "UNKNOWN"),
        "duration_hours": scene.get("shooting_schedule", {}).get("duration_hours"),
        "status": status,
        "risk_level": risk_level,
        "issues": issues,
        "risk_factors": risk_factors,
        "cast_required": [next((c.get("name") for c in project.get("cast", []) if c.get("actor_id") == cid), cid) for cid in cast_required],
        "equipment_required": [next((e.get("name") for e in project.get("equipment", []) if e.get("equipment_id") == eid), eid) for eid in equipment_required],
        "location": location_id,
        "exterior": interior_exterior == "EXTERIOR"
    }


def _calculate_overall_status(scene_reports: list[dict[str, Any]]) -> str:
    """
    Calculate overall production status for the day.
    """
    
    no_go = sum(1 for s in scene_reports if s["status"] == "NO_GO")
    conditional = sum(1 for s in scene_reports if s["status"] == "CONDITIONAL")
    go = sum(1 for s in scene_reports if s["status"] == "GO")
    
    if no_go > 0:
        return "PRODUCTION_AT_RISK"
    elif conditional > 0:
        return "PROCEED_WITH_CAUTION"
    else:
        return "READY_TO_PROCEED"


def _generate_gemini_briefing(project: dict[str, Any], shoot_date: str, scene_reports: list[dict[str, Any]]) -> str:
    """
    Use Gemini to generate human-readable daily briefing for crew.
    """
    
    prompt = f"""
You are a Production Manager briefing the crew for today's shoot.
Based on this information, write a SHORT (150 words max) briefing for the crew.

PROJECT: {project.get('metadata', {}).get('project_name')}
DATE: {shoot_date}
DIRECTOR: {project.get('metadata', {}).get('director')}

TODAY'S SCENES:
{json.dumps([{
    'scene': s['scene_title'],
    'time': s['scheduled_time'],
    'duration': s['duration_hours'],
    'status': s['status'],
    'issues': s['issues'],
    'cast': s['cast_required'],
    'equipment': s['equipment_required']
} for s in scene_reports], indent=2)}

BRIEFING REQUIREMENTS:
1. Start with overall status (GO/CONDITIONAL/AT_RISK)
2. List today's scenes
3. Highlight any issues or risks
4. Give specific instructions for crew
5. End with confidence level

FORMAT: Clear, actionable, crew-friendly language.
"""
    
    model = genai.GenerativeModel(MODEL)
    response = model.generate_content(prompt)
    return response.text
