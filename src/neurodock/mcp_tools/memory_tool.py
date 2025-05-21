"""
Memory MCP Tool Handler for NeuroDock

This module implements the handler for the MCP memory tool, supporting memory storage via the Model Context Protocol.
All logic is modular, robustly error-handled, and thoroughly commented for clarity and maintainability.
"""
from typing import Dict, Any
import logging
from neurodock.models.memory import MemoryCreate, MemoryType
from neurodock.neo4j.memory_repository import MemoryRepository
from neurodock.services.project_settings import ProjectSettings

logger = logging.getLogger(__name__)

async def handle_memory_store(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle storing memory via MCP.
    Args:
        data: Dictionary containing memory fields (content, type, source, filePath, projectId, etc.)
    Returns:
        Dict with success status, memory_id, project_id, and message.
    """
    try:
        content = data.get("content")
        memory_type_str = data.get("type", "normal").lower()
        source = data.get("source", "vscode")
        file_path = data.get("filePath")
        project_id = data.get("projectId")
        project_path = data.get("projectPath")

        # If no explicit project ID was provided but we have a file path, try to determine the project from the file path
        if not project_id and file_path:
            project_path = _infer_project_path(file_path)
            if project_path:
                settings = ProjectSettings.load_settings(project_path)
                project_id = settings.get("project_id")

        # Map the string to MemoryType (default to NORMAL)
        memory_type = MemoryType.NORMAL
        for m_type in MemoryType:
            if m_type.value == memory_type_str:
                memory_type = m_type
                break

        # Validate required fields
        if not content:
            logger.error("No content provided for memory storage.")
            return {"success": False, "message": "Content is required to store memory."}

        memory_create = MemoryCreate(
            content=content,
            type=memory_type,
            source=source,
            project_id=project_id
        )

        # Store the memory in the repository
        memory = await MemoryRepository.create_memory(memory_create)

        return {
            "success": True,
            "memory_id": str(memory.id),
            "project_id": project_id,
            "message": "Memory stored successfully"
        }

    except Exception as e:
        logger.error(f"Error storing memory: {str(e)}")
        return {
            "success": False,
            "message": f"Error storing memory: {str(e)}"
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
