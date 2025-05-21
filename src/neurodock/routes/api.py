# --- REST Tool Schema Discovery Endpoint ---
@router.get("/tools")
async def get_rest_tools_schema():
    """
    Returns a list of all available REST API tools and their JSON schemas for discoverability (VSCode/Copilot compatibility).
    """
    # Example: This should be dynamically generated in a real system
    return {
        "tools": [
            {
                "name": "getMemories",
                "endpoint": "/api/memories",
                "method": "GET",
                "schema": "MemoryQuery",
                "description": "Get memories with optional search filter"
            },
            {
                "name": "createMemory",
                "endpoint": "/api/memories",
                "method": "POST",
                "schema": "MemoryCreate",
                "description": "Create a new memory"
            },
            {
                "name": "getMemory",
                "endpoint": "/api/memories/{memory_id}",
                "method": "GET",
                "schema": "MemoryNode",
                "description": "Get a memory by ID"
            },
            {
                "name": "deleteMemory",
                "endpoint": "/api/memories/{memory_id}",
                "method": "DELETE",
                "schema": "MemoryNode",
                "description": "Delete a memory by ID"
            }
            # Add all other REST tools here...
        ]
    }
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from neurodock.models.memory import MemoryNode, MemoryCreate, MemoryType
from neurodock.neo4j.memory_repository import MemoryRepository

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/memories", response_model=List[MemoryNode])
async def get_memories(
    query: Optional[str] = None,
    memory_type: Optional[MemoryType] = None,
    project_id: Optional[str] = None,
    limit: int = Query(50, gt=0, le=100),
):
    """
    Get memories with optional search filter.
    This endpoint is used by the UI to list and search memories.
    """
    try:
        if query:
            # If a search query is provided, use search_memories
            return await MemoryRepository.search_memories(
                query_text=query,
                memory_type=memory_type,
                project_id=project_id,
                limit=limit,
                use_fulltext=True  # Use fulltext search for better results
            )
        else:
            # Otherwise, get all memories with optional filters
            return await MemoryRepository.search_memories(
                query_text="",  # Empty string to match all
                memory_type=memory_type,
                project_id=project_id,
                limit=limit,
                use_fulltext=False
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve memories: {str(e)}")


@router.post("/memories", response_model=MemoryNode)
async def create_memory(memory: MemoryCreate):
    """
    Create a new memory.
    This endpoint is used by the UI to create memories.
    """
    try:
        return await MemoryRepository.create_memory(memory)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create memory: {str(e)}")


@router.get("/memories/{memory_id}", response_model=MemoryNode)
async def get_memory(memory_id: UUID):
    """
    Get a memory by ID.
    This endpoint is used by the UI to view a specific memory.
    """
    memory = await MemoryRepository.get_memory_by_id(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail=f"Memory with ID {memory_id} not found")
    return memory


@router.delete("/memories/{memory_id}", response_model=bool)
async def delete_memory(memory_id: UUID):
    """
    Delete a memory by ID.
    This endpoint is used by the UI to delete memories.
    """
    try:
        memory = await MemoryRepository.get_memory_by_id(memory_id)
        if not memory:
            raise HTTPException(status_code=404, detail=f"Memory with ID {memory_id} not found")
        
        success = await MemoryRepository.delete_memory(memory_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete memory")
        
        return True
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete memory: {str(e)}")
