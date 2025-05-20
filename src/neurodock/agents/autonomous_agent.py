import os
import logging
import json
from typing import List, Dict, Any, Optional
from uuid import UUID
import asyncio
import time

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from neurodock.models.task import TaskNode, TaskCreate, TaskUpdate, TaskStatus, TaskPriority
from neurodock.neo4j.task_repository import TaskRepository
from neurodock.services.context_selector import ContextSelector

# Configure logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class AgentAction(BaseModel):
    """
    Represents an action that the agent can take.
    """
    action: str = Field(..., description="The action to take")
    reason: str = Field(..., description="The reason for taking this action")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the action")


class Agent:
    """
    Autonomous agent powered by GPT-4o that can execute tasks.
    """
    
    def __init__(self):
        """Initialize the agent with default parameters."""
        self.model = os.getenv("AGENT_MODEL", "gpt-4o")
        self.max_subtasks = int(os.getenv("MAX_SUBTASKS", "5"))
        self.poll_interval = int(os.getenv("AGENT_POLL_INTERVAL", "60"))  # seconds
        self._running = False
    
    async def process_task(self, task: TaskNode) -> List[Dict[str, Any]]:
        """
        Process a single task and determine what actions to take.
        """
        # Get relevant context for this task
        context_memories = await ContextSelector.select_context(
            query=f"{task.title} {task.description}",
            max_memories=10
        )
        
        # Format the context for the agent
        context_str = "\n\n".join([
            f"Memory [{mem.type}]: {mem.content}" for mem in context_memories
        ])
        
        # Get subtasks if this is a parent task
        subtasks = await TaskRepository.get_subtasks(task.id)
        subtasks_str = ""
        if subtasks:
            subtasks_str = "Current subtasks:\n" + "\n".join([
                f"- {sub.title} (Status: {sub.status.value}, Priority: {sub.priority.value})" 
                for sub in subtasks
            ])
        
        # Construct the prompt for the model
        system_prompt = (
            "You are an autonomous agent in the NeuroDock system. "
            "Your role is to process tasks, break them down into subtasks when needed, "
            "and complete them efficiently. You have access to a knowledge graph of memories "
            "and can create/update tasks.\n\n"
            f"Available Actions:\n"
            "1. complete_task - Mark the task as completed\n"
            "2. update_status - Update the task status\n"
            "3. create_subtask - Create a smaller task that is part of this task\n"
            "4. request_more_info - Request more information to complete the task\n\n"
            "Respond with a JSON array of actions you want to take. Each action should have "
            "'action', 'reason', and 'parameters' fields."
        )
        
        user_prompt = (
            f"Task ID: {task.id}\n"
            f"Title: {task.title}\n"
            f"Description: {task.description}\n"
            f"Status: {task.status.value}\n"
            f"Priority: {task.priority.value}\n"
            f"Weight: {task.weight}\n\n"
            f"{subtasks_str}\n\n"
            "Relevant context from memory:\n"
            f"{context_str}\n\n"
            "Determine what actions to take for this task. Respond with a JSON array."
        )
        
        try:
            # Call the model to get a decision
            response = await client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Parse the response
            content = response.choices[0].message.content
            result = json.loads(content)
            
            if "actions" in result:
                return result["actions"]
            else:
                logger.warning(f"Unexpected response format from model: {content}")
                return []
                
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            return []
    
    async def execute_actions(self, task: TaskNode, actions: List[Dict[str, Any]]) -> None:
        """
        Execute a list of actions on a task.
        """
        for action_data in actions:
            action = action_data.get("action")
            reason = action_data.get("reason", "No reason provided")
            params = action_data.get("parameters", {})
            
            logger.info(f"Executing action '{action}' on task {task.id}: {reason}")
            
            try:
                if action == "complete_task":
                    # Mark the task as completed
                    await TaskRepository.update_task(
                        task.id,
                        TaskUpdate(status=TaskStatus.COMPLETED)
                    )
                    logger.info(f"Marked task {task.id} as completed")
                    
                elif action == "update_status":
                    # Update the task status
                    status_str = params.get("status")
                    if status_str and hasattr(TaskStatus, status_str.upper()):
                        status = TaskStatus[status_str.upper()]
                        await TaskRepository.update_task(
                            task.id,
                            TaskUpdate(status=status)
                        )
                        logger.info(f"Updated task {task.id} status to {status.value}")
                    else:
                        logger.warning(f"Invalid status in update_status action: {status_str}")
                
                elif action == "create_subtask":
                    # Create a subtask
                    title = params.get("title")
                    description = params.get("description", "")
                    priority_value = params.get("priority", 3)
                    
                    # Map priority value to enum
                    priority = None
                    for p in TaskPriority:
                        if p.value == priority_value:
                            priority = p
                            break
                    
                    if not priority:
                        priority = TaskPriority.MEDIUM
                    
                    # Check if we've already reached max subtasks
                    existing_subtasks = await TaskRepository.get_subtasks(task.id)
                    if len(existing_subtasks) >= self.max_subtasks:
                        logger.warning(f"Maximum number of subtasks reached for task {task.id}")
                        continue
                    
                    # Create the subtask
                    subtask = TaskCreate(
                        title=title,
                        description=description,
                        priority=priority,
                        parent_id=task.id
                    )
                    
                    await TaskRepository.create_task(subtask)
                    logger.info(f"Created subtask for task {task.id}: {title}")
                
                elif action == "request_more_info":
                    # Update task to indicate more information is needed
                    await TaskRepository.update_task(
                        task.id,
                        TaskUpdate(
                            status=TaskStatus.BLOCKED,
                            metadata={
                                "needs_info": True,
                                "info_request": params.get("request", "More information is needed")
                            }
                        )
                    )
                    logger.info(f"Requested more info for task {task.id}")
                
                else:
                    logger.warning(f"Unknown action type: {action}")
            
            except Exception as e:
                logger.error(f"Error executing action '{action}': {str(e)}")
    
    async def run_agent_loop(self):
        """
        Main loop for the agent to continuously process tasks.
        """
        self._running = True
        logger.info("Starting agent processing loop")
        
        while self._running:
            try:
                # Get top pending tasks
                pending_tasks = await TaskRepository.get_pending_tasks(limit=5)
                
                if not pending_tasks:
                    logger.info("No pending tasks found, waiting for next cycle")
                else:
                    logger.info(f"Processing {len(pending_tasks)} pending tasks")
                    
                    # Process each task
                    for task in pending_tasks:
                        # Mark task as in progress
                        await TaskRepository.update_task(
                            task.id,
                            TaskUpdate(status=TaskStatus.IN_PROGRESS)
                        )
                        
                        # Process the task
                        actions = await self.process_task(task)
                        
                        # Execute the actions
                        await self.execute_actions(task, actions)
                
                # Wait for the next polling interval
                await asyncio.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"Error in agent loop: {str(e)}")
                await asyncio.sleep(self.poll_interval)
    
    def stop(self):
        """Stop the agent loop."""
        self._running = False
        logger.info("Agent processing loop stopped")


# Singleton agent instance
agent = Agent()
