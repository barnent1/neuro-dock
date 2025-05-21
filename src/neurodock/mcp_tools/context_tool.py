
"""
Context MCP Tool Handler for NeuroDock

This module implements the handler for the MCP context tool, supporting context queries via the Model Context Protocol.
All logic is modular, robustly error-handled, and thoroughly commented for clarity and maintainability.
"""
from typing import Dict, Any
import logging
from neurodock.services.context_selector import ContextSelector
from neurodock.models.memory import MemoryType
from neurodock.services.project_settings import ProjectSettings

logger = logging.getLogger(__name__)

async def handle_context_query(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle context query via MCP.
    Args:
        data: Dictionary containing query fields (query, max_memories, memory_types, filePath, projectId, etc.)
    Returns:
        Dict with success status, context, project_id, and message.
    """
    try:
        query = data.get("query")
        max_memories = int(data.get("max_memories", 10))
        memory_types_raw = data.get("memory_types", [])
        project_id = data.get("projectId")

        # Try to infer project from file path
        if not project_id and data.get("filePath"):
            project_path = _infer_project_path(data.get("filePath"))
            if project_path:
                settings = ProjectSettings.load_settings(project_path)
                project_id = settings.get("project_id")
                # If isolation level is set to none, don't filter by project
                if settings.get("memory_isolation_level") == "none":
                    project_id = None

        # Parse memory types if provided
        memory_types = []
        if memory_types_raw:
            for m_type_str in memory_types_raw:
                for m_type in MemoryType:
                    if m_type.value == m_type_str.lower():
                        memory_types.append(m_type)
                        break

        # Get relevant context
        memories = await ContextSelector.select_context(
            query=query,
            max_memories=max_memories,
            memory_types=memory_types if memory_types else None,
            project_id=project_id
        )

        # Format response
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
            "message": f"Found {len(context_items)} relevant items"
        }

    except Exception as e:
        logger.error(f"Error querying context: {str(e)}")
        return {
            "success": False,
            "message": f"Error querying context: {str(e)}"
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
