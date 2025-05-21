"""
MCP Project/Task Management Tool Handlers
Implements add_task and related project/task management endpoints for MCP.
Robust error handling and clear comments for maintainability.
"""

import logging
from neurodock.models.task import TaskCreate
from neurodock.services.task_analyzer import TaskAnalyzer

logger = logging.getLogger(__name__)

async def handle_add_task(data):
    """
    Handler for adding a new task via MCP.
    Analyzes and creates the task, breaking it down if needed.
    Args:
        data (dict): Task creation data (title, description, priority, etc.)
    Returns:
        dict: Success status, task ID, and message.
    """
    try:
        # Validate and parse input using TaskCreate
        task_create = TaskCreate(**data)
        # Use TaskAnalyzer to analyze and create (with breakdown if needed)
        task = await TaskAnalyzer.analyze_and_create_task(task_create)
        return {
            "success": True,
            "task_id": str(task.id),
            "message": "Task created successfully"
        }
    except Exception as e:
        logger.error(f"Error adding task: {e}")
        return {
            "success": False,
            "message": f"Error adding task: {e}"
        }
