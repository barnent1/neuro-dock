#!/usr/bin/env python3
"""
Agent Memory Reminder System for NeuroDock

This module provides contextual reminders from Agent 2 (Memory Agent) to Agent 1
after command completion, helping maintain focus and context awareness throughout
the development workflow.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .qdrant_store import search_memory, add_to_memory
from .neo4j_store import get_neo4j_store, get_agent_reminders as get_neo4j_reminders

@dataclass
class AgentReminder:
    """Represents a contextual reminder from Agent 2 to Agent 1."""
    message: str
    priority: str  # "high", "medium", "low"
    category: str  # "task", "memory", "context", "warning"
    metadata: Dict[str, Any]

class MemoryReminderSystem:
    """
    System for generating contextual reminders from Agent 2 to Agent 1.
    
    This helps keep Agent 1 focused and aware of important context by providing
    intelligent reminders after command completion.
    """
    
    def __init__(self, project_root: str):
        """Initialize the reminder system for a project."""
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(__name__)
        
    def generate_post_command_reminders(self, command: str, command_result: str, 
                                      context: Optional[Dict[str, Any]] = None) -> List[AgentReminder]:
        """
        Generate contextual reminders after a command completion.
        
        Args:
            command: The command that was executed
            command_result: Result/output of the command
            context: Additional context from the command execution
            
        Returns:
            List of AgentReminder objects
        """
        reminders = []
        context = context or {}
        
        # Command-specific reminders
        if command == "discuss":
            reminders.extend(self._generate_discuss_reminders(command_result, context))
        elif command == "plan":
            reminders.extend(self._generate_plan_reminders(command_result, context))
        elif command == "run":
            reminders.extend(self._generate_run_reminders(command_result, context))
        elif command == "analyze":
            reminders.extend(self._generate_analyze_reminders(command_result, context))
        elif command == "status":
            reminders.extend(self._generate_status_reminders(command_result, context))
            
        # General memory-based reminders
        reminders.extend(self._generate_memory_reminders())
        
        # Neo4J graph-based reminders
        reminders.extend(self._generate_graph_reminders())
        
        # Priority and context reminders
        reminders.extend(self._generate_priority_reminders(context))
        
        return self._filter_and_prioritize_reminders(reminders)
    
    def _generate_discuss_reminders(self, result: str, context: Dict[str, Any]) -> List[AgentReminder]:
        """Generate reminders after discuss command."""
        reminders = []
        
        # Check if requirements are fully clarified
        if "unclear" in result.lower() or "more information" in result.lower():
            reminders.append(AgentReminder(
                message="🤔 Requirements may need further clarification before planning",
                priority="high",
                category="context",
                metadata={"command": "discuss", "needs_clarification": True}
            ))
            
        # Suggest next steps
        if "plan" not in result.lower():
            reminders.append(AgentReminder(
                message="📋 Next step: Run 'nd plan' to break down requirements into tasks",
                priority="medium",
                category="task",
                metadata={"command": "discuss", "suggested_next": "plan"}
            ))
            
        # Check for complexity indicators
        if any(word in result.lower() for word in ["complex", "challenging", "difficult", "multiple"]):
            reminders.append(AgentReminder(
                message="⚠️ Complex requirements detected - consider using 'nd analyze' for task breakdown",
                priority="medium",
                category="warning",
                metadata={"command": "discuss", "complexity_detected": True}
            ))
            
        return reminders
    
    def _generate_plan_reminders(self, result: str, context: Dict[str, Any]) -> List[AgentReminder]:
        """Generate reminders after plan command."""
        reminders = []
        
        # Count tasks if available
        task_count = context.get("task_count", 0)
        if task_count > 10:
            reminders.append(AgentReminder(
                message=f"📊 Large plan detected ({task_count} tasks) - consider breaking into smaller sprints",
                priority="medium",
                category="context",
                metadata={"command": "plan", "task_count": task_count}
            ))
        elif task_count > 0:
            reminders.append(AgentReminder(
                message=f"✅ Plan created with {task_count} tasks - ready for execution with 'nd run'",
                priority="low",
                category="task",
                metadata={"command": "plan", "task_count": task_count}
            ))
            
        # Check for high complexity tasks
        if context.get("high_complexity_tasks", 0) > 0:
            reminders.append(AgentReminder(
                message="🔍 High complexity tasks detected - review with 'nd analyze --interactive'",
                priority="high",
                category="warning",
                metadata={"command": "plan", "complex_tasks": True}
            ))
            
        # Dependency reminders
        if context.get("dependencies_detected", False):
            reminders.append(AgentReminder(
                message="🔗 Task dependencies detected - ensure proper execution order",
                priority="medium",
                category="context",
                metadata={"command": "plan", "dependencies": True}
            ))
            
        return reminders
    
    def _generate_run_reminders(self, result: str, context: Dict[str, Any]) -> List[AgentReminder]:
        """Generate reminders after run command."""
        reminders = []
        
        completed_tasks = context.get("completed_tasks", 0)
        failed_tasks = context.get("failed_tasks", 0)
        remaining_tasks = context.get("remaining_tasks", 0)
        
        # Success reminders
        if completed_tasks > 0:
            reminders.append(AgentReminder(
                message=f"🎉 Progress made: {completed_tasks} task(s) completed successfully",
                priority="low",
                category="task",
                metadata={"command": "run", "completed": completed_tasks}
            ))
            
        # Failure reminders
        if failed_tasks > 0:
            reminders.append(AgentReminder(
                message=f"⚠️ {failed_tasks} task(s) failed - review errors and consider breaking down complex tasks",
                priority="high",
                category="warning",
                metadata={"command": "run", "failed": failed_tasks}
            ))
            
        # Progress reminders
        if remaining_tasks > 0:
            reminders.append(AgentReminder(
                message=f"📋 {remaining_tasks} task(s) remaining - use 'nd run' to continue or 'nd status' to review",
                priority="medium",
                category="task",
                metadata={"command": "run", "remaining": remaining_tasks}
            ))
        elif completed_tasks > 0 and remaining_tasks == 0:
            reminders.append(AgentReminder(
                message="🏆 All tasks completed! Consider running 'nd status' for final review",
                priority="low",
                category="task",
                metadata={"command": "run", "project_complete": True}
            ))
            
        return reminders
    
    def _generate_analyze_reminders(self, result: str, context: Dict[str, Any]) -> List[AgentReminder]:
        """Generate reminders after analyze command."""
        reminders = []
        
        complexity_rating = context.get("complexity_rating", 0)
        should_break_down = context.get("should_break_down", False)
        
        if complexity_rating > 7:
            reminders.append(AgentReminder(
                message=f"🔥 High complexity detected (rating: {complexity_rating}) - strongly consider task breakdown",
                priority="high",
                category="warning",
                metadata={"command": "analyze", "complexity": complexity_rating}
            ))
        elif should_break_down:
            reminders.append(AgentReminder(
                message="📝 Task breakdown recommended - use suggested subtasks for better success rate",
                priority="medium",
                category="context",
                metadata={"command": "analyze", "breakdown_suggested": True}
            ))
            
        # Dependency warnings
        dependencies = context.get("dependencies", [])
        if dependencies:
            reminders.append(AgentReminder(
                message=f"⚡ Dependencies identified: {', '.join(dependencies[:3])} - ensure prerequisites are met",
                priority="medium",
                category="context",
                metadata={"command": "analyze", "dependencies": dependencies}
            ))
            
        return reminders
    
    def _generate_status_reminders(self, result: str, context: Dict[str, Any]) -> List[AgentReminder]:
        """Generate reminders after status command."""
        reminders = []
        
        completion_rate = context.get("completion_rate", 0)
        in_progress_tasks = context.get("in_progress_tasks", 0)
        
        # Progress-based reminders
        if completion_rate < 25:
            reminders.append(AgentReminder(
                message="🚀 Project just started - focus on completing initial setup tasks first",
                priority="medium",
                category="context",
                metadata={"command": "status", "completion_rate": completion_rate}
            ))
        elif completion_rate > 75:
            reminders.append(AgentReminder(
                message="🎯 Project nearing completion - review remaining tasks for final push",
                priority="medium",
                category="context",
                metadata={"command": "status", "completion_rate": completion_rate}
            ))
            
        # In-progress task reminders
        if in_progress_tasks > 3:
            reminders.append(AgentReminder(
                message=f"⚠️ Many tasks in progress ({in_progress_tasks}) - consider focusing on completion",
                priority="medium",
                category="warning",
                metadata={"command": "status", "in_progress": in_progress_tasks}
            ))
            
        return reminders
    
    def _generate_memory_reminders(self) -> List[AgentReminder]:
        """Generate reminders based on vector memory context."""
        reminders = []
        
        try:
            # Search for recent important memories
            recent_warnings = search_memory("warning error failed", limit=3)
            if recent_warnings:
                reminders.append(AgentReminder(
                    message=f"⚠️ Recent issues detected in memory - review {len(recent_warnings)} warning(s)",
                    priority="medium",
                    category="memory",
                    metadata={"memory_type": "warnings", "count": len(recent_warnings)}
                ))
                
            # Search for incomplete items
            incomplete_items = search_memory("TODO incomplete pending", limit=3)
            if incomplete_items:
                reminders.append(AgentReminder(
                    message=f"📝 {len(incomplete_items)} incomplete item(s) in memory - consider prioritizing",
                    priority="low",
                    category="memory",
                    metadata={"memory_type": "incomplete", "count": len(incomplete_items)}
                ))
                
            # Search for complex tasks
            complex_tasks = search_memory("complex difficult challenging", limit=2)
            if complex_tasks:
                reminders.append(AgentReminder(
                    message="🔍 Complex tasks in memory - ensure proper analysis and breakdown",
                    priority="medium",
                    category="memory",
                    metadata={"memory_type": "complex", "count": len(complex_tasks)}
                ))
                
        except Exception as e:
            self.logger.debug(f"Memory search failed for reminders: {e}")
            
        return reminders
    
    def _generate_graph_reminders(self) -> List[AgentReminder]:
        """Generate reminders based on Neo4J graph memory."""
        reminders = []
        
        try:
            # Get Neo4J-based reminders
            neo4j_reminders = get_neo4j_reminders("agent1")
            for reminder_text in neo4j_reminders[:3]:  # Limit to 3 most important
                reminders.append(AgentReminder(
                    message=reminder_text,
                    priority="medium",
                    category="memory",
                    metadata={"source": "neo4j_graph"}
                ))
                
        except Exception as e:
            self.logger.debug(f"Neo4J reminder generation failed: {e}")
            
        return reminders
    
    def _generate_priority_reminders(self, context: Dict[str, Any]) -> List[AgentReminder]:
        """Generate priority-based reminders."""
        reminders = []
        
        # Time-based reminders
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 17:  # Work hours
            reminders.append(AgentReminder(
                message="💼 Work hours detected - focus on high-priority tasks for maximum productivity",
                priority="low",
                category="context",
                metadata={"time_context": "work_hours"}
            ))
            
        # Database connectivity reminder
        if not context.get("database_connected", True):
            reminders.append(AgentReminder(
                message="🗄️ Database connection issue - run 'nd setup' to restore full functionality",
                priority="high",
                category="warning",
                metadata={"database_issue": True}
            ))
            
        return reminders
    
    def _filter_and_prioritize_reminders(self, reminders: List[AgentReminder]) -> List[AgentReminder]:
        """Filter and prioritize reminders to avoid overwhelming the user."""
        # Remove duplicates
        seen_messages = set()
        unique_reminders = []
        for reminder in reminders:
            if reminder.message not in seen_messages:
                seen_messages.add(reminder.message)
                unique_reminders.append(reminder)
                
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        unique_reminders.sort(key=lambda r: priority_order.get(r.priority, 3))
        
        # Limit total reminders
        max_reminders = 5
        return unique_reminders[:max_reminders]
    
    def format_reminders_for_display(self, reminders: List[AgentReminder]) -> str:
        """Format reminders for terminal display."""
        if not reminders:
            return ""
            
        lines = ["\n🧠 Agent 2 Memory Reminders:"]
        lines.append("─" * 50)
        
        for i, reminder in enumerate(reminders, 1):
            priority_icon = {"high": "🔥", "medium": "⚡", "low": "💡"}.get(reminder.priority, "📝")
            lines.append(f"{priority_icon} {reminder.message}")
            
        lines.append("─" * 50)
        return "\n".join(lines)

# Global reminder system instance
_reminder_system = None

def get_reminder_system(project_root: str = None) -> MemoryReminderSystem:
    """Get the global reminder system instance."""
    global _reminder_system
    
    if not project_root:
        project_root = str(Path.cwd())
        
    if _reminder_system is None or str(_reminder_system.project_root) != project_root:
        _reminder_system = MemoryReminderSystem(project_root)
        
    return _reminder_system

def show_post_command_reminders(command: str, result: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Show Agent 2 reminders after command completion.
    
    This function should be called at the end of CLI commands to provide
    contextual reminders from Agent 2 to help Agent 1 stay focused.
    """
    try:
        reminder_system = get_reminder_system()
        reminders = reminder_system.generate_post_command_reminders(command, result, context)
        
        if reminders:
            reminder_text = reminder_system.format_reminders_for_display(reminders)
            print(reminder_text)
            
            # Store reminders in memory for future reference
            reminder_summary = f"Agent 2 reminders after '{command}': " + "; ".join([r.message for r in reminders])
            add_to_memory(reminder_summary, {
                "type": "agent_reminder",
                "source": "agent2_memory_system",
                "command": command,
                "reminder_count": len(reminders)
            })
            
    except Exception as e:
        # Silent failure - don't disrupt user workflow
        logging.getLogger(__name__).debug(f"Reminder generation failed: {e}")

def test_reminder_system() -> bool:
    """Test the reminder system functionality."""
    print("🧠 Testing Agent Memory Reminder System...")
    
    try:
        reminder_system = get_reminder_system()
        
        # Test discuss reminders
        print("📝 Testing discuss command reminders...")
        discuss_reminders = reminder_system._generate_discuss_reminders(
            "Requirements are unclear and need more information", 
            {"needs_clarification": True}
        )
        print(f"✅ Generated {len(discuss_reminders)} discuss reminders")
        
        # Test plan reminders
        print("📋 Testing plan command reminders...")
        plan_reminders = reminder_system._generate_plan_reminders(
            "Plan created successfully",
            {"task_count": 12, "high_complexity_tasks": 2}
        )
        print(f"✅ Generated {len(plan_reminders)} plan reminders")
        
        # Test run reminders
        print("🚀 Testing run command reminders...")
        run_reminders = reminder_system._generate_run_reminders(
            "Tasks executed",
            {"completed_tasks": 3, "failed_tasks": 1, "remaining_tasks": 5}
        )
        print(f"✅ Generated {len(run_reminders)} run reminders")
        
        # Test formatting
        print("🎨 Testing reminder formatting...")
        all_reminders = discuss_reminders + plan_reminders + run_reminders
        formatted = reminder_system.format_reminders_for_display(all_reminders[:3])
        print("✅ Reminder formatting successful")
        print(formatted)
        
        print("\n🎉 Reminder system test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Reminder system test failed: {e}")
        return False
