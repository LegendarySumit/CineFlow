"""
FORMAT COMPATIBILITY LAYER

Provides helpers to work seamlessly with both old data/ format and new project_data format.

Old Format (data/):
- locations: has 'name', 'type', 'weather_dependent'
- actors: has 'name', 'role', 'availability' as dict of dates
- equipment: has 'name', 'category', 'status'
- scenes: has 'cast_ids', 'equipment_ids', 'dependencies' as dict

New Format (project_data):
- locations: has 'location_name', 'location_type', 'weather_dependency'
- actors: has 'name', 'role', 'availability' with 'status', 'available_from', 'available_until'
- equipment: has 'name', 'category', 'status'
- scenes: has 'cast_required', 'equipment_required', 'dependencies' as string or null
"""

from typing import Any


def detect_format(dataset: dict[str, Any]) -> str:
    """
    Detect if dataset is old or new format.
    
    Returns: 'new' or 'old'
    """
    if not dataset or not dataset.get('locations'):
        return 'old'  # Default to old if can't detect
    
    loc = dataset['locations'][0]
    # New format has 'location_name', old has 'name'
    if 'location_name' in loc:
        return 'new'
    elif 'name' in loc:
        return 'old'
    
    return 'old'  # Default


# Helper functions for backward compatibility
def _detect_format_from_scenes(scenes: list[dict[str, Any]]) -> str:
    """Detect format from scenes list"""
    if not scenes:
        return 'old'
    
    scene = scenes[0]
    # New format has 'cast_required', old has 'cast_ids'
    if 'cast_required' in scene:
        return 'new'
    elif 'cast_ids' in scene:
        return 'old'
    
    return 'old'


def get_location_name(location: dict[str, Any], is_new_format: bool = True) -> str:
    """Extract location name from either format"""
    if is_new_format:
        return location.get('location_name', '')
    else:
        return location.get('name', '')


def get_location_type(location: dict[str, Any], is_new_format: bool = True) -> str:
    """Extract location type from either format"""
    if is_new_format:
        return location.get('location_type', 'UNKNOWN')
    else:
        return location.get('type', 'UNKNOWN')


def get_location_weather_dependency(location: dict[str, Any], is_new_format: bool = True) -> str:
    """Extract weather dependency from either format"""
    if is_new_format:
        return location.get('weather_dependency', 'NONE')
    else:
        # Old format has boolean 'weather_dependent'
        is_dependent = location.get('weather_dependent', False)
        return 'CRITICAL' if is_dependent else 'NONE'


def normalize_locations(dataset: dict[str, Any]) -> dict[str, str]:
    """
    Create name → ID mapping for locations, handling both formats.
    
    Returns: {'location_name': 'location_id', ...}
    """
    fmt = detect_format(dataset)
    locations_dict = {}
    
    for loc in dataset.get('locations', []):
        name = get_location_name(loc, is_new_format=(fmt == 'new'))
        loc_id = loc.get('location_id')
        if name and loc_id:
            locations_dict[name] = loc_id
    
    return locations_dict


def normalize_actors(dataset: dict[str, Any]) -> dict[str, str]:
    """
    Create name → ID mapping for actors.
    Name field is same in both formats.
    
    Returns: {'actor_name': 'actor_id', ...}
    """
    actors_dict = {}
    
    for actor in dataset.get('actors', []) or []:
        # 'cast' is the key in new format, 'actors' in old
        name = actor.get('name')
        actor_id = actor.get('actor_id')
        if name and actor_id:
            actors_dict[name] = actor_id
    
    return actors_dict


def normalize_equipment(dataset: dict[str, Any]) -> dict[str, str]:
    """
    Create name → ID mapping for equipment.
    Name field is same in both formats.
    
    Returns: {'equipment_name': 'equipment_id', ...}
    """
    equipment_dict = {}
    
    for eq in dataset.get('equipment', []):
        name = eq.get('name')
        eq_id = eq.get('equipment_id')
        if name and eq_id:
            equipment_dict[name] = eq_id
    
    return equipment_dict


def get_scene_cast_ids(scene: dict[str, Any], is_new_format: bool = True) -> list[str]:
    """Extract cast IDs from either scene format"""
    if is_new_format:
        return scene.get('cast_required', [])
    else:
        return scene.get('cast_ids', [])


def get_scene_equipment_ids(scene: dict[str, Any], is_new_format: bool = True) -> list[str]:
    """Extract equipment IDs from either scene format"""
    if is_new_format:
        return scene.get('equipment_required', [])
    else:
        return scene.get('equipment_ids', [])


def get_scene_title(scene: dict[str, Any], is_new_format: bool = True) -> str:
    """Extract scene title from either format"""
    if is_new_format:
        return scene.get('scene_title', scene.get('title', ''))
    else:
        return scene.get('title', '')


def get_scene_duration(scene: dict[str, Any], is_new_format: bool = True) -> float:
    """Extract scene duration from either format"""
    if is_new_format:
        # New format: scene["shooting_schedule"]["duration_hours"]
        return scene.get('shooting_schedule', {}).get('duration_hours', 0)
    else:
        # Old format: scene["duration_hours"]
        return scene.get('duration_hours', 0)


def get_scene_dependencies(scene: dict[str, Any], is_new_format: bool = True) -> list[str]:
    """
    Extract scene dependencies, handling both formats.
    
    New format: "None" string or null
    Old format: dict with "cast_blocking", "location_blocking", etc.
    
    Returns: list of blocking reasons
    """
    if is_new_format:
        deps = scene.get('dependencies', 'None')
        # New format: just a string or null
        return [] if not deps or deps == 'None' else [deps]
    else:
        # Old format: dict with blocking info
        deps = scene.get('dependencies', {})
        if not deps:
            return []
        
        blocking = []
        if deps.get('cast_blocking'):
            blocking.append(f"cast: {','.join(deps['cast_blocking'])}")
        if deps.get('location_blocking'):
            blocking.append(f"location: {','.join(deps['location_blocking'])}")
        if deps.get('equipment_blocking'):
            blocking.append(f"equipment: {','.join(deps['equipment_blocking'])}")
        
        return blocking


def normalize_dataset(dataset: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize any dataset to have consistent field names.
    Useful for functions that don't care about format.
    
    Returns normalized dataset with:
    - locations: all have 'location_id', 'location_name', 'location_type'
    - cast/actors: all have 'actor_id', 'name', 'role'
    - equipment: all have 'equipment_id', 'name', 'category'
    - scenes: all have cast_required, equipment_required, scene_title, duration_hours
    """
    fmt = detect_format(dataset)
    is_new = (fmt == 'new')
    
    normalized = {
        'locations': [],
        'cast': [],
        'equipment': [],
        'scenes': []
    }
    
    # Normalize locations
    for loc in dataset.get('locations', []):
        normalized['locations'].append({
            'location_id': loc.get('location_id'),
            'location_name': get_location_name(loc, is_new),
            'location_type': get_location_type(loc, is_new),
            'weather_dependency': get_location_weather_dependency(loc, is_new),
        })
    
    # Normalize cast/actors
    for actor in dataset.get('cast', []) or dataset.get('actors', []):
        normalized['cast'].append({
            'actor_id': actor.get('actor_id'),
            'name': actor.get('name'),
            'role': actor.get('role'),
            'availability': actor.get('availability', {}),
        })
    
    # Normalize equipment
    for eq in dataset.get('equipment', []):
        normalized['equipment'].append({
            'equipment_id': eq.get('equipment_id'),
            'name': eq.get('name'),
            'category': eq.get('category'),
            'status': eq.get('status'),
        })
    
    # Normalize scenes
    for scene in dataset.get('scenes', []):
        normalized['scenes'].append({
            'scene_id': scene.get('scene_id'),
            'scene_title': get_scene_title(scene, is_new),
            'location_id': scene.get('location_id'),
            'cast_required': get_scene_cast_ids(scene, is_new),
            'equipment_required': get_scene_equipment_ids(scene, is_new),
            'duration_hours': get_scene_duration(scene, is_new),
            'dependencies': get_scene_dependencies(scene, is_new),
        })
    
    return normalized



# Backward compatibility helper functions for cascade_detector and other services
def _get_cast_ids(scene: dict[str, Any], is_new_format: bool = False) -> list[str]:
    """Get cast IDs from scene, handling both old and new formats"""
    return get_scene_cast_ids(scene, is_new_format)


def _get_equipment_ids(scene: dict[str, Any], is_new_format: bool = False) -> list[str]:
    """Get equipment IDs from scene, handling both old and new formats"""
    return get_scene_equipment_ids(scene, is_new_format)
