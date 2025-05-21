
"""
Task MCP Tool Handler for NeuroDock

This module implements the handler for the MCP task tool, supporting task creation via the Model Context Protocol.
All logic is modular, robustly error-handled, and thoroughly commented for clarity and maintainability.
"""
from typing import Dict, Any
import logging
from uuid import UUID
from neurodock.models.task import TaskCreate, TaskPriority
from neurodock.neo4j.task_repository import TaskRepository
from neurodock.services.project_settings import ProjectSettings

logger = logging.getLogger(__name__)

async def handle_task_create(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle task creation via MCP.
    Args:
        data: Dictionary containing task fields (title, description, priority, parent_id, filePath, projectId, etc.)
    Returns:
        Dict with success status, task_id, project_id, and message.
    """
    try:
        title = data.get("title")
        description = data.get("description", "")
        priority_value = data.get("priority", 3)
        parent_id_str = data.get("parent_id")
        project_id = data.get("projectId")

        # If a file path is provided, try to infer the project
        if not project_id and data.get("filePath"):
            project_path = _infer_project_path(data.get("filePath"))
            if project_path:
                settings = ProjectSettings.load_settings(project_path)
                project_id = settings.get("project_id")

        # Parse priority (default to MEDIUM)
        priority = TaskPriority.MEDIUM
        try:
            priority_int = int(priority_value)
            for p in TaskPriority:
                if p.value == priority_int:
                    priority = p
                    break
        except Exception:
            pass

        # Parse parent ID if provided
        parent_id = UUID(parent_id_str) if parent_id_str else None

        # Validate required fields
        if not title:
            logger.error("No title provided for task creation.")
            return {"success": False, "message": "Title is required to create a task."}

        task_create = TaskCreate(
            title=title,
            description=description,
            priority=priority,
            parent_id=parent_id,
            metadata={"project_id": project_id} if project_id else {}
        )

        # Store the task in the repository
        task = await TaskRepository.create_task(task_create)

        return {
            "success": True,
            "task_id": str(task.id),
            "project_id": project_id,
            "message": "Task created successfully"
        }

    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        return {
            "success": False,
            "message": f"Error creating task: {str(e)}"
        }

def _infer_project_path(file_path: str):
    """
    Infer the project path from a file path. Returns None if not found.
    """
    import pathlib
    try:
        current_dir = pathlib.Path(file_path).parent
        while current_dir != current_dir.parent:
            if (current_dir / "neurodock.json").exists():
                return str(current_dir)
            current_dir = current_dir.parent
        return None
    except Exception as e:
        logger.error(f"Error inferring project path: {str(e)}")
        return None
