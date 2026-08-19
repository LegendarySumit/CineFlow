import json
import os
from typing import Any


def load_dataset(data_dir: str = "data") -> dict[str, Any]:
    """Loads all production JSON files into memory.
    Falls back to empty dataset if directory doesn't exist (new format uses projects/ folder)."""
    files = ["production", "scenes", "actors", "locations", "equipment", "schedule"]
    dataset = {}

    # If data_dir doesn't exist, return empty dataset
    if not os.path.exists(data_dir):
        for name in files:
            dataset[name] = []
        return dataset

    for name in files:
        file_path = os.path.join(data_dir, f"{name}.json")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                dataset[name] = json.load(f)
        else:
            dataset[name] = []

    return dataset


def load_project(project_id: str, projects_dir: str = "projects") -> dict[str, Any]:
    """Loads a complete project JSON file from the projects folder."""
    project_file = None
    
    # Find project file by ID
    for filename in os.listdir(projects_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(projects_dir, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("metadata", {}).get("project_id") == project_id:
                        return data
            except (json.JSONDecodeError, IOError):
                continue
    
    return None


def get_all_projects(projects_dir: str = "projects") -> list[dict[str, Any]]:
    """Lists all available projects."""
    projects = []
    
    if not os.path.exists(projects_dir):
        return projects
    
    for filename in os.listdir(projects_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(projects_dir, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    projects.append({
                        "project_id": data.get("metadata", {}).get("project_id"),
                        "project_name": data.get("metadata", {}).get("project_name"),
                        "director": data.get("metadata", {}).get("director"),
                        "status": data.get("metadata", {}).get("status"),
                        "total_shoot_days": data.get("metadata", {}).get("total_shoot_days"),
                        "scenes_count": len(data.get("scenes", []))
                    })
            except (json.JSONDecodeError, IOError):
                continue
    
    return projects


def convert_project_to_dataset(project: dict[str, Any]) -> dict[str, Any]:
    """Converts a new project format into the legacy dataset format for backward compatibility."""
    dataset = {
        "production": project.get("metadata", {}),
        "scenes": project.get("scenes", []),
        "cast": project.get("cast", []),
        "locations": project.get("locations", []),
        "equipment": project.get("equipment", []),
        "schedule": []
    }
    
    return dataset


def get_scene_by_id(scene_id: str, dataset: dict[str, Any]) -> dict[str, Any]:
    """Retrieves a scene by its ID from the dataset."""
    for scene in dataset.get("scenes", []):
        if scene["scene_id"] == scene_id:
            return scene
    return {}


def get_actor_by_id(actor_id: str, dataset: dict[str, Any]) -> dict[str, Any]:
    """Retrieves an actor by their ID from the dataset."""
    for actor in dataset.get("cast", []):
        if actor["actor_id"] == actor_id:
            return actor
    return {}


def get_equipment_by_id(equipment_id: str, dataset: dict[str, Any]) -> dict[str, Any]:
    """Retrieves equipment by its ID from the dataset."""
    for eq in dataset.get("equipment", []):
        if eq["equipment_id"] == equipment_id:
            return eq
    return {}


def get_location_by_id(location_id: str, dataset: dict[str, Any]) -> dict[str, Any]:
    """Retrieves a location by its ID from the dataset."""
    for loc in dataset.get("locations", []):
        if loc["location_id"] == location_id:
            return loc
    return {}
