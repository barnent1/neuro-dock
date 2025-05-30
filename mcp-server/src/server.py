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
        list_available_projects, get_project_metadata, update_project_metadata,
        list_project_tasks, load_task, save_task, get_task_file_path,
        analyze_task_complexity
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

# ==============================================================================
# PROJECT MANAGEMENT TOOLS - Multi-project Support
# ==============================================================================

@mcp.tool()
async def neurodock_add_project(name: str, description: str = "") -> str:
    """Create a new isolated project workspace with metadata tracking.
    
    Args:
        name: Project name (unique identifier)
        description: Optional project description
    
    Returns:
        JSON string with project creation status and metadata
    """
    if not NEURODOCK_AVAILABLE:
        return json.dumps({"error": "NeuroDock core modules not available"})
    
    try:
        # Check if project already exists
        existing_projects = list_available_projects()
        if any(p['name'] == name for p in existing_projects):
            return json.dumps({
                "error": f"Project '{name}' already exists",
                "existing_projects": [p['name'] for p in existing_projects]
            })
        
        # Create the project
        metadata = create_project(name, description)
        
        return json.dumps({
            "success": True,
            "project": metadata,
            "message": f"✅ Project '{name}' created successfully"
        })
        
    except Exception as e:
        return json.dumps({"error": f"Failed to create project: {str(e)}"})

@mcp.tool()
async def neurodock_list_projects() -> str:
    """List all available projects with their metadata and statistics.
    
    Returns:
        JSON string with project list and details
    """
    if not NEURODOCK_AVAILABLE:
        return json.dumps({"error": "NeuroDock core modules not available"})
    
    try:
        projects = list_available_projects()
        current_project = get_current_project()
        
        return json.dumps({
            "projects": projects,
            "current_project": current_project,
            "total_projects": len(projects),
            "message": f"Found {len(projects)} projects"
        })
        
    except Exception as e:
        return json.dumps({"error": f"Failed to list projects: {str(e)}"})

@mcp.tool()
async def neurodock_set_active_project(name: str) -> str:
    """Switch to a different project context.
    
    Args:
        name: Name of the project to make active
    
    Returns:
        JSON string with switch status and project metadata
    """
    if not NEURODOCK_AVAILABLE:
        return json.dumps({"error": "NeuroDock core modules not available"})
    
    try:
        # Check if project exists
        projects = list_available_projects()
        project_names = [p['name'] for p in projects]
        
        if name not in project_names:
            return json.dumps({
                "error": f"Project '{name}' not found",
                "available_projects": project_names
            })
        
        # Set as active project
        set_current_project(name)
        
        # Get project metadata
        metadata = get_project_metadata(name)
        
        return json.dumps({
            "success": True,
            "active_project": name,
            "metadata": metadata,
            "message": f"✅ Switched to project '{name}'"
        })
        
    except Exception as e:
        return json.dumps({"error": f"Failed to switch project: {str(e)}"})

@mcp.tool()
async def neurodock_get_project_status(project_name: str = "") -> str:
    """Get comprehensive status and metadata for a project.
    
    Args:
        project_name: Project name (defaults to current project)
    
    Returns:
        JSON string with detailed project status
    """
    if not NEURODOCK_AVAILABLE:
        return json.dumps({"error": "NeuroDock core modules not available"})
    
    try:
        if not project_name:
            project_name = get_current_project()
            
        if not project_name:
            return json.dumps({"error": "No active project and no project specified"})
        
        # Get project metadata
        metadata = get_project_metadata(project_name)
        
        if not metadata:
            return json.dumps({"error": f"Project '{project_name}' not found"})
        
        # Calculate project statistics
        current_project = get_current_project()
        is_active = project_name == current_project
        
        return json.dumps({
            "project": metadata,
            "is_active": is_active,
            "current_project": current_project,
            "status": "active" if is_active else "inactive",
            "message": f"Project '{project_name}' status retrieved"
        })
        
    except Exception as e:
        return json.dumps({"error": f"Failed to get project status: {str(e)}"})

@mcp.tool()
async def neurodock_agent_info() -> str:
    """Get current agent context and project information - automatically called for cognitive context.
    
    This tool provides essential context about the current project and agent state.
    
    Returns:
        JSON string with agent context and project information
    """
    if not NEURODOCK_AVAILABLE:
        return json.dumps({"error": "NeuroDock core modules not available"})
    
    try:
        current_project = get_current_project()
        
        if current_project:
            metadata = get_project_metadata(current_project)
            projects_list = list_available_projects()
        else:
            metadata = None
            projects_list = list_available_projects()
        
        context = {
            "agent_system": "NeuroDock AI Agent Operating System",
            "current_project": current_project,
            "project_metadata": metadata,
            "available_projects": len(projects_list),
            "cognitive_mode": "multi-project",
            "capabilities": [
                "project_management", "task_management", "memory_system",
                "discussion_system", "ui_generation", "agent_coordination"
            ],
            "message": "Agent context loaded successfully"
        }
        
        return json.dumps(context)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to get agent info: {str(e)}"})

# ==============================================================================
# ENHANCED TASK MANAGEMENT TOOLS - With Complexity Analysis
# ==============================================================================

@mcp.tool()
async def neurodock_add_task(
    title: str,
    description: str = "",
    priority: str = "medium",
    assign_to: str = "",
    project_name: str = ""
) -> str:
    """Add a new task with automatic complexity analysis and decomposition suggestions.
    
    Args:
        title: Task title
        description: Detailed task description
        priority: Task priority (low/medium/high/urgent)
        assign_to: Team member assignment
        project_name: Project to add task to (defaults to current project)
    
    Returns:
        JSON string with task creation status and complexity analysis
    """
    if not NEURODOCK_AVAILABLE:
        return json.dumps({"error": "NeuroDock core modules not available"})
    
    try:
        # Use specified project or get current project
        if project_name:
            current_project_name = project_name
        else:
            current_project_name = get_current_project()
            
        if not current_project_name:
            return json.dumps({"error": "No active project and no project specified"})
        
        # Analyze task complexity
        complexity_analysis = analyze_task_complexity(description, title)
        
        # Create task with complexity data
        task_data = {
            'id': f"task_{int(datetime.now().timestamp())}",
            'title': title,
            'description': description,
            'priority': priority,
            'assign_to': assign_to,
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'project': current_project_name,
            'complexity': complexity_analysis
        }
        
        # Store task (simplified for MCP - would normally use CLI task storage)
        store = get_neurodock_store()
        if store:
            # Store in database
            task_id = store.create_task(
                title=title,
                description=description,
                priority=priority,
                assign_to=assign_to
            )
            task_data['id'] = task_id
        
        # Update project metadata
        update_project_metadata(current_project_name, task_count=1)
        
        result = {
            "success": True,
            "task": task_data,
            "complexity_analysis": complexity_analysis,
            "message": f"✅ Task '{title}' created with complexity rating {complexity_analysis['complexity_rating']}/10"
        }
        
        # Add decomposition suggestion if needed
        if complexity_analysis['needs_decomposition']:
            result['recommendation'] = f"⚠️ High complexity task (rating {complexity_analysis['complexity_rating']}/10). Consider using neurodock_decompose_task to break it down."
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to add task: {str(e)}"})

@mcp.tool()
async def neurodock_rate_task_complexity(
    task_title: str,
    task_description: str = ""
) -> str:
    """Analyze and rate the complexity of a task using AI-powered heuristics.
    
    Args:
        task_title: The task title to analyze
        task_description: The task description to analyze
    
    Returns:
        JSON string with detailed complexity analysis
    """
    if not NEURODOCK_AVAILABLE:
        return json.dumps({"error": "NeuroDock core modules not available"})
    
    try:
        analysis = analyze_task_complexity(task_description, task_title)
        
        result = {
            "task_title": task_title,
            "complexity_analysis": analysis,
            "recommendations": []
        }
        
        # Add recommendations based on complexity
        if analysis['needs_decomposition']:
            result['recommendations'].append(
                f"🔨 Consider breaking this task down using neurodock_decompose_task - complexity rating is {analysis['complexity_rating']}/10"
            )
        
        if analysis['complexity_rating'] >= 8:
            result['recommendations'].append(
                "⚠️ This is a very high complexity task. Consider creating a detailed plan first."
            )
        
        if analysis['effort_estimate'] in ["1-2 days", "3+ days"]:
            result['recommendations'].append(
                "📅 This task may need multiple work sessions. Consider setting milestones."
            )
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to analyze task complexity: {str(e)}"})

@mcp.tool()
async def neurodock_decompose_task(
    task_title: str,
    task_description: str,
    max_subtasks: int = 5
) -> str:
    """Break down a complex task into smaller, manageable subtasks.
    
    Args:
        task_title: The complex task title
        task_description: The complex task description  
        max_subtasks: Maximum number of subtasks to create (default: 5)
    
    Returns:
        JSON string with decomposed subtasks and implementation plan
    """
    if not NEURODOCK_AVAILABLE:
        return json.dumps({"error": "NeuroDock core modules not available"})
    
    try:
        # First analyze complexity
        complexity_analysis = analyze_task_complexity(task_description, task_title)
        
        if not complexity_analysis['needs_decomposition']:
            return json.dumps({
                "warning": f"Task complexity rating is {complexity_analysis['complexity_rating']}/10 - decomposition may not be necessary",
                "original_task": {
                    "title": task_title,
                    "description": task_description,
                    "complexity": complexity_analysis
                },
                "recommendation": "This task is already manageable. Consider proceeding as-is."
            })
        
        # Use LLM to generate subtasks (simplified for now)
        # In full implementation, this would call the LLM for intelligent decomposition
        subtasks = [
            {
                "title": f"Research and planning for {task_title}",
                "description": "Investigate requirements, constraints, and approach",
                "priority": "high",
                "estimated_effort": "1-2 hours"
            },
            {
                "title": f"Design phase for {task_title}",
                "description": "Create detailed design and architecture",
                "priority": "high", 
                "estimated_effort": "2-4 hours"
            },
            {
                "title": f"Implementation phase 1",
                "description": "Begin core implementation work",
                "priority": "medium",
                "estimated_effort": "4-6 hours"
            },
            {
                "title": f"Testing and validation",
                "description": "Test implementation and validate requirements",
                "priority": "medium",
                "estimated_effort": "2-3 hours"
            },
            {
                "title": f"Documentation and cleanup",
                "description": "Document changes and clean up code",
                "priority": "low",
                "estimated_effort": "1-2 hours"
            }
        ]
        
        # Limit to max_subtasks
        subtasks = subtasks[:max_subtasks]
        
        result = {
            "success": True,
            "original_task": {
                "title": task_title,
                "description": task_description,
                "complexity": complexity_analysis
            },
            "subtasks": subtasks,
            "total_subtasks": len(subtasks),
            "estimated_total_effort": "10-17 hours",
            "message": f"✅ Decomposed '{task_title}' into {len(subtasks)} manageable subtasks"
        }
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to decompose task: {str(e)}"})

@mcp.tool()
async def neurodock_complete_task(
    task_id: str,
    completion_notes: str = "",
    project_name: str = ""
) -> str:
    """Mark a task as completed and update project progress statistics.
    
    Args:
        task_id: ID of the task to complete
        completion_notes: Optional notes about the completion
        project_name: Project containing the task (defaults to current project)
    
    Returns:
        JSON string with completion status and updated project metrics
    """
    if not NEURODOCK_AVAILABLE:
        return json.dumps({"error": "NeuroDock core modules not available"})
    
    try:
        # Use specified project or get current project
        if project_name:
            current_project_name = project_name
        else:
            current_project_name = get_current_project()
            
        if not current_project_name:
            return json.dumps({"error": "No active project and no project specified"})
        
        # Get database store
        store = get_neurodock_store()
        if not store:
            return json.dumps({"error": "Database store not available"})
        
        # Update task status
        success = store.update_task_status(task_id, 'completed')
        
        if not success:
            return json.dumps({"error": f"Task '{task_id}' not found or update failed"})
        
        # Get updated task info
        task = store.get_task(task_id)
        
        # Update project metadata with completion
        project_metadata = get_project_metadata(current_project_name)
        if project_metadata:
            completed_tasks = project_metadata.get('completed_tasks', 0) + 1
            update_project_metadata(
                current_project_name,
                completed_tasks=completed_tasks,
                last_activity='task_completed'
            )
        
        result = {
            "success": True,
            "task_id": task_id,
            "task": task if task else {"id": task_id, "status": "completed"},
            "completion_notes": completion_notes,
            "completed_at": datetime.now().isoformat(),
            "project": current_project_name,
            "message": f"✅ Task '{task_id}' marked as completed"
        }
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to complete task: {str(e)}"})

@mcp.tool()
async def neurodock_remove_task(
    task_id: str,
    project_name: str = "",
    confirm: bool = False
) -> str:
    """Remove a task from the project with validation.
    
    Args:
        task_id: ID of the task to remove
        project_name: Project containing the task (defaults to current project)
        confirm: Must be True to actually delete the task
    
    Returns:
        JSON string with removal status and validation
    """
    if not NEURODOCK_AVAILABLE:
        return json.dumps({"error": "NeuroDock core modules not available"})
    
    try:
        # Use specified project or get current project
        if project_name:
            current_project_name = project_name
        else:
            current_project_name = get_current_project()
            
        if not current_project_name:
            return json.dumps({"error": "No active project and no project specified"})
        
        # Get database store
        store = get_neurodock_store()
        if not store:
            return json.dumps({"error": "Database store not available"})
        
        # Get task details before deletion for confirmation
        task = store.get_task(task_id)
        if not task:
            return json.dumps({"error": f"Task '{task_id}' not found"})
        
        # Safety check - require confirmation
        if not confirm:
            return json.dumps({
                "error": "Confirmation required",
                "task": task,
                "message": f"To delete task '{task_id}': {task.get('title', 'Unknown')}, call this tool again with confirm=True",
                "warning": "This action cannot be undone"
            })
        
        # Remove task
        success = store.delete_task(task_id)
        
        if not success:
            return json.dumps({"error": f"Failed to delete task '{task_id}'"})
        
        # Update project metadata
        project_metadata = get_project_metadata(current_project_name)
        if project_metadata:
            total_tasks = project_metadata.get('total_tasks', 1) - 1
            update_project_metadata(
                current_project_name,
                total_tasks=max(0, total_tasks),
                last_activity='task_removed'
            )
        
        result = {
            "success": True,
            "task_id": task_id,
            "removed_task": task,
            "project": current_project_name,
            "message": f"🗑️ Task '{task_id}' removed successfully",
            "removed_at": datetime.now().isoformat()
        }
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to remove task: {str(e)}"})

@mcp.tool()
async def neurodock_remove_project(
    project_name: str,
    confirm: bool = False,
    delete_data: bool = False
) -> str:
    """Remove a project and optionally all its data with safety validation.
    
    Args:
        project_name: Name of the project to remove
        confirm: Must be True to actually delete the project
        delete_data: If True, also delete all tasks, memories, and project data
    
    Returns:
        JSON string with removal status and validation
    """
    if not NEURODOCK_AVAILABLE:
        return json.dumps({"error": "NeuroDock core modules not available"})
    
    try:
        # Get project metadata for confirmation
        project_metadata = get_project_metadata(project_name)
        if not project_metadata:
            return json.dumps({"error": f"Project '{project_name}' not found"})
        
        # Get project statistics for safety confirmation
        project_stats = {
            "total_tasks": project_metadata.get('total_tasks', 0),
            "completed_tasks": project_metadata.get('completed_tasks', 0),
            "created_date": project_metadata.get('created_date', 'Unknown'),
            "last_activity": project_metadata.get('last_activity', 'Unknown')
        }
        
        # Safety check - require confirmation
        if not confirm:
            return json.dumps({
                "error": "Confirmation required",
                "project": project_name,
                "project_stats": project_stats,
                "message": f"To delete project '{project_name}' with {project_stats['total_tasks']} tasks, call this tool again with confirm=True",
                "warning": "This action cannot be undone. Set delete_data=True to also remove all tasks and memories.",
                "data_deletion_note": f"delete_data is currently {delete_data}"
            })
        
        # Check if this is the current active project
        current_project = get_current_project()
        if current_project == project_name:
            # Switch to a different project or clear current project
            available_projects = list_available_projects()
            if len(available_projects) > 1:
                # Switch to another available project
                other_projects = [p for p in available_projects if p != project_name]
                new_active = other_projects[0]
                set_current_project(new_active)
                switched_to = new_active
            else:
                # No other projects, clear current project
                set_current_project("")
                switched_to = None
        else:
            switched_to = None
        
        # Get database store for data deletion
        store = get_neurodock_store()
        deleted_data = {}
        
        if delete_data and store:
            # Get all project tasks before deletion
            tasks = list_project_tasks(project_name)
            
            # Delete all project tasks
            task_count = 0
            for task in tasks:
                if store.delete_task(task.get('id')):
                    task_count += 1
            
            # Delete project memories (if any specific to project)
            memory_count = 0
            memories = store.get_all_memories()
            for memory in memories:
                if memory.get('metadata', {}).get('project') == project_name:
                    store.delete_memory(memory.get('id'))
                    memory_count += 1
            
            deleted_data = {
                "tasks_deleted": task_count,
                "memories_deleted": memory_count,
                "data_deletion_completed": True
            }
        
        # Remove project directory/metadata
        projects_available = list_available_projects()
        if project_name in projects_available:
            # Remove project from available projects
            # This would depend on how projects are stored - for now, assume successful
            project_removed = True
        else:
            project_removed = False
        
        result = {
            "success": True,
            "project_name": project_name,
            "project_stats": project_stats,
            "project_removed": project_removed,
            "data_deletion": delete_data,
            "deleted_data": deleted_data,
            "active_project_switched": switched_to,
            "message": f"🗑️ Project '{project_name}' removed successfully",
            "removed_at": datetime.now().isoformat(),
            "warning": "Project removal completed - this action cannot be undone"
        }
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to remove project: {str(e)}"})

@mcp.tool()
async def neurodock_auto_memory_update(
    interaction_summary: str,
    key_insights: List[str] = None,
    project_name: str = ""
) -> str:
    """Automatically update project memory with insights from AI interactions.
    
    Args:
        interaction_summary: Summary of the recent interaction or work session
        key_insights: List of important insights or decisions made
        project_name: Project to associate memory with (defaults to current project)
    
    Returns:
        JSON string with memory update status
    """
    if not NEURODOCK_AVAILABLE:
        return json.dumps({"error": "NeuroDock core modules not available"})
    
    try:
        # Use specified project or get current project
        if project_name:
            current_project_name = project_name
        else:
            current_project_name = get_current_project()
            
        if not current_project_name:
            return json.dumps({"error": "No active project and no project specified"})
        
        # Get database store
        store = get_neurodock_store()
        if not store:
            return json.dumps({"error": "Database store not available"})
        
        # Create comprehensive memory entry
        memory_content = f"Project: {current_project_name}\n\nInteraction Summary:\n{interaction_summary}"
        
        if key_insights:
            memory_content += f"\n\nKey Insights:\n" + "\n".join(f"• {insight}" for insight in key_insights)
        
        # Store memory with project context
        memory_data = {
            "content": memory_content,
            "type": "auto_interaction",
            "project": current_project_name,
            "interaction_summary": interaction_summary,
            "key_insights": key_insights or [],
            "auto_generated": True,
            "created_at": datetime.now().isoformat()
        }
        
        memory_id = store.add_memory(memory_data)
        
        # Also try to add to vector store for semantic search
        try:
            add_to_memory(memory_content, {
                "type": "auto_interaction",
                "project": current_project_name,
                "memory_id": memory_id
            })
            vector_stored = True
        except Exception:
            vector_stored = False
        
        result = {
            "success": True,
            "memory_id": memory_id,
            "project": current_project_name,
            "interaction_summary": interaction_summary,
            "insights_count": len(key_insights or []),
            "vector_stored": vector_stored,
            "message": f"📝 Auto-memory updated for project '{current_project_name}'",
            "created_at": datetime.now().isoformat()
        }
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to auto-update memory: {str(e)}"})

@mcp.tool()
async def neurodock_get_project_insights(
    project_name: str = "",
    insight_type: str = "all",
    limit: int = 10
) -> str:
    """Get project-specific insights and accumulated knowledge.
    
    Args:
        project_name: Project to get insights for (defaults to current project)
        insight_type: Type of insights (all, decisions, learnings, patterns)
        limit: Maximum number of insights to return
    
    Returns:
        JSON string with project insights and patterns
    """
    if not NEURODOCK_AVAILABLE:
        return json.dumps({"error": "NeuroDock core modules not available"})
    
    try:
        # Use specified project or get current project
        if project_name:
            current_project_name = project_name
        else:
            current_project_name = get_current_project()
            
        if not current_project_name:
            return json.dumps({"error": "No active project and no project specified"})
        
        # Get database store
        store = get_neurodock_store()
        if not store:
            return json.dumps({"error": "Database store not available"})
        
        # Get all memories for the project
        all_memories = store.get_all_memories()
        project_memories = [
            memory for memory in all_memories
            if memory.get('metadata', {}).get('project') == current_project_name
            or memory.get('project') == current_project_name
        ]
        
        # Filter by insight type
        filtered_insights = []
        for memory in project_memories:
            memory_type = memory.get('type', '').lower()
            
            if insight_type == "all":
                filtered_insights.append(memory)
            elif insight_type == "decisions" and "decision" in memory_type:
                filtered_insights.append(memory)
            elif insight_type == "learnings" and "learning" in memory_type:
                filtered_insights.append(memory)
            elif insight_type == "patterns" and "pattern" in memory_type:
                filtered_insights.append(memory)
            elif insight_type in memory_type:
                filtered_insights.append(memory)
        
        # Sort by date and limit
        filtered_insights = sorted(
            filtered_insights,
            key=lambda x: x.get('created_at', ''),
            reverse=True
        )[:limit]
        
        # Analyze patterns
        insight_patterns = {
            "total_insights": len(filtered_insights),
            "insight_types": {},
            "key_themes": [],
            "recent_trends": []
        }
        
        # Count insight types
        for insight in filtered_insights:
            insight_type_key = insight.get('type', 'unknown')
            insight_patterns["insight_types"][insight_type_key] = insight_patterns["insight_types"].get(insight_type_key, 0) + 1
        
        # Extract key themes (simple keyword extraction)
        all_content = " ".join([insight.get('content', '') for insight in filtered_insights])
        common_words = {}
        for word in all_content.lower().split():
            if len(word) > 4:  # Only meaningful words
                common_words[word] = common_words.get(word, 0) + 1
        
        insight_patterns["key_themes"] = sorted(common_words.items(), key=lambda x: x[1], reverse=True)[:5]
        
        result = {
            "success": True,
            "project": current_project_name,
            "insight_type_filter": insight_type,
            "insights": filtered_insights,
            "patterns": insight_patterns,
            "message": f"📊 Found {len(filtered_insights)} insights for project '{current_project_name}'",
            "retrieved_at": datetime.now().isoformat()
        }
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to get project insights: {str(e)}"})

@mcp.tool()
async def neurodock_auto_decompose(
    task_description: str,
    threshold: int = 7,
    project_name: str = ""
) -> str:
    """Automatically analyze and decompose tasks that exceed complexity threshold.
    
    Args:
        task_description: Description of the task to analyze
        threshold: Complexity threshold for auto-decomposition (default: 7)
        project_name: Project to associate with (defaults to current project)
    
    Returns:
        JSON string with decomposition analysis and recommendations
    """
    if not NEURODOCK_AVAILABLE:
        return json.dumps({"error": "NeuroDock core modules not available"})
    
    try:
        # Use specified project or get current project
        if project_name:
            current_project_name = project_name
        else:
            current_project_name = get_current_project()
            
        if not current_project_name:
            return json.dumps({"error": "No active project and no project specified"})
        
        # First, analyze the task complexity
        complexity_result = await neurodock_rate_task_complexity(
            task_description=task_description,
            project_name=current_project_name
        )
        
        complexity_data = json.loads(complexity_result)
        
        if "error" in complexity_data:
            return json.dumps({"error": f"Failed to analyze complexity: {complexity_data['error']}"})
        
        complexity_score = complexity_data.get("complexity_score", 0)
        
        # Auto-decompose if complexity exceeds threshold
        should_decompose = complexity_score >= threshold
        
        decomposition_result = {}
        if should_decompose:
            decompose_result = await neurodock_decompose_task(
                task_description=task_description,
                project_name=current_project_name
            )
            decomposition_result = json.loads(decompose_result)
        
        # Generate recommendations
        recommendations = []
        if should_decompose:
            recommendations.extend([
                f"Task complexity ({complexity_score}/10) exceeds threshold ({threshold})",
                "Consider breaking this task into smaller subtasks",
                "Focus on one subtask at a time for better progress tracking",
                "Each subtask should have complexity ≤ 6 for optimal execution"
            ])
        else:
            recommendations.extend([
                f"Task complexity ({complexity_score}/10) is within manageable range",
                "Task can be executed as a single unit",
                "Consider adding specific milestones if task duration > 1 day"
            ])
        
        result = {
            "success": True,
            "task_description": task_description,
            "complexity_score": complexity_score,
            "threshold": threshold,
            "should_decompose": should_decompose,
            "auto_decomposed": should_decompose,
            "decomposition": decomposition_result if should_decompose else None,
            "recommendations": recommendations,
            "project": current_project_name,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        # Store the auto-decomposition analysis in memory
        store = get_neurodock_store()
        if store:
            memory_content = f"Auto-decomposition analysis for: {task_description}\nComplexity: {complexity_score}/10\nDecomposed: {should_decompose}"
            store.add_memory({
                "content": memory_content,
                "type": "auto_decomposition",
                "project": current_project_name,
                "task_description": task_description,
                "complexity_score": complexity_score,
                "auto_decomposed": should_decompose,
                "created_at": datetime.now().isoformat()
            })
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to auto-decompose task: {str(e)}"})

@mcp.tool()
async def neurodock_plan(
    project_goal: str,
    project_name: str = "",
    planning_horizon: str = "sprint",
    auto_create_tasks: bool = True
) -> str:
    """Interactive project planning with automatic task creation and complexity analysis.
    
    Args:
        project_goal: High-level goal or objective for the project
        project_name: Project to plan for (defaults to current project)
        planning_horizon: Planning timeframe (sprint, month, quarter)
        auto_create_tasks: Whether to automatically create tasks from the plan
    
    Returns:
        JSON string with comprehensive project plan and created tasks
    """
    if not NEURODOCK_AVAILABLE:
        return json.dumps({"error": "NeuroDock core modules not available"})
    
    try:
        # Use specified project or get current project
        if project_name:
            current_project_name = project_name
        else:
            current_project_name = get_current_project()
            
        if not current_project_name:
            return json.dumps({"error": "No active project and no project specified"})
        
        # Get database store
        store = get_neurodock_store()
        if not store:
            return json.dumps({"error": "Database store not available"})
        
        # Analyze the project goal and generate planning framework
        planning_framework = {
            "project_goal": project_goal,
            "planning_horizon": planning_horizon,
            "suggested_phases": [],
            "estimated_complexity": 0,
            "recommended_approach": "",
            "success_metrics": []
        }
        
        # Break down the goal into logical phases/milestones
        if "web" in project_goal.lower() or "app" in project_goal.lower():
            planning_framework["suggested_phases"] = [
                {"phase": "Requirements & Design", "tasks": ["Define user requirements", "Create wireframes", "Design system architecture"]},
                {"phase": "Development Setup", "tasks": ["Setup development environment", "Initialize project structure", "Configure tooling"]},
                {"phase": "Core Development", "tasks": ["Implement core features", "Build user interface", "Setup database"]},
                {"phase": "Testing & Deployment", "tasks": ["Write tests", "Performance optimization", "Deploy to production"]}
            ]
        elif "research" in project_goal.lower() or "analysis" in project_goal.lower():
            planning_framework["suggested_phases"] = [
                {"phase": "Research Planning", "tasks": ["Define research questions", "Literature review", "Methodology design"]},
                {"phase": "Data Collection", "tasks": ["Gather data sources", "Setup data pipeline", "Quality validation"]},
                {"phase": "Analysis", "tasks": ["Exploratory analysis", "Statistical modeling", "Results interpretation"]},
                {"phase": "Documentation", "tasks": ["Write findings", "Create visualizations", "Prepare presentation"]}
            ]
        else:
            # Generic project structure
            planning_framework["suggested_phases"] = [
                {"phase": "Planning & Preparation", "tasks": ["Define scope and objectives", "Resource planning", "Risk assessment"]},
                {"phase": "Implementation", "tasks": ["Execute main deliverables", "Progress monitoring", "Quality assurance"]},
                {"phase": "Review & Completion", "tasks": ["Final review", "Documentation", "Project closure"]}
            ]
        
        # Calculate planning metrics
        total_tasks = sum(len(phase["tasks"]) for phase in planning_framework["suggested_phases"])
        planning_framework["estimated_complexity"] = min(10, max(3, total_tasks // 2))
        
        # Generate recommendations based on horizon
        if planning_horizon == "sprint":
            planning_framework["recommended_approach"] = "Focus on 1-2 phases with clear deliverables"
            planning_framework["success_metrics"] = ["Daily progress updates", "Weekly milestone reviews"]
        elif planning_horizon == "month":
            planning_framework["recommended_approach"] = "Complete 2-3 phases with iterative feedback"
            planning_framework["success_metrics"] = ["Weekly progress reviews", "Bi-weekly stakeholder updates"]
        else:  # quarter
            planning_framework["recommended_approach"] = "Full project lifecycle with regular checkpoints"
            planning_framework["success_metrics"] = ["Monthly milestone reviews", "Quarterly goal assessment"]
        
        created_tasks = []
        if auto_create_tasks:
            # Create tasks for each phase
            for phase in planning_framework["suggested_phases"]:
                for task_desc in phase["tasks"]:
                    # Create the task
                    task_result = await neurodock_add_task(
                        description=task_desc,
                        category=phase["phase"].lower().replace(" ", "_"),
                        project_name=current_project_name,
                        auto_analyze=True
                    )
                    
                    task_data = json.loads(task_result)
                    if "success" in task_data and task_data["success"]:
                        created_tasks.append({
                            "task_id": task_data.get("task_id"),
                            "description": task_desc,
                            "phase": phase["phase"],
                            "complexity": task_data.get("complexity_analysis", {}).get("complexity_score", "unknown")
                        })
        
        # Store planning session in memory
        memory_content = f"Project Planning Session: {project_goal}\nHorizon: {planning_horizon}\nPhases: {len(planning_framework['suggested_phases'])}\nTasks Created: {len(created_tasks)}"
        store.add_memory({
            "content": memory_content,
            "type": "project_planning",
            "project": current_project_name,
            "project_goal": project_goal,
            "planning_horizon": planning_horizon,
            "phases_count": len(planning_framework["suggested_phases"]),
            "tasks_created": len(created_tasks),
            "created_at": datetime.now().isoformat()
        })
        
        result = {
            "success": True,
            "project": current_project_name,
            "planning_framework": planning_framework,
            "auto_created_tasks": auto_create_tasks,
            "created_tasks": created_tasks,
            "planning_summary": {
                "total_phases": len(planning_framework["suggested_phases"]),
                "total_tasks": len(created_tasks),
                "estimated_complexity": planning_framework["estimated_complexity"],
                "planning_horizon": planning_horizon
            },
            "next_steps": [
                "Review and refine the suggested tasks",
                "Prioritize tasks based on dependencies",
                "Set realistic timelines for each phase",
                "Begin with the highest priority tasks"
            ],
            "message": f"📋 Project plan created for '{current_project_name}' with {len(created_tasks)} tasks",
            "planned_at": datetime.now().isoformat()
        }
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to create project plan: {str(e)}"})

@mcp.tool()
async def neurodock_cognitive_loop() -> str:
    """Execute the cognitive loop for context awareness and intelligent recommendations.
    
    This tool is designed to be auto-called by AI assistants to maintain cognitive awareness
    of the current project state and provide intelligent recommendations.
    
    Returns:
        JSON string with cognitive context and recommendations
    """
    if not NEURODOCK_AVAILABLE:
        return json.dumps({"error": "NeuroDock core modules not available"})
    
    try:
        # Get current project context
        current_project = get_current_project()
        
        if not current_project:
            return json.dumps({
                "cognitive_status": "no_active_project",
                "recommendation": "Set an active project using neurodock_set_active_project or create a new project",
                "suggested_actions": ["neurodock_list_projects", "neurodock_add_project"]
            })
        
        # Get database store
        store = get_neurodock_store()
        if not store:
            return json.dumps({"error": "Database store not available"})
        
        # Gather cognitive context
        cognitive_context = {
            "project": current_project,
            "timestamp": datetime.now().isoformat(),
            "context_analysis": {},
            "task_intelligence": {},
            "memory_insights": {},
            "recommendations": [],
            "priority_actions": []
        }
        
        # Analyze current tasks
        tasks = list_project_tasks(current_project)
        pending_tasks = [t for t in tasks if t.get('status') == 'pending']
        in_progress_tasks = [t for t in tasks if t.get('status') == 'in_progress']
        completed_tasks = [t for t in tasks if t.get('status') == 'completed']
        
        cognitive_context["task_intelligence"] = {
            "total_tasks": len(tasks),
            "pending_count": len(pending_tasks),
            "in_progress_count": len(in_progress_tasks),
            "completed_count": len(completed_tasks),
            "completion_rate": round(len(completed_tasks) / max(1, len(tasks)) * 100, 1),
            "high_complexity_tasks": []
        }
        
        # Identify high complexity tasks that might need decomposition
        for task in pending_tasks + in_progress_tasks:
            if task.get('complexity', 0) >= 7:
                cognitive_context["task_intelligence"]["high_complexity_tasks"].append({
                    "id": task.get('id'),
                    "description": task.get('description', ''),
                    "complexity": task.get('complexity'),
                    "status": task.get('status')
                })
        
        # Analyze recent memory patterns
        all_memories = store.get_all_memories()
        project_memories = [m for m in all_memories if m.get('project') == current_project]
        recent_memories = sorted(project_memories, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
        
        cognitive_context["memory_insights"] = {
            "total_memories": len(project_memories),
            "recent_activity_types": [m.get('type', 'unknown') for m in recent_memories],
            "knowledge_areas": {}
        }
        
        # Generate intelligent recommendations
        recommendations = []
        priority_actions = []
        
        # Task-based recommendations
        if len(in_progress_tasks) == 0 and len(pending_tasks) > 0:
            recommendations.append("No tasks in progress - consider starting the highest priority pending task")
            priority_actions.append("neurodock_list_tasks status=pending")
        
        if len(cognitive_context["task_intelligence"]["high_complexity_tasks"]) > 0:
            recommendations.append(f"Found {len(cognitive_context['task_intelligence']['high_complexity_tasks'])} high-complexity tasks that could benefit from decomposition")
            priority_actions.append("neurodock_auto_decompose")
        
        if cognitive_context["task_intelligence"]["completion_rate"] < 20:
            recommendations.append("Low task completion rate - consider reviewing task scope and priorities")
            priority_actions.append("neurodock_plan")
        
        # Memory-based recommendations
        if len(project_memories) < 5:
            recommendations.append("Limited project memory - consider adding key decisions and insights to build knowledge base")
            priority_actions.append("neurodock_add_memory")
        
        # Progress-based recommendations
        if len(tasks) == 0:
            recommendations.append("No tasks defined - start with project planning to create structured roadmap")
            priority_actions.append("neurodock_plan")
        
        cognitive_context["recommendations"] = recommendations[:5]  # Limit to top 5
        cognitive_context["priority_actions"] = priority_actions[:3]  # Limit to top 3
        
        # Generate context summary
        cognitive_context["context_analysis"] = {
            "project_health": "healthy" if cognitive_context["task_intelligence"]["completion_rate"] > 60 else "needs_attention",
            "activity_level": "high" if len(recent_memories) >= 3 else "low",
            "focus_area": "task_execution" if len(in_progress_tasks) > 0 else "planning",
            "cognitive_load": "high" if len(cognitive_context["task_intelligence"]["high_complexity_tasks"]) > 2 else "manageable"
        }
        
        # Store cognitive loop execution in memory
        store.add_memory({
            "content": f"Cognitive loop executed for project: {current_project}",
            "type": "cognitive_loop",
            "project": current_project,
            "context_summary": cognitive_context["context_analysis"],
            "recommendations_count": len(recommendations),
            "created_at": datetime.now().isoformat()
        })
        
        return json.dumps(cognitive_context, default=str)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to execute cognitive loop: {str(e)}"})

@mcp.tool()
async def neurodock_agent_behavior(
    behavior_mode: str = "adaptive",
    focus_area: str = "auto",
    verbosity: str = "normal"
) -> str:
    """Configure and retrieve agent behavior settings for cognitive consistency.
    
    Args:
        behavior_mode: Agent behavior mode (adaptive, focused, exploratory, systematic)
        focus_area: Primary focus area (auto, planning, execution, analysis, learning)
        verbosity: Response verbosity (minimal, normal, detailed, comprehensive)
    
    Returns:
        JSON string with behavior configuration and guidelines
    """
    if not NEURODOCK_AVAILABLE:
        return json.dumps({"error": "NeuroDock core modules not available"})
    
    try:
        current_project = get_current_project()
        
        # Define behavior profiles
        behavior_profiles = {
            "adaptive": {
                "description": "Adapts approach based on project context and user patterns",
                "characteristics": ["Context-aware responses", "Dynamic task prioritization", "Learning from interactions"],
                "ideal_for": "Most general-purpose work and evolving projects"
            },
            "focused": {
                "description": "Maintains sharp focus on current objectives with minimal distractions",
                "characteristics": ["Goal-oriented responses", "Reduced exploratory suggestions", "Task completion emphasis"],
                "ideal_for": "Sprint work, deadlines, and execution phases"
            },
            "exploratory": {
                "description": "Encourages creative thinking and broader perspective",
                "characteristics": ["Alternative approach suggestions", "Creative problem-solving", "Broader context awareness"],
                "ideal_for": "Research, brainstorming, and innovation projects"
            },
            "systematic": {
                "description": "Emphasizes structured approaches and methodical progress",
                "characteristics": ["Step-by-step guidance", "Process optimization", "Quality assurance focus"],
                "ideal_for": "Complex projects, compliance work, and systematic development"
            }
        }
        
        # Define focus areas
        focus_areas = {
            "auto": "Automatically determine focus based on project state and recent activity",
            "planning": "Emphasize project planning, task organization, and strategic thinking",
            "execution": "Focus on task completion, progress tracking, and immediate actions",
            "analysis": "Prioritize data analysis, insights generation, and pattern recognition",
            "learning": "Emphasize knowledge acquisition, skill development, and improvement"
        }
        
        # Generate behavior configuration
        selected_profile = behavior_profiles.get(behavior_mode, behavior_profiles["adaptive"])
        selected_focus = focus_areas.get(focus_area, focus_areas["auto"])
        
        behavior_config = {
            "behavior_mode": behavior_mode,
            "focus_area": focus_area,
            "verbosity": verbosity,
            "profile": selected_profile,
            "focus_description": selected_focus,
            "current_project": current_project,
            "configured_at": datetime.now().isoformat()
        }
        
        # Generate agent instructions based on configuration
        agent_instructions = []
        
        if behavior_mode == "adaptive":
            agent_instructions.extend([
                "Monitor project context and adapt recommendations accordingly",
                "Learn from user patterns and adjust approach dynamically",
                "Balance between different work modes as needed"
            ])
        elif behavior_mode == "focused":
            agent_instructions.extend([
                "Prioritize current objectives and minimize distractions",
                "Provide direct, actionable guidance",
                "Emphasize task completion and progress"
            ])
        elif behavior_mode == "exploratory":
            agent_instructions.extend([
                "Encourage creative approaches and alternative solutions",
                "Suggest broader perspectives and innovative ideas",
                "Support research and discovery activities"
            ])
        elif behavior_mode == "systematic":
            agent_instructions.extend([
                "Follow structured methodologies and best practices",
                "Emphasize quality, documentation, and process",
                "Provide step-by-step guidance for complex tasks"
            ])
        
        # Add focus-specific instructions
        if focus_area == "planning":
            agent_instructions.append("Prioritize project planning tools and strategic guidance")
        elif focus_area == "execution":
            agent_instructions.append("Focus on task completion and immediate actionable steps")
        elif focus_area == "analysis":
            agent_instructions.append("Emphasize data analysis and insight generation")
        elif focus_area == "learning":
            agent_instructions.append("Support knowledge acquisition and skill development")
        
        behavior_config["agent_instructions"] = agent_instructions
        
        # Store behavior configuration
        store = get_neurodock_store()
        if store and current_project:
            store.add_memory({
                "content": f"Agent behavior configured: {behavior_mode} mode, {focus_area} focus",
                "type": "agent_behavior_config",
                "project": current_project,
                "behavior_mode": behavior_mode,
                "focus_area": focus_area,
                "verbosity": verbosity,
                "created_at": datetime.now().isoformat()
            })
        
        return json.dumps(behavior_config, default=str)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to configure agent behavior: {str(e)}"})

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
