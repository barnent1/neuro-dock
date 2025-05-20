"""
Task Analyzer Service

This service provides task analysis, estimation, and automatic breakdown capabilities.
It ensures tasks remain manageable by automatically splitting large tasks into smaller subtasks.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

from neurodock.models.task import (
    TaskNode, TaskCreate, TaskComplexity, TaskType,
    TaskStatus, TaskPriority
)
from neurodock.neo4j.task_repository import TaskRepository
from neurodock.services.context_selector import ContextSelector

class TaskAnalyzer:
    """
    Analyzes tasks and breaks them down into manageable chunks.
    """
    
    # Constants for task breakdown
    MAX_LINES_PER_TASK = 500
    MAX_HOURS_PER_TASK = 4.0
    
    @staticmethod
    async def analyze_and_create_task(task_create: TaskCreate) -> TaskNode:
        """
        Analyzes a task creation request and either creates a single task
        or breaks it down into multiple subtasks if needed.
        """
        # Analyze the task description
        complexity, est_hours, est_loc = await TaskAnalyzer._estimate_task_metrics(task_create)
        
        # Create the main task
        task = TaskNode(
            title=task_create.title,
            description=task_create.description,
            priority=task_create.priority,
            complexity=complexity,
            estimated_hours=est_hours,
            estimated_loc=est_loc,
            requires_breakdown=TaskAnalyzer._needs_breakdown(est_hours, est_loc)
        )
        
        # If task needs breakdown, create subtasks
        if task.requires_breakdown:
            task = await TaskAnalyzer._break_down_task(task)
        
        # Store in database
        return await TaskRepository.create_task(task)
    
    @staticmethod
    async def _estimate_task_metrics(
        task_create: TaskCreate
    ) -> Tuple[TaskComplexity, float, Optional[int]]:
        """
        Estimates task complexity, time, and lines of code based on description.
        Uses context from similar tasks to improve estimates.
        """
        # Get context from similar completed tasks
        similar_tasks = await ContextSelector.select_context(
            query=task_create.description,
            max_memories=5,
            memory_types=["task"]
        )
        
        # Base estimates on similar tasks if available
        if similar_tasks:
            avg_hours = sum(float(t.metadata.get("actual_hours", 2.0)) for t in similar_tasks) / len(similar_tasks)
            avg_loc = sum(int(t.metadata.get("actual_loc", 200)) for t in similar_tasks) / len(similar_tasks)
        else:
            # Default estimates
            avg_hours = 2.0
            avg_loc = 200
        
        # Adjust estimates based on task description complexity
        complexity_factors = TaskAnalyzer._analyze_description_complexity(task_create.description)
        
        estimated_hours = avg_hours * complexity_factors["time_multiplier"]
        estimated_loc = int(avg_loc * complexity_factors["loc_multiplier"])
        
        # Determine complexity level
        if estimated_loc <= 50:
            complexity = TaskComplexity.TRIVIAL
        elif estimated_loc <= 200:
            complexity = TaskComplexity.SIMPLE
        elif estimated_loc <= 500:
            complexity = TaskComplexity.MODERATE
        else:
            complexity = TaskComplexity.COMPLEX
            
        return complexity, estimated_hours, estimated_loc
    
    @staticmethod
    def _analyze_description_complexity(description: str) -> Dict[str, float]:
        """
        Analyzes task description to determine complexity factors.
        """
        # Count technical terms, code snippets, and requirements
        tech_terms = len(re.findall(r'\b(api|database|async|cache|optimize|refactor|implement|integrate)\b', 
                                  description.lower()))
        code_snippets = len(re.findall(r'```.*?```', description, re.DOTALL))
        requirements = len(re.findall(r'\n[-*]\s', description))
        
        # Calculate multipliers
        base_multiplier = 1.0
        time_multiplier = base_multiplier + (tech_terms * 0.1) + (code_snippets * 0.2) + (requirements * 0.15)
        loc_multiplier = base_multiplier + (tech_terms * 0.15) + (code_snippets * 0.25) + (requirements * 0.1)
        
        return {
            "time_multiplier": time_multiplier,
            "loc_multiplier": loc_multiplier
        }
    
    @staticmethod
    def _needs_breakdown(estimated_hours: float, estimated_loc: Optional[int]) -> bool:
        """
        Determines if a task needs to be broken down based on estimates.
        """
        if estimated_hours > TaskAnalyzer.MAX_HOURS_PER_TASK:
            return True
        if estimated_loc and estimated_loc > TaskAnalyzer.MAX_LINES_PER_TASK:
            return True
        return False
    
    @staticmethod
    async def _break_down_task(task: TaskNode) -> TaskNode:
        """
        Breaks down a large task into smaller, manageable subtasks.
        Returns the updated parent task with subtask references.
        """
        # Use GPT to analyze the task and suggest breakdown
        subtask_specs = await TaskAnalyzer._generate_subtask_breakdown(task)
        
        # Create subtasks
        for spec in subtask_specs:
            subtask = TaskNode(
                title=spec["title"],
                description=spec["description"],
                priority=task.priority,
                parent_id=task.id,
                estimated_hours=spec["estimated_hours"],
                complexity=TaskComplexity.MODERATE,  # Subtasks should be moderate or simpler
                task_type=task.task_type,
                skills_required=spec.get("skills_required", [])
            )
            created_subtask = await TaskRepository.create_task(subtask)
            task.subtasks.append(created_subtask.id)
        
        return task
    
    @staticmethod
    async def _generate_subtask_breakdown(task: TaskNode) -> List[Dict[str, Any]]:
        """
        Uses AI to analyze the task and suggest a logical breakdown into subtasks.
        Each subtask should be completable within the maximum lines/hours limits.
        """
        # TODO: Implement AI-based task breakdown
        # For now, return a simple linear breakdown
        total_parts = max(
            round(task.estimated_hours / TaskAnalyzer.MAX_HOURS_PER_TASK),
            round(task.estimated_loc / TaskAnalyzer.MAX_LINES_PER_TASK)
        )
        
        subtasks = []
        hours_per_part = task.estimated_hours / total_parts
        
        for i in range(total_parts):
            subtasks.append({
                "title": f"{task.title} - Part {i + 1}",
                "description": f"Part {i + 1} of {total_parts}: {task.description}",
                "estimated_hours": hours_per_part
            })
        
        return subtasks
