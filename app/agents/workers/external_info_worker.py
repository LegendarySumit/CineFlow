"""
EXTERNAL INFO WORKER - Autonomous external world investigation via Parallel MCP.

Role: Investigate real-world conditions that impact production decisions.
Responsibility: Query Parallel AI MCP for:
  - Weather conditions
  - Location information & accessibility
  - Travel/access disruptions
  - Local events
  - News & announcements
  - Venue/location operational status
  - Public alerts

Architecture:
  CineFlow (Internal Data) + Parallel MCP (External World) → Gemini Reasoning → Decision
"""

from typing import Any

from app.tools.parallel_mcp import parallel_web_search
from app.tools.production import get_scene_by_id, load_dataset


def gather_external_context(scene_id: str, crisis_query: str, project_data: dict[str, Any] = None, crisis_type: str = None) -> dict[str, Any]:
    """
    Autonomously investigate external world conditions relevant to the crisis.
    
    CRISIS-TYPE-AWARE: Only queries relevant dimensions based on crisis type:
    - CAST crisis: Skip weather, focus on cast availability/health/alternative actors
    - EQUIPMENT crisis: Skip weather, focus on equipment rental/repair availability
    - LOCATION crisis: Focus on location access/permits/alternatives, weather if outdoor
    - WEATHER crisis: Focus on weather forecasts and outdoor viability
    - SCHEDULE crisis: Focus on calendar conflicts and timing
    
    Now supports both old format (data/) and new comprehensive format (projects/)
    """
    
    # If project_data provided (new format), use it directly
    if project_data:
        scene = None
        for s in project_data.get('scenes', []):
            if s['scene_id'] == scene_id:
                scene = s
                break
        
        if not scene:
            return {
                "status": "error",
                "message": f"Scene {scene_id} not found",
                "scene_id": scene_id
            }
        
        location = scene.get("location_id", "Unknown")
        interior_exterior = "EXTERIOR" if "EXTERIOR" in scene.get("interior_exterior", "") else "INTERIOR"
        date = scene.get("shooting_schedule", {}).get("shoot_date", "Unknown")
    else:
        # Old format - load from data/
        dataset = load_dataset("data")
        scene = get_scene_by_id(scene_id, dataset)
        
        if not scene:
            return {
                "status": "error",
                "message": f"Scene {scene_id} not found",
                "scene_id": scene_id
            }
        
        location = scene.get("location", "Unknown")
        interior_exterior = scene.get("interior_exterior", "UNKNOWN")
        date = _get_scene_date(scene_id, dataset)
    
    external_data = {}
    queries = _build_investigation_queries(location, interior_exterior, crisis_query, date, crisis_type)
    
    print("\n[EXTERNAL INFO WORKER] Autonomous Investigation (Crisis-Type-Aware)")
    print(f"  Crisis Type: {crisis_type or 'UNKNOWN'}")
    print(f"  Location: {location}")
    print(f"  Scene Type: {interior_exterior}")
    print(f"  Date: {date}")
    print(f"  Queries: {len(queries)} (filtered for {crisis_type or 'general'} crisis)")
    
    for query_type, query_text in queries:
        print(f"  -> Investigating: {query_type}")
        result = parallel_web_search(query_text)
        external_data[query_type] = result
    
    return {
        "status": "success",
        "scene_id": scene_id,
        "location": location,
        "interior_exterior": interior_exterior,
        "date": date,
        "crisis_type": crisis_type,
        "external_context": external_data,
        "investigation_dimensions": list(external_data.keys()),
        "total_sources": sum(len(result.get("results", [])) for result in external_data.values()),
        "data_quality": _assess_data_quality(external_data)
    }


def _get_scene_date(scene_id: str, dataset: dict[str, Any]) -> str:
    """Extract shooting date from schedule."""
    schedule = dataset.get("schedule", [])
    entry = next((s for s in schedule if s["scene_id"] == scene_id), None)
    if entry:
        return entry.get("date", "Unknown")
    return "Unknown"


def _build_investigation_queries(
    location: str,
    interior_exterior: str,
    crisis_query: str,
    date: str,
    crisis_type: str = None
) -> list[tuple[str, str]]:
    """
    Autonomously decide which external dimensions to investigate.
    
    CRISIS-TYPE-AWARE FILTERING:
    - CAST: Skip weather, focus on actor/health availability
    - EQUIPMENT: Skip weather, focus on rental/repair/alternative equipment
    - LOCATION: Focus on access/permits, weather only if outdoor
    - WEATHER: Focus on forecasts/conditions
    - SCHEDULE: Focus on calendar/timing
    
    Returns: List of (query_type, query_text) tuples
    """
    
    queries = []
    
    # Skip weather queries for CAST/EQUIPMENT crises (not relevant)
    include_weather = crisis_type not in ["CAST", "EQUIPMENT"]
    
    # 1. WEATHER - Only for non-CAST/EQUIPMENT crises and outdoor scenes
    if include_weather and interior_exterior == "EXTERIOR":
        queries.append((
            "WEATHER",
            f"Weather forecast {location} {date} conditions alerts storms rain monsoon"
        ))
    
    # 2. LOCATION ACCESSIBILITY - Always relevant
    queries.append((
        "LOCATION_ACCESS",
        f"{location} accessibility road closures travel disruptions access restrictions"
    ))
    
    # 3. VENUE/FACILITY STATUS - Always relevant
    queries.append((
        "VENUE_STATUS",
        f"{location} facility operational status closed shutdowns alerts"
    ))
    
    # 4. LOCAL EVENTS - Can block access (relevant for all crisis types)
    queries.append((
        "LOCAL_EVENTS",
        f"Events {location} {date} festivals shutdowns demonstrations public gatherings"
    ))
    
    # 5. PUBLIC ANNOUNCEMENTS - Safety alerts (always relevant)
    queries.append((
        "PUBLIC_ALERTS",
        f"Announcements alerts {location} government warnings restrictions {date}"
    ))
    
    # 6. CAST-SPECIFIC NEWS - For CAST crises only
    if crisis_type == "CAST":
        queries.append((
            "CAST_AVAILABILITY",
            f"Cast health availability hospitalizations emergencies {location} {date}"
        ))
        queries.append((
            "ALTERNATIVE_ACTORS",
            f"Available actors casting agencies {location} {date} emergency replacements"
        ))
    
    # 7. EQUIPMENT-SPECIFIC NEWS - For EQUIPMENT crises only
    if crisis_type == "EQUIPMENT":
        queries.append((
            "EQUIPMENT_RENTAL",
            f"Equipment rental services {location} camera audio replacement alternatives"
        ))
        queries.append((
            "REPAIR_SERVICES",
            f"Equipment repair services {location} emergency fix same-day turnaround"
        ))
    
    # 8. General equipment news - For equipment-related queries
    if "equipment" in crisis_query.lower():
        queries.append((
            "EQUIPMENT_NEWS",
            f"Equipment {location} repair services availability rental alternatives"
        ))
    
    if "damage" in crisis_query.lower() or "damaged" in crisis_query.lower():
        queries.append((
            "DAMAGE_NEWS",
            f"Damage reports {location} infrastructure impact response"
        ))
    
    # 9. INFRASTRUCTURE - Always relevant
    queries.append((
        "INFRASTRUCTURE",
        f"Infrastructure {location} utilities power water status operational"
    ))
    
    return queries


def _assess_data_quality(external_data: dict[str, Any]) -> dict[str, Any]:
    """
    Assess quality and completeness of external data gathered.
    
    Returns: Quality metrics for Gemini evaluation
    """
    
    total_results = sum(len(data.get("results", [])) for data in external_data.values())
    successful_queries = sum(1 for data in external_data.values() if data.get("status") == "success")
    total_queries = len(external_data)
    
    # Detect if using fallback mock data
    has_real_data = any(
        data.get("source") == "web_search" 
        for data in external_data.values()
    )
    
    quality_score = (successful_queries / total_queries * 100) if total_queries > 0 else 0
    
    return {
        "total_queries": total_queries,
        "successful_queries": successful_queries,
        "total_results": total_results,
        "quality_score": round(quality_score, 1),
        "has_real_data": has_real_data,
        "source_types": list({data.get("source", "unknown") for data in external_data.values()})
    }
