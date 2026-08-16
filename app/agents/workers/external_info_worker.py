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


def gather_external_context(scene_id: str, crisis_query: str) -> dict[str, Any]:
    """
    Autonomously investigate external world conditions relevant to the crisis.
    
    Queries multiple dimensions:
    1. Weather & environmental conditions
    2. Location accessibility & travel disruptions
    3. Venue/facility operational status
    4. Local events & public announcements
    5. News relevant to location/equipment
    6. Infrastructure/utility status
    
    Returns: Comprehensive external context for Gemini reasoning
    """
    
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
    queries = _build_investigation_queries(location, interior_exterior, crisis_query, date)
    
    print("\n[EXTERNAL INFO WORKER] Autonomous Investigation")
    print(f"  Location: {location}")
    print(f"  Scene Type: {interior_exterior}")
    print(f"  Date: {date}")
    print(f"  Queries: {len(queries)}")
    
    for query_type, query_text in queries:
        print(f"  → Investigating: {query_type}")
        result = parallel_web_search(query_text)
        external_data[query_type] = result
    
    return {
        "status": "success",
        "scene_id": scene_id,
        "location": location,
        "interior_exterior": interior_exterior,
        "date": date,
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
    date: str
) -> list[tuple[str, str]]:
    """
    Autonomously decide which external dimensions to investigate.
    
    Returns: List of (query_type, query_text) tuples
    """
    
    queries = []
    
    # 1. WEATHER - Critical for outdoor scenes
    if interior_exterior == "EXTERIOR":
        queries.append((
            "WEATHER",
            f"Weather forecast {location} {date} conditions alerts storms rain monsoon"
        ))
    
    # 2. LOCATION ACCESSIBILITY - All scenes
    queries.append((
        "LOCATION_ACCESS",
        f"{location} accessibility road closures travel disruptions access restrictions"
    ))
    
    # 3. VENUE/FACILITY STATUS - All scenes
    queries.append((
        "VENUE_STATUS",
        f"{location} facility operational status closed shutdowns alerts"
    ))
    
    # 4. LOCAL EVENTS - Can block access or cause disruptions
    queries.append((
        "LOCAL_EVENTS",
        f"Events {location} {date} festivals shutdowns demonstrations public gatherings"
    ))
    
    # 5. PUBLIC ANNOUNCEMENTS - Safety alerts, government orders
    queries.append((
        "PUBLIC_ALERTS",
        f"Announcements alerts {location} government warnings restrictions {date}"
    ))
    
    # 6. NEWS - Relevant to location/situation
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
    
    # 7. INFRASTRUCTURE - Utilities, power, water
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
