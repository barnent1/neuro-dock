
"""
Editor Context MCP Tool Handler for NeuroDock

This module implements the handler for the MCP editor-context tool, supporting context queries for VSCode editor integration via the Model Context Protocol.
All logic is modular, robustly error-handled, and thoroughly commented for clarity and maintainability.
"""
from typing import Dict, Any
import logging
from neurodock.services.context_selector import ContextSelector
from neurodock.models.memory import MemoryType
from neurodock.services.project_settings import ProjectSettings

logger = logging.getLogger(__name__)

async def handle_editor_context(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle editor context query via MCP (for VSCode integration).
    Args:
        data: Dictionary containing query fields (query, filePath, projectId, etc.)
    Returns:
        Dict with success status, context, project_id, and message.
    """
    try:
        # For now, reuse the context query logic (can be specialized later)
        query = data.get("query")
        file_path = data.get("filePath")
        project_id = data.get("projectId")

        # Try to infer project from file path
        if not project_id and file_path:
            project_path = _infer_project_path(file_path)
            if project_path:
                settings = ProjectSettings.load_settings(project_path)
                project_id = settings.get("project_id")

        # Use a specialized selector or fallback to ContextSelector
        memories = await ContextSelector.select_context(
            query=query,
            max_memories=10,
            project_id=project_id
        )

        context_items = []
        for memory in memories:
            context_items.append({
                "id": str(memory.id),
                "content": memory.content,
                "type": memory.type.value,
                "timestamp": memory.timestamp.isoformat(),
                "source": memory.source,
                "project_id": memory.project_id
            })

        return {
            "success": True,
            "context": context_items,
            "project_id": project_id,
            "message": f"Found {len(context_items)} relevant items for editor"
        }

    except Exception as e:
        logger.error(f"Error querying editor context: {str(e)}")
        return {
            "success": False,
            "message": f"Error querying editor context: {str(e)}"
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
