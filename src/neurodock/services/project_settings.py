from typing import Dict, Optional, Any
import os
import json
import logging

logger = logging.getLogger(__name__)

class ProjectSettings:
    """
    Handler for project-specific settings stored in neurodock.json files.
    """
    
    @staticmethod
    def load_settings(project_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load project settings from neurodock.json file.
        
        Args:
            project_path: Path to the project directory. If None, tries to infer from context.
            
        Returns:
            Dictionary of project settings
        """
        # Default settings
        default_settings = {
            "project_id": os.path.basename(project_path) if project_path else "default",
            "name": os.path.basename(project_path) if project_path else "Default Project",
            "memory_isolation_level": "strict",  # Options: none, loose, strict
            "memory_ttl_days": 90,  # Time to live for memories in days
            "task_auto_creation": True,
        }
        
        if not project_path:
            logger.warning("No project path provided, using default settings")
            return default_settings
            
        config_path = os.path.join(project_path, "neurodock.json")
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    settings = json.load(f)
                
                # Merge with defaults (keeping user settings where provided)
                for key, value in default_settings.items():
                    if key not in settings:
                        settings[key] = value
                
                return settings
            else:
                logger.info(f"No neurodock.json found in {project_path}, using default settings")
                return default_settings
                
        except Exception as e:
            logger.error(f"Error loading neurodock.json: {str(e)}")
            return default_settings
    
    @staticmethod
    def create_default_config(project_path: str) -> Dict[str, Any]:
        """
        Create a default neurodock.json configuration file.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Dictionary of created settings
        """
        project_name = os.path.basename(project_path)
        
        config = {
            "project_id": project_name,
            "name": project_name,
            "description": f"NeuroDock configuration for {project_name}",
            "memory_isolation_level": "strict",
            "memory_ttl_days": 90,
            "task_auto_creation": True,
            "agent_enabled": True,
            "excluded_paths": [
                "node_modules",
                "dist",
                "build",
                ".git",
                "__pycache__",
                "*.pyc"
            ],
            "memory_types": {
                "code": True,
                "documentation": True,
                "comment": True,
                "important": True,
                "normal": True,
                "trivial": False
            }
        }
        
        config_path = os.path.join(project_path, "neurodock.json")
        
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Created default neurodock.json in {project_path}")
            return config
        except Exception as e:
            logger.error(f"Error creating neurodock.json: {str(e)}")
            return {}
