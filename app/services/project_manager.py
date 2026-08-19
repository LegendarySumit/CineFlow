"""
Project Manager - Handles multi-project setup and persistence.
Allows directors to upload and manage multiple film productions.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class ProjectManager:
    """Manages multiple film production projects."""
    
    def __init__(self, projects_dir: str = "projects"):
        self.projects_dir = projects_dir
        self.active_project_id: Optional[str] = None
        self.active_project_data: Optional[Dict[str, Any]] = None
        os.makedirs(projects_dir, exist_ok=True)
    
    def validate_production_data(self, production_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate production.json structure - supports both old and new formats."""
        
        # Check if it's the new comprehensive format
        if 'metadata' in production_data:
            required_fields = ['project_id', 'project_name', 'cast', 'equipment', 'locations', 'scenes']
        else:
            required_fields = ['production_id', 'name', 'scenes', 'cast', 'budget']
        
        missing = [f for f in required_fields if f not in production_data]
        
        if missing:
            return {
                'valid': False,
                'errors': [f'Missing required field: {f}' for f in missing]
            }
        
        errors = []
        
        # Validate scenes
        scenes = production_data.get('scenes', [])
        if not isinstance(scenes, list) or len(scenes) == 0:
            errors.append(f'Scenes must be non-empty array. Found: {len(scenes) if isinstance(scenes, list) else "not a list"}')
        else:
            for idx, scene in enumerate(scenes):
                if 'scene_id' not in scene:
                    errors.append(f'Scene {idx}: missing scene_id')
                if 'scene_title' not in scene and 'title' not in scene:
                    errors.append(f'Scene {idx}: missing scene_title or title')
        
        # Validate cast
        cast = production_data.get('cast', [])
        if not isinstance(cast, list) or len(cast) == 0:
            errors.append(f'Cast must be non-empty array. Found: {len(cast) if isinstance(cast, list) else "not a list"}')
        
        # Validate budget (optional for new format)
        if 'budget' in production_data or 'production_budget_inr' in production_data:
            budget = production_data.get('budget') or production_data.get('production_budget_inr', 0)
            if not isinstance(budget, (int, float)) or budget <= 0:
                errors.append(f'Budget must be positive number. Found: {budget}')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors if errors else [],
            'scenes_count': len(scenes) if isinstance(scenes, list) else 0,
            'cast_count': len(cast) if isinstance(cast, list) else 0
        }
    
    def create_project(self, project_id: str, production_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create and save a new project - supports both old and new comprehensive formats."""
        
        # Validate first
        validation = self.validate_production_data(production_data)
        if not validation['valid']:
            return {
                'status': 'error',
                'message': 'Invalid production data',
                'errors': validation['errors']
            }
        
        # Save to file
        project_path = os.path.join(self.projects_dir, f'{project_id}.json')
        
        # Handle both old and new formats
        if 'metadata' in production_data:
            # New comprehensive format
            project_file = production_data
            if 'metadata' not in project_file:
                project_file['metadata'] = {}
            project_file['metadata']['project_id'] = project_id
            project_file['metadata']['created_at'] = datetime.utcnow().isoformat()
        else:
            # Old format - convert to new
            project_file = {
                'metadata': {
                    'project_id': project_id,
                    'project_name': production_data.get('name'),
                    'director': production_data.get('director', 'Unknown'),
                    'created_at': datetime.utcnow().isoformat(),
                    'scenes_count': validation['scenes_count'],
                    'cast_count': validation['cast_count'],
                    'budget': production_data.get('budget'),
                    'status': production_data.get('status', 'PRE_PRODUCTION')
                },
                'production': production_data
            }
        
        try:
            with open(project_path, 'w') as f:
                json.dump(project_file, f, indent=2)
            
            return {
                'status': 'success',
                'project_id': project_id,
                'message': f'Project created successfully',
                'metadata': project_file.get('metadata', {}),
                'scenes_count': validation['scenes_count'],
                'cast_count': validation['cast_count']
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to save project: {str(e)}'
            }
    
    def load_project(self, project_id: str) -> Dict[str, Any]:
        """Load a project and set as active."""
        
        project_path = os.path.join(self.projects_dir, f'{project_id}.json')
        
        if not os.path.exists(project_path):
            return {
                'status': 'error',
                'message': f'Project not found: {project_id}'
            }
        
        try:
            with open(project_path, 'r') as f:
                project_data = json.load(f)
            
            self.active_project_id = project_id
            self.active_project_data = project_data['production']
            
            return {
                'status': 'success',
                'project_id': project_id,
                'metadata': project_data['metadata'],
                'scenes': [{'scene_id': s.get('scene_id'), 'title': s.get('title')} for s in self.active_project_data.get('scenes', [])]
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to load project: {str(e)}'
            }
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all available projects."""
        
        projects = []
        
        try:
            for filename in os.listdir(self.projects_dir):
                if filename.endswith('.json'):
                    project_id = filename[:-5]
                    filepath = os.path.join(self.projects_dir, filename)
                    
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        metadata = data.get('metadata', {})
                        projects.append({
                            'project_id': project_id,
                            'name': metadata.get('name', 'Unknown'),
                            'scenes_count': metadata.get('scenes_count', 0),
                            'budget': metadata.get('budget', 0),
                            'created_at': metadata.get('created_at')
                        })
        except Exception as e:
            logger.error(f'Error listing projects: {e}', exc_info=True)
        
        return sorted(projects, key=lambda x: x.get('created_at', ''), reverse=True)
    
    def get_active_project(self) -> Optional[Dict[str, Any]]:
        """Get currently active project data."""
        return self.active_project_data
    
    def get_scene(self, scene_id: str) -> Optional[Dict[str, Any]]:
        """Get scene data from active project."""
        
        if not self.active_project_data:
            return None
        
        scenes = self.active_project_data.get('scenes', [])
        for scene in scenes:
            if scene.get('scene_id') == scene_id:
                return scene
        
        return None
    
    def delete_project(self, project_id: str) -> Dict[str, Any]:
        """Delete a project."""
        
        project_path = os.path.join(self.projects_dir, f'{project_id}.json')
        
        if not os.path.exists(project_path):
            return {'status': 'error', 'message': f'Project not found: {project_id}'}
        
        try:
            os.remove(project_path)
            
            # Clear active if it was the deleted project
            if self.active_project_id == project_id:
                self.active_project_id = None
                self.active_project_data = None
            
            return {'status': 'success', 'message': f'Project deleted: {project_id}'}
        except Exception as e:
            return {'status': 'error', 'message': f'Failed to delete: {str(e)}'}


# Global project manager instance
_project_manager = ProjectManager()


def get_project_manager() -> ProjectManager:
    """Get the global project manager instance."""
    return _project_manager
