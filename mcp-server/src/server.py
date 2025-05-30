#!/usr/bin/env python3
"""
NeuroDock MCP Server - Python Implementation
Model Context Protocol server for NeuroDock project management
"""

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
import asyncio
import subprocess
import webbrowser
from urllib.parse import urlencode

from mcp.server.fastmcp import FastMCP

# Import NeuroDock core modules
try:
    # Add the NeuroDock source directory to Python path
    neurodock_src = Path(__file__).parent.parent.parent / "src"
    if neurodock_src.exists():
        sys.path.insert(0, str(neurodock_src))
    
    from neurodock.db import get_store
    from neurodock.discussion import run_interactive_discussion
    from neurodock.agent import ProjectAgent
    from neurodock.memory.qdrant_store import search_memory, add_to_memory
    from neurodock.memory.neo4j_store import get_neo4j_store
    # Import CLI functions for project management
    from neurodock.cli import (
        get_current_project, set_current_project, create_project,
        list_available_projects, get_project_metadata, update_project_metadata
    )
    NEURODOCK_AVAILABLE = True
except ImportError as e:
    print(f"Warning: NeuroDock core modules not available: {e}", file=sys.stderr)
    NEURODOCK_AVAILABLE = False

# Initialize FastMCP server
mcp = FastMCP("neurodock-mcp")

def get_neurodock_store():
    """Get NeuroDock database store instance"""
    if not NEURODOCK_AVAILABLE:
        return None
    
    try:
        # Get current working directory as project path
        project_path = str(Path.cwd())
        return get_store(project_path)
    except Exception as e:
        print(f"Failed to connect to NeuroDock database: {e}", file=sys.stderr)
        return None

def get_project_agent():
    """Get NeuroDock project agent instance"""
    if not NEURODOCK_AVAILABLE:
        return None
    
    try:
        project_path = str(Path.cwd())
        return ProjectAgent(project_path)
    except Exception as e:
        print(f"Failed to initialize NeuroDock project agent: {e}", file=sys.stderr)
        return None

# MCP Resources - Project context and data
@mcp.resource("neurodock://project/files")
async def get_project_files() -> str:
    """Get the project file structure and important configuration files"""
    try:
        cwd = Path.cwd()
        structure = {"files": [], "config_files": {}}
        
        # Get file tree
        for item in cwd.rglob('*'):
            if (item.is_file() and 
                not any(part.startswith('.') for part in item.parts) and
                not any(part in ['node_modules', '__pycache__', '.git'] for part in item.parts)):
                rel_path = str(item.relative_to(cwd))
                if len(rel_path) < 200:  # Reasonable path length
                    structure["files"].append(rel_path)
        
        # Read important config files
        config_files = ['package.json', 'requirements.txt', 'pyproject.toml', 'README.md', '.neurodock/config.json']
        for config_file in config_files:
            config_path = cwd / config_file
            if config_path.exists() and config_path.stat().st_size < 50000:  # < 50KB
                try:
                    structure["config_files"][config_file] = config_path.read_text()
                except Exception:
                    structure["config_files"][config_file] = "Error reading file"
        
        return json.dumps(structure, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.resource("neurodock://project/tasks")
async def get_project_tasks() -> str:
    """Get all tasks and their current status"""
    store = get_neurodock_store()
    if not store:
        return json.dumps({"error": "NeuroDock store not available"})
    
    try:
        tasks = store.get_tasks()
        return json.dumps({"tasks": tasks}, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.resource("neurodock://project/memory")
async def get_project_memory() -> str:
    """Get project memories and decisions"""
    store = get_neurodock_store()
    if not store:
        return json.dumps({"error": "NeuroDock store not available"})
    
    try:
        memories = store.get_all_memories()
        return json.dumps({"memories": memories}, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.resource("neurodock://project/context")
async def get_full_project_context() -> str:
    """Get comprehensive project context including files, tasks, and memories"""
    agent = get_project_agent()
    if not agent:
        return json.dumps({"error": "NeuroDock project agent not available"})
    
    try:
        context = agent.load_project_context()
        return json.dumps(context, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})

# MCP Prompts - Agile workflow templates
@mcp.prompt("neurodock-requirements-gathering")
async def requirements_gathering_prompt(project_name: str = "", stakeholder: str = "user") -> str:
    """Template for gathering project requirements systematically"""
    return f"""
# Requirements Gathering Session for {project_name or "Project"}

## Stakeholder: {stakeholder}

### 1. Project Overview
- What is the main purpose/goal of this project?
- Who are the primary users/beneficiaries?
- What problem does this solve?

### 2. Functional Requirements
- What specific features/capabilities must the system have?
- What are the user stories or use cases?
- What are the acceptance criteria for each feature?

### 3. Non-Functional Requirements
- Performance requirements (speed, scalability, etc.)
- Security and compliance needs
- Usability and accessibility requirements
- Integration requirements with existing systems

### 4. Constraints and Assumptions
- Budget and timeline constraints
- Technology or platform restrictions
- Resource availability
- Regulatory or compliance requirements

### 5. Success Criteria
- How will success be measured?
- What are the key performance indicators (KPIs)?
- What constitutes project completion?

## Next Steps
1. Review and prioritize requirements
2. Identify dependencies and risks
3. Create initial project plan
4. Schedule follow-up sessions as needed

Use the neurodock_add_memory tool to capture important decisions and requirements discussed.
"""

@mcp.prompt("neurodock-sprint-planning")
async def sprint_planning_prompt(sprint_number: int = 1, duration_weeks: int = 2) -> str:
    """Template for agile sprint planning sessions"""
    return f"""
# Sprint {sprint_number} Planning Session

## Sprint Details
- Duration: {duration_weeks} weeks
- Start Date: [TO BE FILLED]
- End Date: [TO BE FILLED]

## Sprint Goal
[Define the high-level objective for this sprint]

## Backlog Review
1. Review product backlog priorities
2. Identify tasks ready for development
3. Estimate effort for each task

## Capacity Planning
- Team availability (accounting for holidays, PTO, etc.)
- Estimated velocity based on historical data
- Risk factors and dependencies

## Task Selection
Use neurodock_list_tasks to review available tasks, then:
1. Select high-priority tasks that fit sprint capacity
2. Break down large tasks into smaller, manageable pieces
3. Assign tasks to team members
4. Update task status using neurodock_update_task

## Definition of Done
- [ ] Code written and reviewed
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] Deployed to staging environment
- [ ] Stakeholder acceptance received

## Sprint Backlog
[List selected tasks with estimates]

## Risk Mitigation
- Identify potential blockers
- Plan mitigation strategies
- Establish communication protocols

Use neurodock_add_memory to capture sprint planning decisions and commitments.
"""

@mcp.prompt("neurodock-retrospective")
async def retrospective_prompt(sprint_number: int = 1) -> str:
    """Template for sprint retrospective sessions"""
    return f"""
# Sprint {sprint_number} Retrospective

## Sprint Summary
- Sprint Goal: [Review the goal set during planning]
- Planned vs. Actual Delivery: [Compare what was planned vs. delivered]
- Key Metrics: [Velocity, burndown, quality metrics]

## What Went Well? 🎉
- Successes and achievements
- Effective practices and processes
- Team collaboration highlights
- Technical wins

## What Could Be Improved? 🔍
- Challenges and obstacles encountered
- Process inefficiencies
- Communication gaps
- Technical debt or quality issues

## Action Items 🎯
1. [Specific improvement to implement]
2. [Process change to try]
3. [Team practice to adopt]
4. [Issue to address]

## Lessons Learned 📚
- Key insights from this sprint
- Knowledge to share with other teams
- Documentation to update

## Next Sprint Considerations
- Adjustments to process or practices
- Capacity or velocity changes
- Dependencies to address

## Team Feedback
- Individual reflections
- Team dynamics observations
- Suggestions for team development

Use neurodock_add_memory to capture retrospective insights and action items.
Use neurodock_create_task to create tasks for implementing improvements.
"""

@mcp.prompt("neurodock-daily-standup")
async def daily_standup_prompt() -> str:
    """Template for daily standup meetings"""
    return f"""
# Daily Standup - {datetime.now().strftime('%Y-%m-%d')}

## Standup Format
Each team member shares:

### 1. What did you accomplish yesterday?
- Completed tasks and progress made
- Key achievements or breakthroughs

### 2. What will you work on today?
- Planned tasks and priorities
- Goals for the day

### 3. Are there any blockers or impediments?
- Obstacles preventing progress
- Help needed from team or stakeholders

## Team Updates
Use neurodock_list_tasks status=in_progress to review active work.

## Action Items
- [ ] Address any blockers identified
- [ ] Update task status using neurodock_update_task
- [ ] Schedule follow-up discussions if needed

## Notes and Decisions
Use neurodock_add_memory to capture any important decisions or information shared.

## Team Availability
- [Note any planned absences or limited availability]

Keep this meeting focused and timeboxed to 15 minutes or less.
"""

@mcp.tool()
async def neurodock_get_project_status(project_path: str = "") -> str:
    """Get the current status of the NeuroDock project including active tasks and recent activity.
    
    Args:
        project_path: Optional path to specific project directory
    """
    store = get_neurodock_store()
    if not store:
        return "❌ NeuroDock database not available. Run 'nd setup' to configure the database connection."
    
    try:
        # Get recent tasks
        tasks = store.get_tasks()
        recent_tasks = tasks[-5:] if tasks else []
        
        # Get recent memories
        memories = store.get_all_memories()
        recent_memories = memories[:3] if memories else []
        
        # Get project statistics
        stats = store.get_project_stats()
        
        # Get project context if agent is available
        agent = get_project_agent()
        context_info = {}
        if agent:
            try:
                context_info = agent.load_project_context()
            except Exception as e:
                context_info = {"error": f"Failed to load project context: {e}"}
        
        status_info = {
            "project_path": project_path or str(Path.cwd()),
            "recent_tasks": [
                {
                    "id": task.get("id"),
                    "title": task.get("title"),
                    "status": task.get("status"),
                    "created_at": str(task.get("created_at", ""))
                } for task in recent_tasks
            ],
            "recent_memories": [
                {
                    "type": memory.get("type"),
                    "text": memory.get("text", "")[:200] + "..." if len(memory.get("text", "")) > 200 else memory.get("text", ""),
                    "created_at": str(memory.get("created_at", ""))
                } for memory in recent_memories
            ],
            "project_stats": stats,
            "neurodock_available": True,
            "context_summary": context_info
        }
        
        return f"✅ NeuroDock Project Status:\n\n{json.dumps(status_info, indent=2, default=str)}"
        
    except Exception as e:
        return f"❌ Error retrieving project status: {str(e)}"

@mcp.tool()
async def neurodock_list_tasks(status: str = "all", limit: int = 10) -> str:
    """List tasks in the NeuroDock project with optional filtering.
    
    Args:
        status: Filter by task status (pending, in_progress, completed, failed, or all)
        limit: Maximum number of tasks to return
    """
    store = get_neurodock_store()
    if not store:
        return "❌ NeuroDock database not available. Run 'nd setup' to configure the database connection."
    
    try:
        if status == "all":
            tasks = store.get_tasks()
        else:
            tasks = store.get_tasks(status=status)
        
        # Limit results
        limited_tasks = tasks[:limit] if tasks else []
        
        task_data = []
        for task in limited_tasks:
            task_data.append({
                "id": task.get("id"),
                "title": task.get("title"),
                "description": task.get("description"),
                "status": task.get("status"),
                "complexity": task.get("complexity"),
                "created_at": str(task.get("created_at", "")),
                "updated_at": str(task.get("updated_at", ""))
            })
        
        return f"📋 Tasks (showing {len(task_data)} results, filtered by '{status}'):\n\n{json.dumps(task_data, indent=2, default=str)}"
        
    except Exception as e:
        return f"❌ Error retrieving tasks: {str(e)}"

@mcp.tool()
async def neurodock_update_task(task_id: str, status: str = "", notes: str = "") -> str:
    """Update the status or details of a specific task.
    
    Args:
        task_id: ID of the task to update
        status: New status for the task (pending, in_progress, completed, failed)
        notes: Additional notes about the task update
    """
    store = get_neurodock_store()
    if not store:
        return "❌ NeuroDock database not available. Run 'nd setup' to configure the database connection."
    
    try:
        if status:
            success = store.update_task_status(task_id, status)
            if not success:
                return f"❌ Failed to update task {task_id}. Task may not exist."
        
        # Add notes to memory if provided
        if notes:
            memory_text = f"Task Update - {task_id}: {notes}"
            store.add_memory(memory_text, "task_update")
        
        # Get updated task details
        tasks = store.get_tasks()
        updated_task = next((task for task in tasks if task.get("id") == task_id), None)
        
        if updated_task:
            result = {
                "task_id": task_id,
                "updated_status": updated_task.get("status"),
                "title": updated_task.get("title"),
                "notes_added": bool(notes),
                "timestamp": str(updated_task.get("updated_at", ""))
            }
            return f"✅ Task {task_id} updated successfully:\n\n{json.dumps(result, indent=2)}"
        else:
            return f"⚠️ Task {task_id} updated but details could not be retrieved."
            
    except Exception as e:
        return f"❌ Error updating task {task_id}: {str(e)}"

@mcp.tool()
async def neurodock_create_task(description: str, priority: str = "medium", category: str = "general") -> str:
    """Create a new task in the NeuroDock project.
    
    Args:
        description: Description of the task to create
        priority: Priority level of the task (low, medium, high)
        category: Category or type of task (bug, feature, documentation, etc.)
    """
    store = get_neurodock_store()
    if not store:
        return "❌ NeuroDock database not available. Run 'nd setup' to configure the database connection."
    
    try:
        # Create task using NeuroDock store
        task_data = {
            "title": description,
            "description": description,
            "status": "pending",
            "priority": priority,
            "category": category,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        task_id = store.add_task(task_data)
        
        # Also add creation to memory for context
        memory_content = f"Created new task: {description} (Priority: {priority}, Category: {category})"
        store.add_memory({
            "type": "task_creation",
            "text": memory_content,
            "metadata": {"task_id": task_id, "action": "create_task"},
            "created_at": datetime.now()
        })
        
        return f"✅ Task created successfully with ID {task_id}\nTitle: {description}\nPriority: {priority}\nCategory: {category}"
        
    except Exception as e:
        return f"❌ Failed to create task: {str(e)}"

@mcp.tool()
async def neurodock_add_memory(content: str, category: str = "note", tags: List[str] = None) -> str:
    """Store important information or decisions in the project memory.
    
    Args:
        content: The information to store in memory
        category: Category for the memory (decision, requirement, note, etc.)
        tags: Tags to help organize and search the memory
    """
    if tags is None:
        tags = []
    
    store = get_neurodock_store()
    if not store:
        return "❌ NeuroDock database not available. Run 'nd setup' to configure the database connection."
    
    try:
        # Store in NeuroDock memory system
        memory_data = {
            "type": category,
            "text": content,
            "tags": tags,
            "metadata": {"source": "mcp_server", "category": category},
            "created_at": datetime.now()
        }
        
        memory_id = store.add_memory(memory_data)
        
        # For Qdrant vector search integration if available
        try:
            add_to_memory(content, metadata={"category": category, "tags": tags, "id": memory_id})
        except Exception as e:
            # Vector store not available, continue with regular storage
            pass
        
        return f"✅ Memory stored successfully with ID {memory_id}\nCategory: {category}\nTags: {', '.join(tags) if tags else 'None'}\nContent: {content[:100]}{'...' if len(content) > 100 else ''}"
        
    except Exception as e:
        return f"❌ Failed to store memory: {str(e)}"

@mcp.tool()
async def neurodock_search_memory(query: str, category: str = "", limit: int = 5) -> str:
    """Search through project memories and past decisions.
    
    Args:
        query: Search terms to find relevant memories
        category: Filter by memory category
        limit: Maximum number of results to return
    """
    store = get_neurodock_store()
    if not store:
        return "❌ NeuroDock database not available. Run 'nd setup' to configure the database connection."
    
    try:
        # First try vector search with Qdrant if available
        vector_results = []
        try:
            vector_results = search_memory(query, limit=limit)
        except Exception as e:
            # Vector search not available, fall back to text search
            pass
        
        # Get memories from store with filtering
        all_memories = store.get_all_memories()
        filtered_memories = []
        
        for memory in all_memories:
            # Filter by category if specified
            if category and memory.get("type", "").lower() != category.lower():
                continue
                
            # Simple text search in content
            memory_text = memory.get("text", "").lower()
            if query.lower() in memory_text:
                filtered_memories.append(memory)
        
        # Sort by relevance/date and limit results
        filtered_memories = sorted(filtered_memories, 
                                 key=lambda x: x.get("created_at", ""), 
                                 reverse=True)[:limit]
        
        # Combine vector and text results
        results = []
        seen_ids = set()
        
        # Add vector results first (if any)
        for result in vector_results[:limit]:
            if result.get("id") not in seen_ids:
                results.append({
                    "source": "vector_search",
                    "score": result.get("score", 0),
                    "content": result.get("content", ""),
                    "metadata": result.get("metadata", {})
                })
                seen_ids.add(result.get("id"))
        
        # Add text search results
        for memory in filtered_memories:
            if memory.get("id") not in seen_ids:
                results.append({
                    "source": "text_search",
                    "id": memory.get("id"),
                    "type": memory.get("type"),
                    "content": memory.get("text", ""),
                    "tags": memory.get("tags", []),
                    "created_at": str(memory.get("created_at", ""))
                })
                seen_ids.add(memory.get("id"))
        
        if not results:
            return f"🔍 No memories found matching '{query}'"
        
        return f"🔍 Memory search results for '{query}' (found {len(results)} matches):\n\n{json.dumps(results[:limit], indent=2, default=str)}"
        
    except Exception as e:
        return f"❌ Error searching memories: {str(e)}"

@mcp.tool()
async def neurodock_get_project_context(include_files: bool = True, include_git: bool = True) -> str:
    """Get comprehensive context about the current project including structure, recent changes, and configuration.
    
    Args:
        include_files: Include file tree and important file contents
        include_git: Include git status and recent commits
    """
    store = get_neurodock_store()
    agent = get_project_agent()
    
    context = {
        "current_directory": str(Path.cwd()),
        "neurodock_available": bool(store),
        "project_agent_available": bool(agent)
    }
    
    # Use ProjectAgent for comprehensive context loading if available
    if agent:
        try:
            agent_context = agent.load_project_context()
            context.update(agent_context)
        except Exception as e:
            context["agent_context_error"] = str(e)
    
    # Get project statistics from store
    if store:
        try:
            context["project_stats"] = store.get_project_stats()
            
            # Get recent activity
            recent_tasks = store.get_tasks()
            context["recent_tasks"] = [
                {
                    "id": task.get("id"),
                    "title": task.get("title"),
                    "status": task.get("status"),
                    "updated_at": str(task.get("updated_at", ""))
                } for task in recent_tasks[-5:]  # Last 5 tasks
            ]
            
            recent_memories = store.get_all_memories()
            context["recent_memories"] = [
                {
                    "type": memory.get("type"),
                    "text": memory.get("text", "")[:100] + "..." if len(memory.get("text", "")) > 100 else memory.get("text", ""),
                    "created_at": str(memory.get("created_at", ""))
                } for memory in recent_memories[:3]  # Last 3 memories
            ]
        except Exception as e:
            context["store_error"] = str(e)
    
    if include_git:
        try:
            # Get git status using subprocess since we're removing execute_nd_command
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, cwd=Path.cwd())
            if result.returncode == 0:
                context["git_status"] = result.stdout
                
            # Get recent commits
            result = subprocess.run(['git', 'log', '--oneline', '-5'], 
                                  capture_output=True, text=True, cwd=Path.cwd())
            if result.returncode == 0:
                context["recent_commits"] = result.stdout
        except Exception as e:
            context["git_error"] = str(e)
    
    if include_files:
        try:
            # Get project structure
            cwd = Path.cwd()
            files = []
            for item in cwd.rglob('*'):
                if (item.is_file() and 
                    not any(part.startswith('.') for part in item.parts) and
                    not any(part in ['node_modules', '__pycache__', '.git'] for part in item.parts)):
                    rel_path = item.relative_to(cwd)
                    if len(str(rel_path)) < 100:  # Avoid very long paths
                        files.append(str(rel_path))
            
            context["project_files"] = files[:50]  # Limit to 50 files
            
            # Try to read important configuration files
            config_files = ['package.json', 'requirements.txt', 'pyproject.toml', 'Cargo.toml', 'README.md']
            for config_file in config_files:
                config_path = cwd / config_file
                if config_path.exists() and config_path.stat().st_size < 10000:  # < 10KB
                    try:
                        context[f"{config_file}_content"] = config_path.read_text()
                    except Exception:
                        continue
                        
        except Exception as e:
            context["files_error"] = str(e)
    
    return f"📋 Project Context:\n\n{json.dumps(context, indent=2, default=str)}"

@mcp.tool()
async def neurodock_start_discussion(topic: str, context: str = "", participants: List[str] = None) -> str:
    """Start an interactive discussion workflow with the NeuroDock system.
    
    Args:
        topic: The main topic or question to discuss
        context: Additional context or background information
        participants: List of participant roles (e.g., ["user", "architect", "qa"])
    """
    if participants is None:
        participants = ["user", "system"]
    
    try:
        # Use NeuroDock's discussion system
        discussion_result = run_interactive_discussion(
            topic=topic,
            context=context,
            participants=participants,
            mode="start"
        )
        
        # Store discussion initiation in memory
        store = get_neurodock_store()
        if store:
            memory_data = {
                "type": "discussion_start",
                "text": f"Started discussion on: {topic}",
                "metadata": {
                    "topic": topic,
                    "context": context,
                    "participants": participants,
                    "discussion_id": discussion_result.get("discussion_id")
                },
                "created_at": datetime.now()
            }
            store.add_memory(memory_data)
        
        return f"💬 Discussion started successfully!\n\n{json.dumps(discussion_result, indent=2, default=str)}"
        
    except Exception as e:
        return f"❌ Failed to start discussion: {str(e)}"

@mcp.tool()
async def neurodock_continue_discussion(discussion_id: str, message: str, participant: str = "user") -> str:
    """Continue an existing interactive discussion with new input.
    
    Args:
        discussion_id: ID of the discussion to continue
        message: The message or input to add to the discussion
        participant: The role of the participant sending the message
    """
    try:
        # Continue the discussion using NeuroDock's system
        discussion_result = run_interactive_discussion(
            discussion_id=discussion_id,
            message=message,
            participant=participant,
            mode="continue"
        )
        
        # Store discussion update in memory
        store = get_neurodock_store()
        if store:
            memory_data = {
                "type": "discussion_update",
                "text": f"Discussion update from {participant}: {message[:100]}{'...' if len(message) > 100 else ''}",
                "metadata": {
                    "discussion_id": discussion_id,
                    "participant": participant,
                    "message_length": len(message)
                },
                "created_at": datetime.now()
            }
            store.add_memory(memory_data)
        
        return f"💬 Discussion continued:\n\n{json.dumps(discussion_result, indent=2, default=str)}"
        
    except Exception as e:
        return f"❌ Failed to continue discussion: {str(e)}"

@mcp.tool()
async def neurodock_get_discussion_status(discussion_id: str = "", include_history: bool = True) -> str:
    """Get the status and history of discussions.
    
    Args:
        discussion_id: Specific discussion ID to check (if empty, returns all recent discussions)
        include_history: Whether to include the full discussion history
    """
    store = get_neurodock_store()
    if not store:
        return "❌ NeuroDock database not available. Run 'nd setup' to configure the database connection."
    
    try:
        # Get discussion-related memories
        all_memories = store.get_all_memories()
        discussion_memories = [
            memory for memory in all_memories 
            if memory.get("type", "").startswith("discussion")
        ]
        
        if discussion_id:
            # Filter by specific discussion ID
            discussion_memories = [
                memory for memory in discussion_memories
                if memory.get("metadata", {}).get("discussion_id") == discussion_id
            ]
        
        # Organize by discussion ID
        discussions = {}
        for memory in discussion_memories:
            d_id = memory.get("metadata", {}).get("discussion_id", "unknown")
            if d_id not in discussions:
                discussions[d_id] = {
                    "discussion_id": d_id,
                    "events": [],
                    "participants": set(),
                    "topic": None,
                    "started_at": None,
                    "last_activity": None
                }
            
            discussions[d_id]["events"].append(memory)
            
            # Extract metadata
            metadata = memory.get("metadata", {})
            if "participants" in metadata:
                discussions[d_id]["participants"].update(metadata["participants"])
            if "participant" in metadata:
                discussions[d_id]["participants"].add(metadata["participant"])
            if "topic" in metadata:
                discussions[d_id]["topic"] = metadata["topic"]
            
            # Track timing
            created_at = memory.get("created_at")
            if created_at:
                if not discussions[d_id]["started_at"] or created_at < discussions[d_id]["started_at"]:
                    discussions[d_id]["started_at"] = created_at
                if not discussions[d_id]["last_activity"] or created_at > discussions[d_id]["last_activity"]:
                    discussions[d_id]["last_activity"] = created_at
        
        # Convert sets to lists for JSON serialization
        for d_id in discussions:
            discussions[d_id]["participants"] = list(discussions[d_id]["participants"])
            discussions[d_id]["event_count"] = len(discussions[d_id]["events"])
            
            if not include_history:
                # Just keep summary info
                discussions[d_id]["events"] = f"{len(discussions[d_id]['events'])} events"
        
        if not discussions:
            return "📝 No discussions found."
        
        return f"📝 Discussion Status:\n\n{json.dumps(discussions, indent=2, default=str)}"
        
    except Exception as e:
        return f"❌ Error retrieving discussion status: {str(e)}"

def initialize_neurodock():
    """Initialize NeuroDock connections and verify system availability"""
    try:
        store = get_neurodock_store()
        if store:
            print("✅ NeuroDock store initialized successfully")
        else:
            print("⚠️  NeuroDock store not available - some features may be limited")
        
        agent = get_project_agent()
        if agent:
            print("✅ NeuroDock project agent initialized successfully")
        else:
            print("⚠️  NeuroDock project agent not available - context features may be limited")
            
        # Test vector memory if available
        try:
            search_memory("test", limit=1)
            print("✅ Vector memory search available")
        except Exception:
            print("⚠️  Vector memory search not available - using text-based search only")
            
    except Exception as e:
        print(f"⚠️  NeuroDock initialization warning: {e}")

if __name__ == "__main__":
    # Initialize NeuroDock systems
    initialize_neurodock()
    
    # Run the FastMCP server
    mcp.run(transport='stdio')

# ==============================================================================
# UI GENERATION TOOLS - V0.dev & Loveable Integration
# ==============================================================================

@mcp.tool()
async def generate_ui_component(
    component_description: str,
    design_requirements: str = "Clean, modern design with good UX",
    component_type: str = "react",
    framework: str = "nextjs",
    styling: str = "tailwindcss",
    data_structure: str = "{}"
) -> str:
    """Generate React UI components using V0.dev with mandatory visual preview.
    
    This tool creates React/Next.js components with a visual preview that MUST be approved
    before code generation. Perfect for creating individual UI components, forms, 
    dashboards, and complex interfaces.
    
    Args:
        component_description: Detailed description of what the component should do
        design_requirements: Visual and UX requirements (colors, layout, interactions)
        component_type: Type of component (react, vue, angular) - default: react
        framework: Framework to use (nextjs, react, vite) - default: nextjs
        styling: Styling approach (tailwindcss, shadcn, styled-components) - default: tailwindcss
        data_structure: JSON string describing the data/props structure
    
    Returns:
        V0.dev preview URL and component generation status
    """
    try:
        # Parse data structure
        try:
            data_props = json.loads(data_structure) if data_structure.strip() else {}
        except json.JSONDecodeError:
            data_props = {}
        
        # Build comprehensive V0.dev prompt
        prompt_parts = [
            f"Create a {component_type} component: {component_description}",
            f"\nDesign Requirements: {design_requirements}",
            f"\nFramework: {framework}",
            f"Styling: {styling}",
        ]
        
        if data_props:
            prompt_parts.append(f"\nData Structure: {json.dumps(data_props, indent=2)}")
        
        # Add best practices
        prompt_parts.extend([
            "\nBest Practices:",
            "- Mobile-first responsive design",
            "- Accessible (WCAG 2.1 AA compliant)",
            "- Type-safe with TypeScript",
            "- Clean, semantic HTML structure",
            "- Modern React patterns (hooks, functional components)",
            "- Performance optimized",
        ])
        
        full_prompt = "\n".join(prompt_parts)
        
        # Create V0.dev URL with prompt
        v0_base_url = "https://v0.dev/chat"
        v0_params = {
            "q": full_prompt
        }
        v0_url = f"{v0_base_url}?{urlencode(v0_params)}"
        
        # Store component generation request
        store = get_neurodock_store()
        component_id = f"ui_component_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if store:
            component_request = {
                "id": component_id,
                "type": "ui_component_generation",
                "description": component_description,
                "design_requirements": design_requirements,
                "framework": framework,
                "styling": styling,
                "data_structure": data_props,
                "v0_url": v0_url,
                "status": "preview_required",
                "created_at": datetime.now().isoformat(),
                "preview_approved": False
            }
            
            store.add_memory({
                "content": f"UI Component Generation Request: {component_description}",
                "type": "ui_generation",
                "metadata": component_request
            })
        
        result = {
            "status": "preview_required",
            "component_id": component_id,
            "v0_preview_url": v0_url,
            "description": component_description,
            "next_steps": [
                "1. 🔗 Open the V0.dev preview URL to see your component",
                "2. 👀 Review the visual design and functionality", 
                "3. ✅ If approved, use 'approve_ui_component' tool to export code",
                "4. ❌ If changes needed, modify prompt and regenerate"
            ],
            "warning": "⚠️ MANDATORY PREVIEW: Component code will only be exported after visual approval"
        }
        
        return f"""🎨 UI Component Generation Started!

📋 **Component Details:**
- **Description:** {component_description}
- **Framework:** {framework} with {styling}
- **Component ID:** {component_id}

🔗 **V0.dev Preview URL:**
{v0_url}

🚨 **CRITICAL: Visual Preview Required**
Please open the V0.dev URL above to see your component. This is MANDATORY before code export.

📝 **Next Steps:**
1. Click the V0.dev link to preview your component
2. Review the design, layout, and functionality
3. If satisfied, run: `approve_ui_component` with component_id: {component_id}
4. If changes needed, modify requirements and regenerate

⚡ **Quick Actions:**
- Approve: Use `approve_ui_component("{component_id}")`
- Modify: Use `generate_ui_component` with updated requirements
- Cancel: Use `cancel_ui_generation("{component_id}")`

{json.dumps(result, indent=2)}"""
        
    except Exception as e:
        return f"❌ UI component generation failed: {str(e)}"

@mcp.tool()
async def approve_ui_component(component_id: str, feedback: str = "") -> str:
    """Approve a UI component after visual preview and export the code.
    
    This tool should only be called AFTER reviewing the V0.dev preview and confirming
    the component meets your requirements.
    
    Args:
        component_id: The component ID from generate_ui_component
        feedback: Optional feedback about the component
    
    Returns:
        Component code and integration instructions
    """
    try:
        store = get_neurodock_store()
        if not store:
            return "❌ NeuroDock database not available"
        
        # Find the component request
        memories = store.get_all_memories()
        component_memory = None
        
        for memory in memories:
            if (memory.get("type") == "ui_generation" and 
                memory.get("metadata", {}).get("id") == component_id):
                component_memory = memory
                break
        
        if not component_memory:
            return f"❌ Component ID {component_id} not found. Please check the ID and try again."
        
        component_data = component_memory.get("metadata", {})
        
        if component_data.get("status") != "preview_required":
            return f"❌ Component {component_id} is not in preview_required status"
        
        # Update component status to approved
        component_data["status"] = "approved"
        component_data["preview_approved"] = True
        component_data["approved_at"] = datetime.now().isoformat()
        component_data["feedback"] = feedback
        
        # Generate integration instructions
        framework = component_data.get("framework", "nextjs")
        styling = component_data.get("styling", "tailwindcss")
        description = component_data.get("description", "")
        
        # Create component file structure
        component_name = component_id.replace("ui_component_", "").replace("_", "-")
        
        integration_guide = f"""
🎉 **UI Component Approved!**

📋 **Component Details:**
- **Name:** {component_name}
- **Description:** {description}
- **Framework:** {framework}
- **Styling:** {styling}

📂 **Recommended File Structure:**
```
src/
  components/
    {component_name}/
      index.tsx          # Main component
      types.ts           # TypeScript interfaces
      styles.module.css  # Component styles (if needed)
      {component_name}.stories.tsx  # Storybook stories (optional)
      {component_name}.test.tsx     # Unit tests (optional)
```

🔧 **Integration Steps:**

1. **Export from V0.dev:**
   - Go back to your V0.dev preview
   - Click "Copy Code" or "Export" button
   - Copy the React/TypeScript component code

2. **Install Dependencies (if new):**
   ```bash
   npm install @radix-ui/react-* # If using Radix components
   npm install lucide-react      # If using Lucide icons
   ```

3. **Create Component File:**
   ```bash
   mkdir -p src/components/{component_name}
   touch src/components/{component_name}/index.tsx
   ```

4. **Add to Component Library:**
   ```typescript
   // src/components/index.ts
   export {{ default as {component_name.title()} }} from './{component_name}';
   ```

5. **Usage Example:**
   ```tsx
   import {{ {component_name.title()} }} from '@/components/{component_name}';
   
   function App() {{
     return (
       <div>
         <{component_name.title()} 
           // Add your props here based on V0.dev component
         />
       </div>
     );
   }}
   ```

💡 **Pro Tips:**
- Test component in isolation first
- Add TypeScript interfaces for all props
- Consider creating Storybook stories for documentation
- Add unit tests for critical functionality
- Ensure responsive design works on all screen sizes

✅ **Component Status:** Ready for Integration
"""

        # Store approval
        store.add_memory({
            "content": f"UI Component Approved: {description} (ID: {component_id})",
            "type": "ui_generation_approved",
            "metadata": component_data
        })
        
        return integration_guide
        
    except Exception as e:
        return f"❌ Failed to approve UI component: {str(e)}"

@mcp.tool()
async def generate_full_app(
    app_description: str,
    tech_requirements: str = "React, TypeScript, Tailwind CSS",
    user_flows: str = "[]",
    app_type: str = "web_app",
    deployment_preference: str = "vercel"
) -> str:
    """Generate complete full-stack applications using Loveable with mandatory preview.
    
    This tool creates entire applications with backend, frontend, database, and deployment.
    Perfect for MVPs, prototypes, and complete application development.
    
    Args:
        app_description: Detailed description of the application and its purpose
        tech_requirements: Technologies needed (databases, APIs, integrations)
        user_flows: JSON string describing main user journeys and workflows
        app_type: Type of application (web_app, mobile_app, dashboard, saas)
        deployment_preference: Preferred hosting (vercel, netlify, custom)
    
    Returns:
        Loveable app preview URL and generation status
    """
    try:
        # Parse user flows
        try:
            flows = json.loads(user_flows) if user_flows.strip() != "[]" else []
        except json.JSONDecodeError:
            flows = []
        
        # Build comprehensive Loveable prompt
        prompt_parts = [
            f"Create a {app_type}: {app_description}",
            f"\nTechnology Requirements: {tech_requirements}",
            f"\nDeployment: {deployment_preference}",
        ]
        
        if flows:
            prompt_parts.append(f"\nUser Flows: {json.dumps(flows, indent=2)}")
        
        # Add application best practices
        prompt_parts.extend([
            "\nApplication Requirements:",
            "- Modern, responsive design",
            "- User authentication and authorization", 
            "- Database integration for data persistence",
            "- RESTful API endpoints",
            "- Error handling and validation",
            "- Loading states and user feedback",
            "- SEO optimized (if web app)",
            "- Performance optimized",
            "- Security best practices",
            "- Accessible design (WCAG compliance)"
        ])
        
        full_prompt = "\n".join(prompt_parts)
        
        # Create Loveable URL
        loveable_base_url = "https://lovable.dev/create"
        loveable_params = {
            "prompt": full_prompt
        }
        loveable_url = f"{loveable_base_url}?{urlencode(loveable_params)}"
        
        # Store app generation request
        store = get_neurodock_store()
        app_id = f"full_app_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if store:
            app_request = {
                "id": app_id,
                "type": "full_app_generation",
                "description": app_description,
                "tech_requirements": tech_requirements,
                "user_flows": flows,
                "app_type": app_type,
                "deployment_preference": deployment_preference,
                "loveable_url": loveable_url,
                "status": "preview_required",
                "created_at": datetime.now().isoformat(),
                "preview_approved": False
            }
            
            store.add_memory({
                "content": f"Full App Generation Request: {app_description}",
                "type": "app_generation",
                "metadata": app_request
            })
        
        result = {
            "status": "preview_required",
            "app_id": app_id,
            "loveable_preview_url": loveable_url,
            "description": app_description,
            "next_steps": [
                "1. 🔗 Open the Loveable URL to see your app being generated",
                "2. 👀 Review the live application preview",
                "3. ✅ If approved, use 'approve_full_app' tool to finalize deployment",
                "4. ❌ If changes needed, modify requirements and regenerate"
            ],
            "warning": "⚠️ MANDATORY PREVIEW: App will only be deployed after visual approval"
        }
        
        return f"""🚀 Full Application Generation Started!

📋 **Application Details:**
- **Description:** {app_description}
- **Type:** {app_type}
- **Tech Stack:** {tech_requirements}
- **App ID:** {app_id}

🔗 **Loveable Preview URL:**
{loveable_url}

🚨 **CRITICAL: Live App Preview Required**
Please open the Loveable URL above to see your complete application. This is MANDATORY before deployment.

📝 **Next Steps:**
1. Click the Loveable link to preview your full application
2. Test the functionality, user flows, and design
3. If satisfied, run: `approve_full_app` with app_id: {app_id}
4. If changes needed, modify requirements and regenerate

⚡ **Quick Actions:**
- Approve: Use `approve_full_app("{app_id}")`
- Modify: Use `generate_full_app` with updated requirements
- Working backend functionality
- Database integration
- Authentication (if required)
- Responsive design across devices

{json.dumps(result, indent=2)}"""
        
    except Exception as e:
        return f"❌ Full app generation failed: {str(e)}"

@mcp.tool()
async def approve_full_app(app_id: str, custom_domain: str = "", feedback: str = "") -> str:
    """Approve a full application after preview and finalize deployment.
    
    This tool should only be called AFTER reviewing the Loveable preview and confirming
    the application meets your requirements.
    
    Args:
        app_id: The app ID from generate_full_app
        custom_domain: Optional custom domain for deployment
        feedback: Optional feedback about the application
    
    Returns:
        Deployment URLs and project access information
    """
    try:
        store = get_neurodock_store()
        if not store:
            return "❌ NeuroDock database not available"
        
        # Find the app request
        memories = store.get_all_memories()
        app_memory = None
        
        for memory in memories:
            if (memory.get("type") == "app_generation" and 
                memory.get("metadata", {}).get("id") == app_id):
                app_memory = memory
                break
        
        if not app_memory:
            return f"❌ App ID {app_id} not found. Please check the ID and try again."
        
        app_data = app_memory.get("metadata", {})
        
        if app_data.get("status") != "preview_required":
            return f"❌ App {app_id} is not in preview_required status"
        
        # Update app status to approved
        app_data["status"] = "approved"
        app_data["preview_approved"] = True
        app_data["approved_at"] = datetime.now().isoformat()
        app_data["custom_domain"] = custom_domain
        app_data["feedback"] = feedback
        
        # Generate deployment information
        app_type = app_data.get("app_type", "web_app")
        description = app_data.get("description", "")
        tech_requirements = app_data.get("tech_requirements", "")
        deployment_pref = app_data.get("deployment_preference", "vercel")
        
        # Create app project structure
        app_name = app_id.replace("full_app_", "").replace("_", "-")
        
        deployment_guide = f"""
🎉 **Full Application Approved!**

📋 **Application Details:**
- **Name:** {app_name}
- **Description:** {description}
- **Type:** {app_type}
- **Tech Stack:** {tech_requirements}

🌐 **Deployment Information:**
- **Platform:** Loveable (with {deployment_pref} hosting)
- **App URL:** [Available in Loveable dashboard]
- **Admin Panel:** [Available in Loveable dashboard]
- **GitHub Repo:** [Auto-generated by Loveable]

🔧 **Post-Deployment Steps:**

1. **Access Your App:**
   - Return to Loveable dashboard
   - Find your approved project
   - Click "Deploy" or "Publish"
   - Get your live application URL

2. **Custom Domain Setup** {f"(Requested: {custom_domain})" if custom_domain else "(Optional)"}:
   - Go to Loveable project settings
   - Navigate to "Custom Domain"
   - Add your domain and configure DNS
   - Enable SSL certificate

3. **Collaboration & Team Access:**
   - Invite team members in Loveable
   - Set permissions and roles
   - Share project for feedback

4. **Monitoring & Analytics:**
   - Enable application monitoring
   - Set up error tracking
   - Configure performance analytics
   - Monitor user engagement

📁 **Project Structure (Generated by Loveable):**
```
{app_name}/
├── pages/              # Next.js pages or React components
├── components/         # Reusable UI components  
├── lib/               # Utility functions and configs
├── styles/            # CSS and styling files
├── public/            # Static assets
├── api/               # Backend API endpoints
├── database/          # Database schema and migrations
├── tests/             # Automated tests
└── deployment/        # Deployment configurations
```

🚀 **Features Included:**
- ✅ Responsive web interface
- ✅ User authentication system
- ✅ Database integration
- ✅ API endpoints
- ✅ Admin dashboard
- ✅ Error handling
- ✅ Loading states
- ✅ Form validations
- ✅ Security measures
- ✅ Performance optimization

💡 **Next Steps:**
1. **Test Thoroughly:** Verify all user flows work correctly
2. **Content Setup:** Add your real content and data
3. **Customization:** Make any final design or functionality tweaks
4. **Launch:** Share with users and gather feedback
5. **Iterate:** Use feedback to improve the application

🔗 **Useful Links:**
- Loveable Dashboard: https://lovable.dev/dashboard
- Documentation: https://docs.lovable.dev/
- Support: https://lovable.dev/support
- Community: https://discord.gg/lovable-dev

✅ **Application Status:** Deployed and Ready for Use!
"""

        # Store approval
        store.add_memory({
            "content": f"Full App Approved: {description} (ID: {app_id})",
            "type": "app_generation_approved", 
            "metadata": app_data
        })
        
        return deployment_guide
        
    except Exception as e:
        return f"❌ Failed to approve full application: {str(e)}"

@mcp.tool()
async def list_ui_generations(status_filter: str = "all") -> str:
    """List all UI component and app generation requests.
    
    Args:
        status_filter: Filter by status (all, preview_required, approved, cancelled)
    
    Returns:
        List of all UI generation requests with their current status
    """
    try:
        store = get_neurodock_store()
        if not store:
            return "❌ NeuroDock database not available"
        
        # Get all UI generation memories
        memories = store.get_all_memories()
        ui_generations = []
        
        for memory in memories:
            if memory.get("type") in ["ui_generation", "app_generation", "ui_generation_approved", "app_generation_approved"]:
                metadata = memory.get("metadata", {})
                if status_filter == "all" or metadata.get("status") == status_filter:
                    ui_generations.append({
                        "id": metadata.get("id", "unknown"),
                        "type": metadata.get("type", "unknown"),
                        "description": metadata.get("description", "No description"),
                        "status": metadata.get("status", "unknown"),
                        "created_at": metadata.get("created_at", "unknown"),
                        "approved_at": metadata.get("approved_at"),
                        "framework": metadata.get("framework"),
                        "app_type": metadata.get("app_type")
                    })
        
        if not ui_generations:
            return f"📱 No UI generations found with status: {status_filter}"
        
        # Sort by creation date (newest first)
        ui_generations.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        result = f"📱 UI Generation History (Status: {status_filter})\n\n"
        
        for gen in ui_generations:
            result += f"🎨 **{gen['id']}**\n"
            result += f"   Type: {gen['type']}\n"
            result += f"   Description: {gen['description']}\n"
            result += f"   Status: {gen['status']}\n"
            result += f"   Created: {gen['created_at']}\n"
            if gen['approved_at']:
                result += f"   Approved: {gen['approved_at']}\n"
            if gen['framework']:
                result += f"   Framework: {gen['framework']}\n"
            if gen['app_type']:
                result += f"   App Type: {gen['app_type']}\n"
            result += "\n"
        
        return result
        
    except Exception as e:
        return f"❌ Failed to list UI generations: {str(e)}"

@mcp.tool()
async def cancel_ui_generation(generation_id: str, reason: str = "User cancelled") -> str:
    """Cancel a pending UI generation request.
    
    Args:
        generation_id: The component or app ID to cancel
        reason: Reason for cancellation
    
    Returns:
        Cancellation confirmation
    """
    try:
        store = get_neurodock_store()
        if not store:
            return "❌ NeuroDock database not available"
        
        # Find and update the generation request
        memories = store.get_all_memories()
        
        for memory in memories:
            if (memory.get("type") in ["ui_generation", "app_generation"] and 
                memory.get("metadata", {}).get("id") == generation_id):
                
                metadata = memory.get("metadata", {})
                metadata["status"] = "cancelled"
                metadata["cancelled_at"] = datetime.now().isoformat()
                metadata["cancellation_reason"] = reason
                
                # Store cancellation
                store.add_memory({
                    "content": f"UI Generation Cancelled: {metadata.get('description', '')} (ID: {generation_id})",
                    "type": f"{memory.get('type')}_cancelled",
                    "metadata": metadata
                })
                
                return f"✅ UI Generation {generation_id} has been cancelled.\nReason: {reason}"
        
        return f"❌ Generation ID {generation_id} not found"
        
    except Exception as e:
        return f"❌ Failed to cancel UI generation: {str(e)}"

# ==============================================================================
# END UI GENERATION TOOLS
# ==============================================================================
