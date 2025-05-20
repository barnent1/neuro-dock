"""
Project management routes for the NeuroDock dashboard.
"""
import os
import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException


from neurodock.neo4j.memory_repository import MemoryRepository
from neurodock.neo4j.task_repository import TaskRepository
from neurodock.services.project_settings import ProjectSettings

router = APIRouter(prefix="/projects", tags=["projects"])


async def load_project_settings(project_dir: str) -> dict:
    """Load project settings from neurodock.json"""
    try:
        with open(os.path.join(project_dir, "neurodock.json")) as f:
            return json.load(f)
    except FileNotFoundError:
        return None


@router.get("")
async def get_projects():
    """
    Get list of available projects.
    First checks for neurodock.json in current directory,
    then looks for other projects in workspace.
    """
    projects = []
    
    # Check current directory for neurodock.json
    current_project = await load_project_settings(".")
    if current_project:
        current_project["is_default"] = True
        projects.append(current_project)
    
    # Look for other projects in workspace
    # TODO: Implement workspace project discovery
    
    return projects



# Always use the project_id from neurodock.json, ignore the URL parameter
def get_current_project_id():
    settings = ProjectSettings.load_settings(os.getcwd())
    return settings.get("project_id", "neurodock")

@router.post("/{project_id}/clearMemories")
async def clear_project_memories(project_id: str):
    """Clear all memories for the current project (ignores URL param)"""
    try:
        real_project_id = get_current_project_id()
        await MemoryRepository.delete_project_memories(real_project_id)
        return {"success": True, "message": f"All memories cleared for project {real_project_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/{project_id}/clearTasks")
async def clear_project_tasks(project_id: str):
    """Clear all tasks for the current project (ignores URL param)"""
    try:
        real_project_id = get_current_project_id()
        await TaskRepository.delete_project_tasks(real_project_id)
        return {"success": True, "message": f"All tasks cleared for project {real_project_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/{project_id}/clearAll")
async def clear_project_data(project_id: str):
    """Clear all data for the current project (ignores URL param)"""
    try:
        real_project_id = get_current_project_id()
        await MemoryRepository.delete_project_memories(real_project_id)
        await TaskRepository.delete_project_tasks(real_project_id)
        return {"success": True, "message": f"All project data cleared for project {real_project_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
