from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Path

from neurodock.models.task import (
    TaskNode, TaskCreate, TaskUpdate, TaskStatus, 
    TaskPriority, TaskEvent, TaskRelationship
)
from neurodock.neo4j.task_repository import TaskRepository

router = APIRouter(prefix="/task", tags=["task"])


@router.post("/", response_model=TaskNode)
async def create_task(task: TaskCreate):
    """
    Create a new task with automatic complexity analysis and breakdown.
    Large tasks (>500 LOC or >4 hours) are automatically broken down into subtasks.
    """
    try:
        # If this is a subtask, verify the parent exists
        if task.parent_id:
            parent = await TaskRepository.get_task_by_id(task.parent_id)
            if not parent:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Parent task with ID {task.parent_id} not found"
                )
            
            # Don't analyze/breakdown subtasks - they should already be properly sized
            return await TaskRepository.create_task(task)
        
        # For new main tasks, analyze and potentially break down
        from neurodock.services.task_analyzer import TaskAnalyzer
        return await TaskAnalyzer.analyze_and_create_task(task)
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.get("/{task_id}", response_model=TaskNode)
async def get_task(task_id: UUID = Path(..., description="The ID of the task to retrieve")):
    """
    Get a task by ID.
    """
    task = await TaskRepository.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    return task


@router.put("/{task_id}", response_model=TaskNode)
async def update_task(
    task_update: TaskUpdate,
    task_id: UUID = Path(..., description="The ID of the task to update")
):
    """
    Update an existing task.
    """
    try:
        updated_task = await TaskRepository.update_task(task_id, task_update)
        if not updated_task:
            raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
        return updated_task
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")


@router.post("/relationship", response_model=TaskRelationship)
async def create_task_relationship(relationship: TaskRelationship):
    """
    Create a relationship between two tasks.
    """
    try:
        # Verify both tasks exist
        from_task = await TaskRepository.get_task_by_id(relationship.from_task_id)
        to_task = await TaskRepository.get_task_by_id(relationship.to_task_id)
        
        if not from_task:
            raise HTTPException(
                status_code=404, 
                detail=f"Task with ID {relationship.from_task_id} not found"
            )
        
        if not to_task:
            raise HTTPException(
                status_code=404, 
                detail=f"Task with ID {relationship.to_task_id} not found"
            )
        
        return await TaskRepository.create_task_relationship(relationship)
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to create task relationship: {str(e)}"
        )


@router.get("/{task_id}/events", response_model=List[TaskEvent])
async def get_task_events(
    task_id: UUID = Path(..., description="The ID of the task to get events for"),
    limit: int = Query(100, gt=0, le=1000)
):
    """
    Get events for a specific task.
    """
    try:
        # Verify the task exists
        task = await TaskRepository.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
        
        return await TaskRepository.get_task_events(task_id, limit)
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task events: {str(e)}")


@router.get("/{task_id}/subtasks", response_model=List[TaskNode])
async def get_subtasks(task_id: UUID = Path(..., description="The ID of the task to get subtasks for")):
    """
    Get all subtasks for a given task.
    """
    try:
        # Verify the task exists
        task = await TaskRepository.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
        
        return await TaskRepository.get_subtasks(task_id)
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get subtasks: {str(e)}")


@router.get("/", response_model=List[TaskNode])
async def get_pending_tasks(limit: int = Query(10, gt=0, le=100)):
    """
    Get pending tasks ordered by priority.
    """
    try:
        return await TaskRepository.get_pending_tasks(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pending tasks: {str(e)}")
