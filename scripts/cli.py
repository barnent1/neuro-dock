#!/usr/bin/env python3
"""
NeuroDock CLI - Command Line Interface for interacting with NeuroDock.
"""
import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import typer
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown

# Add the parent directory to sys.path
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

app = typer.Typer(name="neurodock", help="NeuroDock CLI - Memory and Task Management for AI Agents")
console = Console()

# Base URL for API
API_URL = os.getenv("NEURODOCK_API_URL", "http://localhost:4000")


def api_request(method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Make an API request to the NeuroDock server.
    """
    url = f"{API_URL}{endpoint}"
    
    try:
        with httpx.Client(timeout=30.0) as client:
            if method.lower() == "get":
                response = client.get(url)
            elif method.lower() == "post":
                response = client.post(url, json=data)
            elif method.lower() == "put":
                response = client.put(url, json=data)
            elif method.lower() == "delete":
                response = client.delete(url)
            else:
                console.print(f"[bold red]Unknown HTTP method: {method}[/bold red]")
                sys.exit(1)
                
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPStatusError as e:
        console.print(f"[bold red]HTTP Error: {e.response.status_code} - {e.response.text}[/bold red]")
        sys.exit(1)
    except httpx.RequestError as e:
        console.print(f"[bold red]Request Error: {e}[/bold red]")
        console.print(f"[yellow]Is the NeuroDock server running at {API_URL}?[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        sys.exit(1)


@app.command("health")
def check_health():
    """
    Check the health of the NeuroDock server.
    """
    with console.status("[bold green]Checking NeuroDock server health..."):
        response = api_request("get", "/health")
    
    status = response.get("status")
    agent_status = response.get("agent_status", "unknown")
    
    if status == "ok":
        console.print("[bold green]NeuroDock server is healthy! 🚀[/bold green]")
        console.print(f"Agent status: {agent_status}")
    else:
        console.print("[bold red]NeuroDock server is not healthy![/bold red]")


@app.command("add-memory")
def add_memory(
    content: str = typer.Argument(..., help="Content of the memory"),
    type: str = typer.Option("normal", help="Type of memory (important, normal, trivial, code, etc.)"),
    source: str = typer.Option("cli", help="Source of the memory")
):
    """
    Add a new memory to NeuroDock.
    """
    data = {
        "content": content,
        "type": type,
        "source": source
    }
    
    with console.status("[bold green]Adding memory to NeuroDock..."):
        response = api_request("post", "/memory", data)
    
    console.print("[bold green]Memory added successfully![/bold green]")
    console.print(f"Memory ID: {response.get('id')}")


@app.command("search-memories")
def search_memories(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, help="Maximum number of results to return"),
    memory_type: Optional[str] = typer.Option(None, help="Filter by memory type")
):
    """
    Search for memories in NeuroDock.
    """
    # Build the endpoint
    endpoint = f"/memory/search/{query}?limit={limit}"
    if memory_type:
        endpoint += f"&memory_type={memory_type}"
    
    with console.status(f"[bold green]Searching for '{query}'..."):
        response = api_request("get", endpoint)
    
    # Create a table to display results
    table = Table(title=f"Search Results for '{query}'")
    table.add_column("ID", style="dim")
    table.add_column("Type", style="cyan")
    table.add_column("Content")
    table.add_column("Source", style="green")
    
    for memory in response:
        table.add_row(
            str(memory.get("id")),
            memory.get("type"),
            memory.get("content")[:100] + ("..." if len(memory.get("content", "")) > 100 else ""),
            memory.get("source")
        )
    
    console.print(table)


@app.command("add-task")
def add_task(
    title: str = typer.Argument(..., help="Title of the task"),
    description: str = typer.Option("", help="Description of the task"),
    priority: int = typer.Option(3, help="Priority (1-8, higher is more important)"),
    parent_id: Optional[str] = typer.Option(None, help="Parent task ID (if this is a subtask)")
):
    """
    Add a new task to NeuroDock.
    """
    data = {
        "title": title,
        "description": description,
        "priority": priority
    }
    
    if parent_id:
        data["parent_id"] = parent_id
    
    with console.status("[bold green]Adding task to NeuroDock..."):
        response = api_request("post", "/task", data)
    
    console.print("[bold green]Task added successfully![/bold green]")
    console.print(f"Task ID: {response.get('id')}")
    console.print(f"Title: {response.get('title')}")


@app.command("get-pending-tasks")
def get_pending_tasks(
    limit: int = typer.Option(10, help="Maximum number of tasks to return")
):
    """
    Get pending tasks from NeuroDock.
    """
    with console.status("[bold green]Fetching pending tasks..."):
        response = api_request("get", f"/task?limit={limit}")
    
    # Create a table to display results
    table = Table(title="Pending Tasks")
    table.add_column("ID", style="dim")
    table.add_column("Title")
    table.add_column("Priority", style="cyan")
    table.add_column("Status", style="green")
    
    for task in response:
        table.add_row(
            str(task.get("id")),
            task.get("title"),
            str(task.get("priority")),
            task.get("status")
        )
    
    console.print(table)


@app.command("get-task-details")
def get_task_details(
    task_id: str = typer.Argument(..., help="ID of the task to display")
):
    """
    Get details of a specific task.
    """
    with console.status(f"[bold green]Fetching details for task {task_id}..."):
        task = api_request("get", f"/task/{task_id}")
    
    # Display task details in a panel
    md_content = f"""
    # {task.get('title')}
    
    **Status:** {task.get('status')}  
    **Priority:** {task.get('priority')}  
    **Created:** {task.get('created_at')}  
    **Updated:** {task.get('updated_at')}
    
    ## Description
    {task.get('description', 'No description provided.')}
    """
    
    console.print(Panel(Markdown(md_content), title=f"Task {task_id}", border_style="green"))
    
    # Fetch and display subtasks if any
    try:
        subtasks = api_request("get", f"/task/{task_id}/subtasks")
        
        if subtasks:
            subtask_table = Table(title="Subtasks")
            subtask_table.add_column("ID", style="dim")
            subtask_table.add_column("Title")
            subtask_table.add_column("Status", style="green")
            
            for subtask in subtasks:
                subtask_table.add_row(
                    str(subtask.get("id")),
                    subtask.get("title"),
                    subtask.get("status")
                )
            
            console.print(subtask_table)
    except:
        # Silently ignore errors in fetching subtasks
        pass


@app.command("context")
def get_context(
    query: str = typer.Argument(..., help="Query to get context for"),
    max_memories: int = typer.Option(10, help="Maximum number of memories to return")
):
    """
    Get relevant context for a query.
    """
    data = {
        "query": query,
        "max_memories": max_memories
    }
    
    with console.status(f"[bold green]Fetching context for '{query}'..."):
        response = api_request("post", "/mcp/context", data)
    
    context_items = response.get("context", [])
    console.print(f"[bold green]Found {len(context_items)} relevant context items:[/bold green]")
    
    for item in context_items:
        console.print(Panel(
            item.get("content"),
            title=f"[{item.get('type')}] {item.get('source')} - {item.get('timestamp')}",
            border_style="cyan"
        ))


# Add a new command to initialize a project
@app.command("init")
def init_project(
    project_path: str = typer.Argument(".", help="Path to the project directory (defaults to current directory)"),
    name: Optional[str] = typer.Option(None, help="Project name (defaults to directory name)"),
    description: Optional[str] = typer.Option(None, help="Project description")
):
    """
    Initialize a project with a neurodock.json configuration file.
    """
    import sys
    sys.path.append(parent_dir)
    
    from app.services.project_settings import ProjectSettings
    
    # Expand and normalize path
    project_path = os.path.abspath(os.path.expanduser(project_path))
    
    # Check if directory exists
    if not os.path.isdir(project_path):
        console.print(f"[bold red]Error: Directory {project_path} does not exist[/bold red]")
        sys.exit(1)
    
    # Check if neurodock.json already exists
    config_path = os.path.join(project_path, "neurodock.json")
    if os.path.exists(config_path):
        overwrite = typer.confirm(f"neurodock.json already exists in {project_path}. Overwrite?", default=False)
        if not overwrite:
            console.print("[yellow]Operation cancelled[/yellow]")
            return
    
    # Get project name if not provided
    if not name:
        name = os.path.basename(project_path)
    
    # Create default config with some customizations
    config = {
        "project_id": name.lower().replace(" ", "_"),
        "name": name,
        "description": description or f"NeuroDock configuration for {name}",
        "memory_isolation_level": "strict",
        "memory_ttl_days": 90,
        "task_auto_creation": True,
        "agent_enabled": True,
        "excluded_paths": [
            "node_modules",
            "dist",
            "build",
            ".git",
            "__pycache__",
            "*.pyc"
        ],
        "memory_types": {
            "code": True,
            "documentation": True,
            "comment": True,
            "important": True,
            "normal": True,
            "trivial": False
        }
    }
    
    # Write config to file
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        console.print(f"[bold green]Initialized NeuroDock project in {project_path}[/bold green]")
        console.print(f"Project ID: {config['project_id']}")
        console.print(f"Project Name: {config['name']}")
        console.print("Memory isolation: strict (project memories won't mix with other projects)")
    except Exception as e:
        console.print(f"[bold red]Error creating neurodock.json: {str(e)}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    app()
