import json
import os
from typing import Any


def load_dataset(data_dir: str = "data") -> dict[str, Any]:
    """Loads all production JSON files into memory."""
    files = ["production", "scenes", "actors", "locations", "equipment", "schedule"]
    dataset = {}

    for name in files:
        file_path = os.path.join(data_dir, f"{name}.json")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                dataset[name] = json.load(f)
        else:
            dataset[name] = []

    return dataset


def get_scene_by_id(scene_id: str, dataset: dict[str, Any]) -> dict[str, Any]:
    """Retrieves a scene by its ID from the dataset."""
    for scene in dataset.get("scenes", []):
        if scene["scene_id"] == scene_id:
            return scene
    return {}
