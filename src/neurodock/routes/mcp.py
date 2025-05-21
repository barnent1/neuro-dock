from fastapi import APIRouter, HTTPException, WebSocket
from typing import Dict, List, Any, Optional
from uuid import UUID
import logging
import json
import os
import pathlib
from neurodock.models.memory import MemoryType, MemoryCreate
from neurodock.neo4j.memory_repository import MemoryRepository

# FastAPI router for MCP endpoints (must be defined before use)
router = APIRouter(prefix="/neuro-dock", tags=["mcp"])

# --- MCP Tool Schema Discovery Endpoint ---
@router.get("/tools")
async def get_mcp_tools_schema():
    """
    Returns a list of all available MCP tools and their JSON schemas for discoverability (VSCode/Copilot compatibility).
    """
    # Example: This should be dynamically generated in a real system
    return {
        "tools": [
            {
                "name": "addMemory",
                "endpoint": "/neuro-dock/memory",
                "method": "POST",
                "schema": "MemoryCreate",
                "description": "Store a new memory"
            },
            {
                "name": "addTask",
                "endpoint": "/neuro-dock/task",
                "method": "POST",
                "schema": "TaskCreate",
                "description": "Create a new task"
            },
            {
                "name": "addEpisode",
                "endpoint": "/neuro-dock/memory/episode",
                "method": "POST",
                "schema": "MemoryCreate",
                "description": "Add an episodic/entity/fact memory"
            },
            {
                "name": "searchNodes",
                "endpoint": "/neuro-dock/memory/search-nodes",
                "method": "POST",
                "schema": "SearchNodesRequest",
                "description": "Search nodes (memories/entities/facts)"
            }
            # Add all other tools here...
        ]
    }
from neurodock.mcp_tools.memory_advanced_tool import handle_add_episode, handle_search_nodes
# --- MCP Advanced Memory Tool Endpoint: Search Nodes ---
@router.post("/memory/search-nodes")
async def search_nodes(data: Dict[str, Any]):
    """
    Search nodes (memories/entities/facts) via the Model Context Protocol (MCP).
    Uses the modular handler from mcp_tools.memory_advanced_tool.
    """
    result = await handle_search_nodes(data)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message"))
    return result

# Imports for FastAPI and typing
from typing import Dict, List, Any, Optional
from uuid import UUID
import logging
import json
import os
import pathlib
from fastapi import APIRouter, HTTPException, WebSocket

from neurodock.mcp_tools.memory_tool import handle_memory_store
from neurodock.mcp_tools.memory_advanced_tool import handle_add_episode
# --- MCP Advanced Memory Tool Endpoint ---
@router.post("/memory/episode")
async def add_episode(data: Dict[str, Any]):
    """
    Add an episode (memory) via the Model Context Protocol (MCP).
    Uses the modular handler from mcp_tools.memory_advanced_tool.
    """
    result = await handle_add_episode(data)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message"))
    return result
from neurodock.mcp_tools.project_task_tool import handle_add_task
from neurodock.mcp_tools.context_tool import handle_context_query

from neurodock.models.memory import MemoryType
from neurodock.models.task import TaskPriority
from neurodock.mcp_tools.editor_context_tool import handle_editor_context

# Configure logging
logger = logging.getLogger(__name__)

# FastAPI router for MCP endpoints
router = APIRouter(prefix="/neuro-dock", tags=["mcp"])
 
# ... (rest of your code, including router definition and all imports) ...

# Add a root GET /neuro-dock endpoint for MCP tool discovery (VS Code compatibility)
@router.get("")
@router.get("/")
async def get_mcp_root():
    """
    Root endpoint for MCP tool discovery. Returns the same info as /config for VS Code compatibility.
    """
    return await get_mcp_config()
from neurodock.models.task import TaskCreate, TaskPriority
from neurodock.neo4j.task_repository import TaskRepository
from neurodock.services.context_selector import ContextSelector
from neurodock.services.project_settings import ProjectSettings

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/neuro-dock", tags=["mcp"])


class ModelContextProtocolService:
    """
    Implementation of Model Context Protocol (MCP) for integration with VSCode and other clients.
    """
    
    @staticmethod
    async def handle_memory_store(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle storing memory via MCP.
        """
        try:
            content = data.get("content")
            memory_type_str = data.get("type", "normal").lower()
            source = data.get("source", "vscode")
            file_path = data.get("filePath")
            
            # Determine project context
            project_id = data.get("projectId")
            project_path = data.get("projectPath")
            
            # If no explicit project ID was provided but we have a file path,
            # try to determine the project from the file path
            if not project_id and file_path:
                project_path = ModelContextProtocolService._infer_project_path(file_path)
                if project_path:
                    settings = ProjectSettings.load_settings(project_path)
                    project_id = settings.get("project_id")
            
            # Map the string to MemoryType
            memory_type = MemoryType.NORMAL  # default
            for m_type in MemoryType:
                if m_type.value == memory_type_str:
                    memory_type = m_type
                    break
            
            memory_create = MemoryCreate(
                content=content,
                type=memory_type,
                source=source,
                project_id=project_id
            )
            
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
    
    @staticmethod
    def _infer_project_path(file_path: str) -> Optional[str]:
        """
        Try to infer the project path from a file path by looking for neurodock.json.
        
        Args:
            file_path: Path to a file
            
        Returns:
            Project path if found, None otherwise
        """
        if not file_path:
            return None
        
        try:
            # Convert to absolute path and handle pathlib.Path functionality
            file_path = os.path.abspath(file_path)
            path = pathlib.Path(file_path)
            
            # Start from the file's directory and work upward
            current_dir = path.parent
            
            # Go up to 10 levels to find neurodock.json
            for _ in range(10):
                config_path = current_dir / "neurodock.json"
                if config_path.exists():
                    return str(current_dir)
                
                # Stop if we reached the filesystem root
                if current_dir == current_dir.parent:
                    break
                    
                # Go up one directory
                current_dir = current_dir.parent
                
            return None
            
        except Exception as e:
            logger.error(f"Error inferring project path: {str(e)}")
            return None
    
    @staticmethod
    async def handle_task_create(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle task creation via MCP.
        """
        try:
            title = data.get("title")
            description = data.get("description", "")
            priority_value = data.get("priority", 3)
            parent_id_str = data.get("parent_id")
            project_id = data.get("projectId")
            
            # If a file path is provided, try to infer the project
            if not project_id and data.get("filePath"):
                project_path = ModelContextProtocolService._infer_project_path(data.get("filePath"))
                if project_path:
                    settings = ProjectSettings.load_settings(project_path)
                    project_id = settings.get("project_id")
            
            # Parse priority
            priority = TaskPriority.MEDIUM  # default
            for p in TaskPriority:
                if p.value == int(priority_value):
                    priority = p
                    break
            
            # Parse parent ID if provided
            parent_id = UUID(parent_id_str) if parent_id_str else None
            
            task_create = TaskCreate(
                title=title,
                description=description,
                priority=priority,
                parent_id=parent_id,
                metadata={"project_id": project_id} if project_id else {}
            )
            
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
    
    @staticmethod
    async def handle_context_query(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle context query via MCP.
        """
        try:
            query = data.get("query")
            max_memories = int(data.get("max_memories", 10))
            memory_types_raw = data.get("memory_types", [])
            project_id = data.get("projectId")
            
            # Try to infer project from file path
            if not project_id and data.get("filePath"):
                project_path = ModelContextProtocolService._infer_project_path(data.get("filePath"))
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
                project_id=project_id  # Pass the project ID to filter memories
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


@router.get("/config")
async def get_mcp_config():
    """
    Return the MCP server configuration and explicit tool operations for VSCode MCP.
    """
    return {
        "version": "1.0",
        "name": "NeuroDock MCP Server",
        "description": "Production-grade MCP server for NeuroDock",
        "tools": [
            {
                "name": "addMemory",
                "endpoint": "/neuro-dock/memory",
                "method": "POST",
                "description": "Store a new memory"
            },
            {
                "name": "addTask",
                "endpoint": "/neuro-dock/task",
                "method": "POST",
                "description": "Create a new task"
            },
            {
                "name": "queryContext",
                "endpoint": "/neuro-dock/context",
                "method": "POST",
                "description": "Query for relevant context/memories"
            },
            {
                "name": "editorContext",
                "endpoint": "/neuro-dock/editor-context",
                "method": "POST",
                "description": "Get context for the editor"
            },
            {
                "name": "websocket",
                "endpoint": "/neuro-dock/ws",
                "method": "WEBSOCKET",
                "description": "Bidirectional MCP communication"
            }
        ],
        "memoryTypes": [type.value for type in MemoryType],
        "taskPriorities": [priority.value for priority in TaskPriority]
    }



# --- MCP Memory Tool Endpoint ---
@router.post("/memory")
async def store_memory(data: Dict[str, Any]):
    """
    Store a memory via the Model Context Protocol (MCP).
    Uses the modular handler from mcp_tools.memory_tool.
    """
    result = await handle_memory_store(data)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message"))
    return result




# --- MCP Project/Task Management Tool Endpoint ---
@router.post("/task")
async def add_task(data: Dict[str, Any]):
    """
    Add a new task via the Model Context Protocol (MCP).
    Uses the modular handler from mcp_tools.project_task_tool.
    """
    result = await handle_add_task(data)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message"))
    return result



# --- MCP Context Tool Endpoint ---
@router.post("/context")
async def query_context(data: Dict[str, Any]):
    """
    Query for relevant context via the Model Context Protocol (MCP).
    Uses the modular handler from mcp_tools.context_tool.
    """
    result = await handle_context_query(data)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message"))
    return result



@router.post("/editor-context")
async def get_editor_context(data: Dict[str, Any]):
    """
    Get relevant context specifically for VSCode editor integration.
    Uses the modular handler from mcp_tools.editor_context_tool.
    """
    result = await handle_editor_context(data)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message"))
    return result


from neurodock.mcp_tools.websocket_tool import handle_websocket

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for the Model Context Protocol.
    Uses the modular handler from mcp_tools.websocket_tool.
    """
    await handle_websocket(websocket)
