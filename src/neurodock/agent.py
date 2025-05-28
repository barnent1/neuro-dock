#!/usr/bin/env python3
"""
Enhanced Agent System for NeuroDock

This module provides intelligent agent operations with automatic memory loading,
task complexity analysis, and context-aware project management.
"""

import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from .utils.models import call_llm, call_llm_plan, call_llm_code
from .db import get_store
from .memory.qdrant_store import search_memory, add_to_memory

class ProjectAgent:
    """
    Intelligent agent that automatically loads project context and provides
    enhanced task management with complexity analysis.
    """
    
    def __init__(self, project_root: str):
        """Initialize agent for a specific project."""
        self.project_root = Path(project_root)
        self.nd_path = self.project_root / ".neuro-dock"
        self.store = get_store(str(project_root))
        self.project_context = None
        
    def load_project_context(self) -> Dict[str, Any]:
        """
        Automatically load all relevant project context including:
        - Project configuration
        - Task history
        - Memory context
        - Previous discussions
        """
        if self.project_context:
            return self.project_context
            
        context = {
            "config": {},
            "tasks": [],
            "memory": [],
            "discussions": [],
            "project_info": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Load project configuration
        config_file = self.nd_path / "config.yaml"
        if config_file.exists():
            try:
                context["config"] = yaml.safe_load(config_file.read_text()) or {}
            except yaml.YAMLError:
                context["config"] = {}
        
        # Load task plan and history
        try:
            plan_data = self.store.get_task_plan()
            if plan_data:
                context["project_info"] = plan_data.get("project", {})
                context["tasks"] = plan_data.get("tasks", [])
        except Exception:
            pass
        
        # Load relevant memory context
        try:
            # Search for project-related memories
            project_name = context["project_info"].get("name", "")
            if project_name:
                memories = search_memory(f"project: {project_name}", limit=10)
                context["memory"] = memories or []
        except Exception:
            pass
            
        # Load recent discussions
        try:
            discussions = self.store.get_memory_by_type("clarified_prompt")
            context["discussions"] = discussions[:5] if discussions else []
        except Exception:
            pass
            
        self.project_context = context
        return context
    
    def analyze_task_complexity(self, task_description: str) -> Dict[str, Any]:
        """
        Analyze task complexity and provide breakdown recommendations.
        
        Returns:
            Dict containing complexity rating, estimated time, and breakdown suggestions
        """
        context = self.load_project_context()
        
        analysis_prompt = f"""
Analyze the complexity of this task and provide a structured assessment:

PROJECT CONTEXT:
- Name: {context['project_info'].get('name', 'Unknown')}
- Description: {context['project_info'].get('description', 'No description')}
- Framework: {context['config'].get('framework', 'auto')}
- Existing Tasks: {len(context['tasks'])} tasks in project

TASK TO ANALYZE:
{task_description}

PREVIOUS CONTEXT:
{self._format_memory_context(context['memory'][:3])}

Please provide a JSON response with the following structure:
{{
    "complexity_rating": 1-10 (1=simple, 10=extremely complex),
    "estimated_hours": number,
    "complexity_factors": ["factor1", "factor2", ...],
    "should_break_down": true/false,
    "suggested_subtasks": [
        {{"name": "subtask name", "description": "detailed description", "complexity": 1-5}},
        ...
    ],
    "dependencies": ["list of dependencies or prerequisites"],
    "risks": ["potential risks or challenges"]
}}

Focus on practical breakdowns that make the task more manageable.
"""
        
        try:
            response = call_llm(analysis_prompt)
            
            # Try to parse JSON response
            try:
                analysis = json.loads(response)
            except json.JSONDecodeError:
                # Fallback: extract key information from text response
                analysis = self._parse_complexity_from_text(response, task_description)
            
            # Store analysis in memory
            add_to_memory(
                f"Task complexity analysis: {task_description}\nResult: {json.dumps(analysis, indent=2)}",
                {
                    "type": "complexity_analysis",
                    "project_path": str(self.project_root),
                    "complexity_rating": analysis.get("complexity_rating", 5)
                }
            )
            
            return analysis
            
        except Exception as e:
            # Fallback analysis
            return {
                "complexity_rating": 5,
                "estimated_hours": 2,
                "complexity_factors": ["unknown_complexity"],
                "should_break_down": False,
                "suggested_subtasks": [],
                "dependencies": [],
                "risks": ["Unable to analyze complexity due to error"],
                "error": str(e)
            }
    
    def enhance_task_with_context(self, task_description: str) -> str:
        """
        Enhance a task description with full project context for better LLM understanding.
        """
        context = self.load_project_context()
        
        enhanced_prompt = f"""
PROJECT CONTEXT:
=================
Name: {context['project_info'].get('name', 'Unknown Project')}
Description: {context['project_info'].get('description', 'No description available')}
Framework/Type: {context['config'].get('framework', 'auto')}
Project Root: {context['config'].get('app_root', '.')}

EXISTING TASKS STATUS:
=====================
{self._format_tasks_status(context['tasks'])}

RELEVANT MEMORY CONTEXT:
========================
{self._format_memory_context(context['memory'][:5])}

CURRENT TASK:
=============
{task_description}

INSTRUCTIONS:
=============
Based on the full project context above, please execute the current task.
Consider the existing codebase, completed tasks, and project structure.
Ensure consistency with the established patterns and architecture.
"""
        
        return enhanced_prompt
    
    def get_project_summary(self) -> Dict[str, Any]:
        """Get a comprehensive project summary for status reporting."""
        context = self.load_project_context()
        
        # Calculate task statistics
        tasks = context['tasks']
        completed = len([t for t in tasks if t.get('status') == 'completed'])
        in_progress = len([t for t in tasks if t.get('status') == 'in_progress'])
        pending = len([t for t in tasks if t.get('status') in ['pending', None]])
        
        return {
            "project_info": context['project_info'],
            "config": context['config'],
            "task_stats": {
                "total": len(tasks),
                "completed": completed,
                "in_progress": in_progress,
                "pending": pending,
                "completion_rate": (completed / len(tasks) * 100) if tasks else 0
            },
            "memory_entries": len(context['memory']),
            "last_updated": context['timestamp']
        }
    
    def get_context_summary(self) -> str:
        """Get a formatted string summary of the project context."""
        summary = self.get_project_summary()
        
        lines = [
            f"Project: {summary['project_info'].get('name', 'NeuroDock Project')}",
            f"Tasks: {summary['task_stats']['total']} total ({summary['task_stats']['completed']} completed)",
            f"Memory: {summary['memory_entries']} entries",
            f"Progress: {summary['task_stats']['completion_rate']:.1f}%"
        ]
        
        if summary['task_stats']['total'] > 0:
            lines.extend([
                f"- Completed: {summary['task_stats']['completed']}",
                f"- In Progress: {summary['task_stats']['in_progress']}",
                f"- Pending: {summary['task_stats']['pending']}"
            ])
        
        # Add recent context from project memory
        context = self.load_project_context()
        if context.get('memory'):
            lines.append(f"Recent Memory: {len(context['memory'][:3])} latest entries available")
        
        return "\n".join(lines)
    
    def _format_tasks_status(self, tasks: List[Dict[str, Any]]) -> str:
        """Format task list for context display."""
        if not tasks:
            return "No tasks defined yet"
        
        formatted = []
        for i, task in enumerate(tasks, 1):
            status = task.get('status', 'pending')
            name = task.get('name', f'Task {i}')
            status_emoji = {
                'completed': '✅',
                'in_progress': '🔄',
                'pending': '⏳'
            }.get(status, '⏳')
            
            formatted.append(f"{status_emoji} {name} ({status})")
        
        return "\n".join(formatted)
    
    def _format_memory_context(self, memories: List[Dict[str, Any]]) -> str:
        """Format memory entries for context display."""
        if not memories:
            return "No relevant memory context found"
        
        formatted = []
        for memory in memories:
            # Handle both string and dict memory entries
            if isinstance(memory, str):
                text = memory[:200]
                mem_type = "memory"
            else:
                text = memory.get('text', memory.get('content', 'No content'))[:200]
                metadata = memory.get('metadata', {})
                mem_type = metadata.get('type', 'unknown')
            formatted.append(f"[{mem_type}] {text}...")
        
        return "\n".join(formatted)
    
    def _parse_complexity_from_text(self, response: str, task_description: str) -> Dict[str, Any]:
        """Fallback parser for complexity analysis when JSON parsing fails."""
        # Simple heuristic-based complexity assessment
        complexity = 5  # default medium complexity
        
        # Simple keyword-based complexity scoring
        high_complexity_keywords = [
            'database', 'authentication', 'api', 'integration', 'deployment',
            'complex', 'advanced', 'multiple', 'system', 'architecture'
        ]
        
        low_complexity_keywords = [
            'simple', 'basic', 'single', 'quick', 'small', 'minor',
            'update', 'fix', 'style', 'text', 'color'
        ]
        
        task_lower = task_description.lower()
        
        high_matches = sum(1 for keyword in high_complexity_keywords if keyword in task_lower)
        low_matches = sum(1 for keyword in low_complexity_keywords if keyword in task_lower)
        
        if high_matches > low_matches:
            complexity = min(8, 5 + high_matches)
        elif low_matches > high_matches:
            complexity = max(2, 5 - low_matches)
        
        return {
            "complexity_rating": complexity,
            "estimated_hours": complexity * 0.5,
            "complexity_factors": ["heuristic_analysis"],
            "should_break_down": complexity > 6,
            "suggested_subtasks": [],
            "dependencies": [],
            "risks": ["Analysis based on heuristics due to parsing error"],
            "raw_response": response
        }

def get_project_agent(project_root: str = None) -> ProjectAgent:
    """Get a project agent instance for the specified or current directory."""
    if project_root is None:
        project_root = str(Path.cwd())
    return ProjectAgent(project_root)
