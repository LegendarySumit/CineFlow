"""
LAYER 1: DYNAMIC ENTITY EXTRACTOR

Parses unstructured user input and maps to actual database entities.
NOT hardcoded. Works with ANY production manifest.
"""

import json
import logging
import os
from typing import Any

import google.generativeai as genai
from dotenv import load_dotenv

from app.tools.format_compat import (
    detect_format,
    normalize_locations,
    normalize_actors,
    normalize_equipment,
    get_scene_cast_ids,
    get_scene_equipment_ids,
)

logger = logging.getLogger(__name__)

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# Use gemini-2.5-flash for free tier - higher quota (10 RPM, 250 RPD)
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def extract_entities(user_query: str, dataset: dict[str, Any]) -> dict[str, Any]:
    """
    Parse arbitrary user input and extract:
    - Location names → Location IDs
    - Actor names → Actor IDs
    - Equipment types → Equipment IDs
    - Permit types → Permit references
    - Time constraints → Duration in hours
    
    This is the CORE of handling arbitrary real-world input.
    Works with both old and new dataset formats.
    """
    
    # Get available entities from database (supports both old and new formats)
    locations = normalize_locations(dataset)
    actors = normalize_actors(dataset)
    equipment = normalize_equipment(dataset)
    
    # Strict JSON format example
    json_example = '{"affected_locations":[],"affected_actors":[],"affected_equipment":[],"affected_permits":[],"crisis_type":"UNKNOWN","estimated_duration_hours":24,"severity":"MEDIUM","confidence":0.5}'
    
    extraction_prompt = f"""Extract production crisis data as JSON only. No markdown, no text, just JSON.

CRISIS QUERY: {user_query}

AVAILABLE:
Locations: {list(locations.keys())}
Actors: {list(actors.keys())}
Equipment: {list(equipment.keys())}

OUTPUT EXACTLY THIS JSON FORMAT:
{json_example}

RULES:
- Return ONLY raw JSON
- No markdown code blocks
- No explanations
- Empty arrays if not mentioned"""
    
    model = genai.GenerativeModel(MODEL)
    response = model.generate_content(
        extraction_prompt,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=300,
            temperature=0.1  # Lower temperature for more consistent JSON
        )
    )
    
    extracted = {}
    try:
        content = response.text if response else ""
        
        # Clean up response
        content = content.strip()
        content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        
        extracted = json.loads(content) if content else {}
        
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse entity extraction: {e!s}. Using defaults.")
        extracted = {}
    
    # Ensure all fields exist with safe defaults
    extracted = {
        "affected_locations": extracted.get("affected_locations") or [],
        "affected_actors": extracted.get("affected_actors") or [],
        "affected_equipment": extracted.get("affected_equipment") or [],
        "affected_permits": extracted.get("affected_permits") or [],
        "crisis_type": extracted.get("crisis_type") or "UNKNOWN",
        "estimated_duration_hours": extracted.get("estimated_duration_hours") or 24,
        "severity": extracted.get("severity") or "MEDIUM",
        "confidence": extracted.get("confidence") or 0.5
    }
    
    # Map names to IDs
    location_ids = [locations.get(name) for name in extracted.get("affected_locations", []) if name in locations]
    actor_ids = [actors.get(name) for name in extracted.get("affected_actors", []) if name in actors]
    equipment_ids = [equipment.get(name) for name in extracted.get("affected_equipment", []) if name in equipment]
    
    return {
        "status": "success",
        "extracted_entities": {
            "location_ids": location_ids,
            "actor_ids": actor_ids,
            "equipment_ids": equipment_ids,
            "permit_types": extracted.get("affected_permits", [])
        },
        "crisis_classification": {
            "type": extracted.get("crisis_type"),
            "severity": extracted.get("severity"),
            "estimated_duration_hours": extracted.get("estimated_duration_hours"),
            "confidence": extracted.get("confidence", 0.5)
        },
        "original_extraction": extracted
    }


def find_affected_scenes(entities: dict[str, Any], dataset: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Given extracted entity IDs, find all scenes that depend on those entities.
    
    This is GRAPH TRAVERSAL against the user's actual production schedule.
    Works with both old and new dataset formats.
    """
    
    location_ids = entities.get("location_ids", [])
    actor_ids = entities.get("actor_ids", [])
    equipment_ids = entities.get("equipment_ids", [])
    
    fmt = detect_format(dataset)
    is_new_format = (fmt == 'new')
    
    scenes = dataset.get("scenes", [])
    affected_scenes = []
    
    for scene in scenes:
        # Check if any extracted entity is required by this scene
        location_match = scene.get("location_id") in location_ids if location_ids else False
        
        # Handle both old and new scene formats
        scene_cast = get_scene_cast_ids(scene, is_new_format)
        scene_equipment = get_scene_equipment_ids(scene, is_new_format)
        
        cast_match = any(aid in scene_cast for aid in actor_ids) if actor_ids else False
        equipment_match = any(eid in scene_equipment for eid in equipment_ids) if equipment_ids else False
        
        if location_match or cast_match or equipment_match:
            affected_scenes.append({
                "scene_id": scene["scene_id"],
                "title": scene.get("title") or scene.get("scene_title", ""),
                "reason_blocked": {
                    "location": location_match,
                    "cast": cast_match,
                    "equipment": equipment_match
                }
            })
    
    return affected_scenes
