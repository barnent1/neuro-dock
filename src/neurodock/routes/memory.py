from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from neurodock.models.memory import MemoryNode, MemoryCreate, MemoryEdge, MemoryEdgeCreate, MemoryType
from neurodock.neo4j.memory_repository import MemoryRepository
from neurodock.services.context_selector import ContextSelector

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("/", response_model=MemoryNode)
async def create_memory(memory: MemoryCreate):
    """
    Create a new memory node.
    """
    try:
        return await MemoryRepository.create_memory(memory)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create memory: {str(e)}")


@router.get("/{memory_id}", response_model=MemoryNode)
async def get_memory(memory_id: UUID):
    """
    Get a memory by ID.
    """
    memory = await MemoryRepository.get_memory_by_id(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail=f"Memory with ID {memory_id} not found")
    return memory


@router.post("/relationship", response_model=MemoryEdge)
async def create_memory_relationship(edge: MemoryEdgeCreate):
    """
    Create a relationship between two memory nodes.
    """
    try:
        # First check if both memory nodes exist
        from_memory = await MemoryRepository.get_memory_by_id(edge.from_id)
        to_memory = await MemoryRepository.get_memory_by_id(edge.to_id)
        
        if not from_memory:
            raise HTTPException(status_code=404, detail=f"Memory with ID {edge.from_id} not found")
        
        if not to_memory:
            raise HTTPException(status_code=404, detail=f"Memory with ID {edge.to_id} not found")
        
        # Create the memory edge
        edge_obj = MemoryEdge(
            label=edge.label,
            from_id=edge.from_id,
            to_id=edge.to_id,
            confidence=edge.confidence
        )
        
        return await MemoryRepository.create_memory_relationship(edge_obj)
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create memory relationship: {str(e)}")


@router.get("/search/{query}", response_model=List[MemoryNode])
async def search_memories(
    query: str,
    memory_type: Optional[MemoryType] = None,
    limit: int = Query(10, gt=0, le=100)
):
    """
    Search memories by content.
    """
    try:
        return await MemoryRepository.search_memories(
            query_text=query,
            memory_type=memory_type,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search memories: {str(e)}")


@router.get("/related/{memory_id}", response_model=List[MemoryNode])
async def get_related_memories(
    memory_id: UUID,
    limit: int = Query(10, gt=0, le=50),
    min_confidence: float = Query(0.5, ge=0.0, le=1.0)
):
    """
    Get memories related to a specific memory.
    """
    try:
        # First check if the memory exists
        memory = await MemoryRepository.get_memory_by_id(memory_id)
        if not memory:
            raise HTTPException(status_code=404, detail=f"Memory with ID {memory_id} not found")
        
        return await MemoryRepository.get_related_memories(
            memory_id=memory_id,
            limit=limit,
            min_confidence=min_confidence
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get related memories: {str(e)}")


@router.get("/context/{query}", response_model=List[MemoryNode])
async def get_context(
    query: str,
    max_memories: int = Query(10, gt=0, le=50),
    memory_types: Optional[List[MemoryType]] = Query(None)
):
    """
    Get relevant context for a query.
    """
    try:
        return await ContextSelector.select_context(
            query=query,
            max_memories=max_memories,
            memory_types=memory_types
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get context: {str(e)}")


# New API endpoints for the UI
@router.get("/all", response_model=List[MemoryNode])
async def get_all_memories(
    limit: int = Query(50, gt=0, le=100),
    memory_type: Optional[MemoryType] = None,
    project_id: Optional[str] = None
):
    """
    Get all memories with optional filters.
    This endpoint is primarily used by the UI.
    """
    try:
        # If no filter is provided, use an empty string to match all memories
        return await MemoryRepository.search_memories(
            query_text="",  # Empty string to match all
            memory_type=memory_type,
            project_id=project_id,
            limit=limit,
            use_fulltext=False  # Don't need fulltext for retrieving all
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve memories: {str(e)}")


@router.delete("/{memory_id}", response_model=bool)
async def delete_memory(memory_id: UUID):
    """
    Delete a memory by ID.
    """
    try:
        # First check if the memory exists
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
