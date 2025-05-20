from typing import Dict, List, Any, Optional
from uuid import UUID
import logging
import json
import os
import pathlib

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status

from neurodock.models.memory import MemoryCreate, MemoryType
from neurodock.neo4j.memory_repository import MemoryRepository
from neurodock.models.task import TaskCreate, TaskPriority
from neurodock.neo4j.task_repository import TaskRepository
from neurodock.services.context_selector import ContextSelector
from neurodock.services.project_settings import ProjectSettings

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["mcp"])


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
    Return the MCP server configuration.
    This helps VSCode understand the capabilities of this MCP server.
    """
    return {
        "version": "1.0",
        "name": "NeuroDock MCP Server",
        "capabilities": {
            "memory": True,
            "tasks": True,
            "context": True,
            "websocket": True
        },
        "endpoints": {
            "memory": "/mcp/memory",
            "task": "/mcp/task",
            "context": "/mcp/context",
            "websocket": "/mcp/ws"
        },
        "memoryTypes": [type.value for type in MemoryType],
        "taskPriorities": [priority.value for priority in TaskPriority]
    }


@router.post("/memory")
async def store_memory(data: Dict[str, Any]):
    """
    Store a memory via the Model Context Protocol.
    """
    result = await ModelContextProtocolService.handle_memory_store(data)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message"))
    return result


@router.post("/task")
async def create_task(data: Dict[str, Any]):
    """
    Create a task via the Model Context Protocol.
    """
    result = await ModelContextProtocolService.handle_task_create(data)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message"))
    return result


@router.post("/context")
async def query_context(data: Dict[str, Any]):
    """
    Query for relevant context via the Model Context Protocol.
    """
    result = await ModelContextProtocolService.handle_context_query(data)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message"))
    return result


@router.post("/editor-context")
async def get_editor_context(data: Dict[str, Any]):
    """
    Get relevant context specifically for VSCode editor integration.
    """
    try:
        code_snippet = data.get("code", "")
        file_path = data.get("filePath")
        max_memories = int(data.get("maxMemories", 10))
        project_id = data.get("projectId")
        
        # If no explicit project ID, try to infer from file path
        if not project_id and file_path:
            project_path = ModelContextProtocolService._infer_project_path(file_path)
            if project_path:
                settings = ProjectSettings.load_settings(project_path)
                project_id = settings.get("project_id")
                
                # If isolation level is set to none, don't filter by project
                if settings.get("memory_isolation_level") == "none":
                    project_id = None
        
        # Use the specialized context selector for editor
        memories = await ContextSelector.select_context_for_editor(
            code_snippet=code_snippet,
            file_path=file_path,
            project_id=project_id,  # Pass project ID
            max_memories=max_memories
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
                "project_id": memory.project_id,
                "relevance": "high" if memory.type in [MemoryType.CODE, MemoryType.DOCUMENTATION] else "medium"
            })
        
        return {
            "success": True,
            "context": context_items,
            "project_id": project_id,
            "message": f"Found {len(context_items)} relevant items for editor context"
        }
        
    except Exception as e:
        logger.error(f"Error getting editor context: {str(e)}")
        return {
            "success": False,
            "message": f"Error getting editor context: {str(e)}"
        }


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for the Model Context Protocol.
    Allows bidirectional communication for MCP clients.
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive and parse the message
            data_text = await websocket.receive_text()
            data = json.loads(data_text)
            
            # Extract the command and payload
            command = data.get("command")
            payload = data.get("payload", {})
            request_id = data.get("requestId", "unknown")
            
            # Process the command
            response = {"requestId": request_id}
            
            if command == "store_memory":
                result = await ModelContextProtocolService.handle_memory_store(payload)
                response.update(result)
                
            elif command == "create_task":
                result = await ModelContextProtocolService.handle_task_create(payload)
                response.update(result)
                
            elif command == "query_context":
                result = await ModelContextProtocolService.handle_context_query(payload)
                response.update(result)
                
            else:
                response.update({
                    "success": False,
                    "message": f"Unknown command: {command}"
                })
            
            # Send the response
            await websocket.send_json(response)
            
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {str(e)}")
        if websocket.client_state != websocket.client_state.DISCONNECTED:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
