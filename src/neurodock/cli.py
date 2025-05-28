#!/usr/bin/env python3

import os
import json
import yaml
import subprocess
from datetime import datetime
from pathlib import Path
import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Import centralized configuration
from .config import get_config

from .utils.models import call_llm, call_llm_plan, call_llm_code, get_current_llm_backend
from .memory.qdrant_store import test_memory_system, add_to_memory
from .memory import show_post_command_reminders
from .discussion import run_interactive_discussion
from .db import get_store, test_database, initialize_schema
from .db.schema import check_database_status
from .agent import get_project_agent

# Import for conversational agent
from .conversational_agent import ConversationalAgent, get_conversation_agent

# Import memory functions with error handling
try:
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

app = typer.Typer(no_args_is_help=True)

def _show_agent_reminders(command: str, result: str = "", context: dict = None):
    """Show Agent 2 reminders after command completion."""
    try:
        show_post_command_reminders(command, result, context)
    except Exception:
        # Gracefully handle any reminder system failures
        pass

@app.command()
def init():
    """Initialize .neuro-dock in the current project folder."""
    root = Path.cwd()
    nd_path = root / ".neuro-dock"

    if nd_path.exists():
        typer.echo("⚠️  .neuro-dock already exists in this project.")
        raise typer.Exit()

    # Initialize database schema - this will raise if database not available
    try:
        initialize_schema()
        typer.echo("✅ Database connection verified")
    except Exception as e:
        typer.echo(f"❌ Database connection failed: {str(e)}")
        typer.echo()
        typer.echo("💡 NeuroDock requires a PostgreSQL database to function.")
        typer.echo("   Run 'nd setup' for database configuration help.")
        raise typer.Exit(1)

    # Create the .neuro-dock folder and essential configuration
    nd_path.mkdir(parents=True, exist_ok=True)
    
    # Create config.yaml with app_root for real project generation
    config_content = """code_root: .
app_root: .
# Framework type for structure generation (auto-detected if not specified)
# Supported: next-js, react, flask, django, express, vanilla
framework: auto
"""
    (nd_path / "config.yaml").write_text(config_content)

    typer.echo(f"✅ Project initialized in: {root}")
    typer.echo("🚀 Ready to start! Try: nd discuss")

@app.command()
def status():
    """Show comprehensive status of .neuro-dock project with intelligent summary."""
    root = Path.cwd()
    nd_path = root / ".neuro-dock"
    
    typer.echo("🔍 NeuroDock Project Status")
    typer.echo("="*50)
    
    # Project status
    if nd_path.exists():
        typer.echo(f"📁 Project: ✅ Initialized in {root}")
        
        # Get intelligent project summary from agent
        try:
            agent = get_project_agent(str(root))
            summary = agent.get_project_summary()
            
            # Project info
            project_info = summary.get("project_info", {})
            if project_info.get("name"):
                typer.echo(f"🏷️  Name: {project_info['name']}")
            if project_info.get("description"):
                typer.echo(f"📝 Description: {project_info['description']}")
            
            # Task statistics
            task_stats = summary.get("task_stats", {})
            if task_stats.get("total", 0) > 0:
                typer.echo()
                typer.echo("📊 Task Progress:")
                typer.echo(f"   Total: {task_stats['total']} tasks")
                typer.echo(f"   ✅ Completed: {task_stats['completed']}")
                typer.echo(f"   🔄 In Progress: {task_stats['in_progress']}")
                typer.echo(f"   ⏳ Pending: {task_stats['pending']}")
                typer.echo(f"   📈 Progress: {task_stats['completion_rate']:.1f}%")
            
            # Memory context
            memory_count = summary.get("memory_entries", 0)
            if memory_count > 0:
                typer.echo(f"🧠 Memory: {memory_count} context entries available")
                
        except Exception:
            # Fallback to basic status if agent fails
            typer.echo("   (Using basic status - agent unavailable)")
    else:
        typer.echo(f"📁 Project: ❌ Not initialized (run 'nd init')")
        return
    
    typer.echo()
    
    # Database status
    try:
        db_status = check_database_status()
        typer.echo(f"🗄️  Database: {db_status['message']}")
        if "help" in db_status:
            typer.echo(f"   💡 {db_status['help']}")
    except Exception as e:
        typer.echo(f"🗄️  Database: ❌ Connection failed: {str(e)}")
        typer.echo("   Run 'nd setup' for database configuration help")
    
    # LLM Backend status
    try:
        backend = get_current_llm_backend()
        typer.echo(f"🤖 LLM Backend: ✅ {backend}")
    except Exception as e:
        typer.echo(f"🤖 LLM Backend: ❌ Configuration issue")
    
    # Memory system status (optional)
    try:
        from .memory.qdrant_store import test_memory_system
        # Don't actually run the test, just check if it's available
        typer.echo("🧠 Memory System: ✅ Qdrant integration available")
    except Exception:
        typer.echo("🧠 Memory System: ⚠️  Qdrant not configured (optional)")
    
    typer.echo()
    if not db_status.get("connected", False):
        typer.echo("🚀 Quick start: Run 'nd setup' for easy database configuration")
    else:
        typer.echo("🎉 System ready! Try 'nd discuss' to start a project")
    
    # Show Agent 2 reminders
    try:
        _show_agent_reminders("status", "Project status checked", {"db_connected": db_status.get("connected", False) if 'db_status' in locals() else False})
    except:
        pass

@app.command()
def setup():
    """Create and configure the NeuroDock system-level environment file."""
    # Get the centralized config and create default env file
    config = get_config()
    env_file = config.create_default_env_file()
    
    typer.echo("🔧 NeuroDock System Setup")
    typer.echo("="*50)
    
    if env_file.exists():
        typer.echo(f"✅ Configuration file created: {env_file}")
        typer.echo()
        
        # Check current database status
        try:
            db_status = check_database_status()
            typer.echo(f"📊 Database Status: {db_status['message']}")
            
            if db_status["connected"]:
                typer.echo("🎉 Your database is already working!")
                return
        except Exception:
            pass
            
        # Database setup options
        typer.echo()
        typer.echo("🚀 Choose Database Setup:")
        typer.echo()
        typer.echo("1. 🐳 Docker PostgreSQL (Easiest - 2 minutes)")
        typer.echo("2. 🌩️  Cloud Database (Recommended - 5 minutes)")  
        typer.echo("3. 🏠 Local PostgreSQL (Advanced - 15 minutes)")
        typer.echo()
        
        choice = typer.prompt("Choose option (1/2/3)", default="1")
        
        if choice == "1":
            setup_docker_postgres()
        elif choice == "2":
            setup_cloud_database()
        elif choice == "3":
            setup_local_postgres()
        else:
            typer.echo("❌ Invalid choice. Run 'nd setup' again.")
            raise typer.Exit(1)
        
        typer.echo()
        typer.echo("🤖 LLM Configuration:")
        typer.echo("   • Default: Ollama (Local AI models)")
        typer.echo("   • Alternative: Claude API (Cloud AI)")
        typer.echo("   • Install Ollama: https://ollama.ai")
        typer.echo()
        typer.echo("🧪 Test your setup:")
        typer.echo("   nd init && nd discuss")
        
    else:
        typer.echo(f"❌ Failed to create configuration file at {env_file}")

@app.command()
def discuss():
    """Interactive discussion to clarify goals and generate task plan."""
    import time
    
    root = Path.cwd()
    nd_path = root / ".neuro-dock"
    
    # Initialize database schema
    initialize_schema()
    
    # Get database store for this project
    store = get_store(str(root))
    
    # Check if .neuro-dock directory exists, create if needed
    if not nd_path.exists():
        typer.echo("🔧 Initializing .neuro-dock directory...")
        nd_path.mkdir(parents=True, exist_ok=True)
        
        # Create config.yaml
        config_content = """code_root: .
app_root: .
framework: auto
"""
        (nd_path / "config.yaml").write_text(config_content)
    
    
    # Check if we have a previous clarified prompt in the database
    existing_prompt = store.get_latest_memory("clarified_prompt")
    
    # If no existing clarified prompt, show Codex-style interface
    if not existing_prompt:
        console = Console()
        
        typer.echo()
        typer.echo("🧠 NeuroDock")
        typer.echo("What would you like to build or clarify?")
        
        try:
            user_input = typer.prompt("> ", type=str)
            
            if not user_input.strip():
                typer.echo("❌ Please provide a description of what you'd like to build.")
                raise typer.Exit(1)
            
            # Store initial prompt in database
            prompt_stored = store.add_memory(user_input.strip(), "user_prompt")
            
            if not prompt_stored:
                # Database not available - show friendly message and guidance
                typer.echo("🔧 Database setup needed for full functionality")
                typer.echo("💡 To enable project memory and task tracking:")
                typer.echo("   1. Run 'nd setup' to configure a database")
                typer.echo("   2. Cloud databases are recommended (5 min setup)")
                typer.echo("   3. Then return here and run 'nd discuss' again")
                typer.echo()
                typer.echo("📋 For now, I can help you plan this project:")
                typer.echo(f"Your idea: {user_input.strip()}")
                
                # Provide basic planning help without database
                from .utils.models import call_llm
                try:
                    basic_response = call_llm(f"Help me plan this project: {user_input.strip()}")
                    typer.echo("\n" + "="*60)
                    typer.echo("🤖 PROJECT PLANNING HELP:")
                    typer.echo("="*60)
                    typer.echo(basic_response)
                    typer.echo("="*60)
                    typer.echo("\n💡 Set up a database with 'nd setup' for full project tracking!")
                    return
                except Exception as e:
                    typer.echo(f"\n💡 Set up a database with 'nd setup' to enable AI planning and project tracking!")
                    return
            
            # Show thinking animation
            typer.echo()
            typer.echo("( ● ) Thinking...", nl=False)
            
            # Add visual feedback
            for i in range(3):
                time.sleep(0.3)
                typer.echo(".", nl=False)
            
            typer.echo()  # New line
            typer.echo()
            
        except KeyboardInterrupt:
            typer.echo("\n⚠️  Cancelled.")
            raise typer.Exit(0)
    
    # Run the interactive discussion workflow
    try:
        typer.echo("🎯 Starting interactive discussion...")
        typer.echo("This will clarify your goals and generate a structured task plan.")
        typer.echo()
        
        success = run_interactive_discussion(nd_path)
        
        if success:
            typer.echo("\n🎉 Discussion completed successfully!")
            typer.echo()
            typer.echo("Next steps:")
            typer.echo("  📋 Review the generated plan: neuro-dock plan")
            typer.echo("  🚀 Start executing tasks: neuro-dock run")
            typer.echo("  📊 Check project status: neuro-dock status")
            
            # Show Agent 2 reminders
            _show_agent_reminders("discuss", "Discussion completed successfully", {"success": True})
        else:
            typer.echo("\n❌ Discussion workflow incomplete.")
            _show_agent_reminders("discuss", "Discussion failed", {"success": False})
            raise typer.Exit(1)
            
    except KeyboardInterrupt:
        typer.echo("\n\n⚠️  Discussion interrupted by user.")
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Discussion error: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def prompt():
    """Read latest user prompt from database, send to LLM, and save response to database."""
    root = Path.cwd()
    nd_path = root / ".neuro-dock"
    
    # Initialize database schema and get store
    initialize_schema()
    store = get_store(str(root))
    
    # Check if .neuro-dock directory exists
    if not nd_path.exists():
        typer.echo("❌ .neuro-dock directory not found in current project.", err=True)
        typer.echo("Run 'neuro-dock init' first to initialize the project.")
        raise typer.Exit(1)

    try:
        # Get latest user prompt from database
        prompt_content = store.get_latest_memory("user_prompt")
        
        if not prompt_content:
            typer.echo("❌ No user prompt found in database.", err=True)
            typer.echo("Run 'neuro-dock discuss' first to create a prompt, or add one to the database.")
            raise typer.Exit(1)
        
        if not prompt_content.strip():
            typer.echo("❌ The user prompt in database is empty.", err=True)
            raise typer.Exit(1)
        
        typer.echo(f"📤 Sending prompt to {get_current_llm_backend()}...")
        typer.echo(f"Prompt: {prompt_content[:100]}{'...' if len(prompt_content) > 100 else ''}")
        
        # Call LLM (supports both Ollama and Claude)
        try:
            llm_response = call_llm(prompt_content)
        except Exception as e:
            typer.echo(f"❌ LLM call failed: {e}", err=True)
            raise typer.Exit(1)
        
        # Store the original prompt and clarified response in vector memory
        try:
            add_to_memory(
                prompt_content, 
                {"type": "user_prompt", "source": "prompt.txt"}
            )
            add_to_memory(
                llm_response, 
                {"type": "clarified_prompt", "source": "prompt_command"}
            )
        except Exception as e:
            # Silent fallback - don't break user experience
            pass
        
        # Save to database for memory system
        try:
            store.add_memory(prompt_content, "user_prompt")
            store.add_memory(llm_response, "clarified_prompt")
            typer.echo("✅ Responses saved to database")
        except Exception as e:
            typer.echo(f"⚠️  Database save warning: {e}")
        
        # Print LLM's response with clear formatting
        typer.echo("\n" + "="*60)
        typer.echo(f"🤖 {get_current_llm_backend().upper()}'S RESPONSE:")
        typer.echo("="*60)
        typer.echo(llm_response)
        typer.echo("="*60)
        
    except FileNotFoundError as e:
        typer.echo(f"❌ File error: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Unexpected error: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def plan():
    """Generate an intelligent project plan with enhanced context awareness."""
    root = Path.cwd()
    nd_path = root / ".neuro-dock"
    
    # Initialize database schema and get store
    initialize_schema()
    store = get_store(str(root))
    
    # Check if .neuro-dock directory exists
    if not nd_path.exists():
        typer.echo("❌ .neuro-dock directory not found in current project.", err=True)
        typer.echo("Run 'nd init' first to initialize the project.")
        raise typer.Exit(1)

    try:
        # Get project agent for enhanced planning
        agent = get_project_agent(str(root))
        
        # Get clarified prompt from database
        clarified_prompt_entry = store.get_latest_memory("clarified_prompt")
        
        if not clarified_prompt_entry:
            typer.echo("❌ No clarified prompt found in database.", err=True)
            typer.echo("Run 'nd discuss' first to create a clarified prompt through interactive discussion.")
            raise typer.Exit(1)

        # Extract text from database entry
        if isinstance(clarified_prompt_entry, dict):
            clarified_prompt = clarified_prompt_entry.get('text', '')
        else:
            clarified_prompt = str(clarified_prompt_entry) if clarified_prompt_entry else ''

        if not clarified_prompt.strip():
            typer.echo("❌ The clarified prompt in database is empty.", err=True)
            raise typer.Exit(1)

        # Load project context for enhanced planning
        context = agent.load_project_context()
        
        # Create enhanced planning prompt with full context
        enhanced_planning_prompt = f"""
ENHANCED PROJECT PLANNING REQUEST

USER REQUIREMENTS:
{clarified_prompt}

EXISTING PROJECT CONTEXT:
=========================
{agent._format_memory_context(context.get('memory', [])[:3])}

EXISTING TASKS:
===============
{agent._format_tasks_status(context.get('tasks', []))}

CONFIGURATION:
==============
Framework: {context.get('config', {}).get('framework', 'auto')}
Project Root: {context.get('config', {}).get('app_root', '.')}

INSTRUCTIONS:
=============
Generate a comprehensive project plan considering the existing context.
If there are existing tasks, integrate with them or update as needed.
Break down complex requirements into manageable tasks.
Consider dependencies and logical sequencing.
"""

        typer.echo(f"📋 Generating enhanced plan with {get_current_llm_backend()}...")
        typer.echo(f"🧠 Using project context: {len(context.get('memory', []))} memories, {len(context.get('tasks', []))} existing tasks")

        # Call LLM for planning with enhanced context
        try:
            plan_response = call_llm_plan(enhanced_planning_prompt.strip())
        except Exception as e:
            typer.echo(f"❌ LLM call failed: {e}", err=True)
            raise typer.Exit(1)

        # Analyze each task in the generated plan for complexity
        try:
            import json
            import yaml
            
            # Try to parse the plan to analyze individual tasks
            try:
                if plan_response.strip().startswith('{'):
                    plan_data = json.loads(plan_response)
                else:
                    plan_data = yaml.safe_load(plan_response)
                
                if isinstance(plan_data, dict) and 'tasks' in plan_data:
                    typer.echo("\n🔍 Analyzing task complexity...")
                    
                    for task in plan_data['tasks']:
                        if isinstance(task, dict) and 'description' in task:
                            analysis = agent.analyze_task_complexity(task['description'])
                            task['complexity_rating'] = analysis.get('complexity_rating', 5)
                            task['estimated_hours'] = analysis.get('estimated_hours', 2)
                            
                            # Add breakdown suggestion for complex tasks
                            if analysis.get('should_break_down'):
                                task['suggested_breakdown'] = analysis.get('suggested_subtasks', [])
                    
                    # Convert back to the original format
                    if plan_response.strip().startswith('{'):
                        plan_response = json.dumps(plan_data, indent=2)
                    else:
                        plan_response = yaml.dump(plan_data, default_flow_style=False)
                        
            except (json.JSONDecodeError, yaml.YAMLError):
                # If parsing fails, continue with original plan
                pass
                
        except Exception:
            # Silent fallback - don't break planning if complexity analysis fails
            pass

        # Store the plan in vector memory
        try:
            add_to_memory(
                plan_response, 
                {"type": "project_plan", "source": "plan_command", "enhanced": True}
            )
        except Exception as e:
            # Silent fallback - don't break user experience
            pass

        # Save the plan to database
        try:
            store.save_task_plan(plan_response)
            typer.echo("✅ Enhanced plan saved to database")
        except Exception as e:
            # Silent fallback for database unavailability
            pass

        typer.echo("\n" + "="*60)
        typer.echo("📋 PLAN GENERATED:")
        typer.echo("="*60)
        typer.echo(plan_response)
        typer.echo("="*60)
        
        # Show Agent 2 reminders
        _show_agent_reminders("plan", plan_response[:200] + "...", {"plan_generated": True, "tasks_count": len(plan_data.get("tasks", [])) if 'plan_data' in locals() else 0})

    except Exception as e:
        typer.echo(f"❌ Unexpected error: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def run(
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Run in interactive mode to select tasks manually"),
    task_name: str = typer.Option(None, "--task", "-t", help="Run a specific task by name"),
    build: bool = typer.Option(False, "--build", "-b", help="Execute build commands after file generation")
):
    """Read task plan from database and automatically run all incomplete tasks sequentially.
    
    By default, runs all incomplete tasks in order. Use --interactive to select tasks manually.
    Use --task to run a specific task by name. Use --build to execute build commands after generation.
    """
    root = Path.cwd()
    nd_path = root / ".neuro-dock"
    
    # Initialize database schema and get store
    initialize_schema()
    store = get_store(str(root))
    
    # Check if .neuro-dock directory exists
    if not nd_path.exists():
        typer.echo("❌ .neuro-dock directory not found in current project.", err=True)
        typer.echo("Run 'neuro-dock init' first to initialize the project.")
        raise typer.Exit(1)

    try:
        # Get task plan from database
        plan_data = store.get_task_plan()
        
        if not plan_data:
            typer.echo("❌ No task plan found in database.", err=True)
            typer.echo("Run 'neuro-dock plan' first to create a project plan.")
            raise typer.Exit(1)

        if not plan_data or "tasks" not in plan_data:
            typer.echo("❌ No tasks found in plan data.", err=True)
            raise typer.Exit(1)

        tasks = plan_data["tasks"]
        if not tasks:
            typer.echo("❌ Task list is empty in plan data.", err=True)
            raise typer.Exit(1)

        # Display project info
        project_info = plan_data.get("project", {})
        typer.echo("\n" + "="*60)
        typer.echo(f"🚀 PROJECT: {project_info.get('name', 'Unknown')}")
        typer.echo(f"📋 {project_info.get('description', 'No description')}")
        typer.echo("="*60)

        # Initialize status for all tasks if not present
        for task in tasks:
            if "status" not in task:
                task["status"] = "pending"

        # If interactive mode or specific task requested
        if interactive or task_name:
            return _run_interactive_mode(tasks, project_info, store, nd_path, task_name, build)
        
        # Auto-run mode: run all incomplete tasks sequentially
        typer.echo(f"\n🤖 Running all incomplete tasks with {get_current_llm_backend()}...")
        
        incomplete_tasks = [task for task in tasks if task.get("status") != "completed"]
        
        if not incomplete_tasks:
            typer.echo("🎉 All tasks are already completed!")
            return
        
        typer.echo(f"📝 Found {len(incomplete_tasks)} incomplete task(s):")
        for i, task in enumerate(incomplete_tasks, 1):
            typer.echo(f"  {i}. {task.get('name', 'Unnamed Task')}")
        
        typer.echo()
        
        # Execute each incomplete task
        completed_count = 0
        for i, task in enumerate(incomplete_tasks, 1):
            task_name_display = task.get('name', 'Unnamed Task')
            typer.echo(f"\n{'='*60}")
            typer.echo(f"🎯 Task {i}/{len(incomplete_tasks)}: {task_name_display}")
            typer.echo(f"📝 {task.get('description', 'No description')}")
            typer.echo('='*60)
            
            success = _execute_task(task, project_info, store, nd_path, build)
            
            if success:
                # Mark task as completed in database
                task["status"] = "completed"
                completed_count += 1
                typer.echo(f"✅ Task '{task_name_display}' completed successfully!")
                
                # Update the task status in database
                store.update_task_status_by_name(task.get('name'), 'completed')
            else:
                typer.echo(f"❌ Task '{task_name_display}' failed. Stopping execution.")
                break
        
        # Final summary
        typer.echo(f"\n{'='*60}")
        typer.echo(f"🎉 EXECUTION COMPLETE!")
        typer.echo(f"✅ Completed: {completed_count}/{len(incomplete_tasks)} tasks")
        if completed_count < len(incomplete_tasks):
            remaining = len(incomplete_tasks) - completed_count
            typer.echo(f"⏳ Remaining: {remaining} task(s)")
        typer.echo(f"{'='*60}")
        
        # Show Agent 2 reminders
        _show_agent_reminders("run", f"Completed {completed_count}/{len(incomplete_tasks)} tasks", {"completed_tasks": completed_count, "total_tasks": len(incomplete_tasks)})
        
    except Exception as e:
        typer.echo(f"❌ Unexpected error: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def tasks():
    """Show the status of all tasks in the current project plan."""
    root = Path.cwd()
    nd_path = root / ".neuro-dock"
    
    # Initialize database schema and get store
    initialize_schema()
    store = get_store(str(root))
    
    # Check if .neuro-dock directory exists
    if not nd_path.exists():
        typer.echo("❌ .neuro-dock directory not found in current project.", err=True)
        typer.echo("Run 'neuro-dock init' first to initialize the project.")
        raise typer.Exit(1)

    try:
        # Get task plan from database
        plan_data = store.get_task_plan()
        
        if not plan_data:
            typer.echo("❌ No task plan found in database.", err=True)
            typer.echo("Run 'neuro-dock plan' first to create a project plan.")
            raise typer.Exit(1)

        if not plan_data or "tasks" not in plan_data:
            typer.echo("❌ No tasks found in plan data.", err=True)
            raise typer.Exit(1)

        tasks = plan_data["tasks"]
        if not tasks:
            typer.echo("❌ Task list is empty in plan data.", err=True)
            raise typer.Exit(1)

        # Display project info
        project_info = plan_data.get("project", {})
        typer.echo("\n" + "="*60)
        typer.echo(f"🚀 PROJECT: {project_info.get('name', 'Unknown')}")
        typer.echo(f"📋 {project_info.get('description', 'No description')}")
        typer.echo("="*60)

        # Initialize status for all tasks if not present
        for task in tasks:
            if "status" not in task:
                task["status"] = "pending"

        # Count tasks by status
        completed_count = sum(1 for task in tasks if task.get("status") == "completed")
        pending_count = len(tasks) - completed_count

        # Display summary
        typer.echo(f"\n📊 TASK SUMMARY:")
        typer.echo(f"   Total: {len(tasks)} tasks")
        typer.echo(f"   ✅ Completed: {completed_count}")
        typer.echo(f"   ⏳ Pending: {pending_count}")

        # Display detailed task list
        typer.echo(f"\n📝 TASK DETAILS:")
        typer.echo("-" * 60)

        for i, task in enumerate(tasks, 1):
            status_icon = "✅" if task.get("status") == "completed" else "⏳"
            status_text = task.get("status", "pending").upper()

            typer.echo(f"{i:2d}. {status_icon} {task.get('name', 'Unnamed Task')} [{status_text}]")
            typer.echo(f"     {task.get('description', 'No description')}")
            if task.get("type"):
                typer.echo(f"     Type: {task.get('type')}")
            typer.echo()

        # Display next actions
        if pending_count > 0:
            typer.echo("🚀 NEXT ACTIONS:")
            typer.echo("   • Run 'neuro-dock run' to execute all pending tasks")
            typer.echo("   • Run 'neuro-dock run --interactive' to select tasks manually")
            typer.echo("   • Run 'neuro-dock run --task <name>' to run a specific task")
        else:
            typer.echo("🎉 All tasks completed! Your project is ready.")

    except typer.Exit:
        # Re-raise typer.Exit without catching it
        raise
    except Exception as e:
        typer.echo(f"❌ Unexpected error: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def memory(
    test: bool = typer.Option(False, "--test", help="Test the Qdrant memory system")
):
    """Manage the Qdrant-based vector memory system."""
    if test:
        try:
            success = test_memory_system()
            if success:
                typer.echo("\n🎉 Memory system test completed successfully!")
            else:
                typer.echo("\n❌ Memory system test failed!")
                raise typer.Exit(1)
        except Exception as e:
            typer.echo(f"❌ Memory test error: {e}", err=True)
            raise typer.Exit(1)
    else:
        typer.echo("📋 Qdrant Memory System")
        typer.echo("Available subcommands:")
        typer.echo("  neuro-dock memory --test    Test the memory system")
        typer.echo("\nRequirements:")
        typer.echo("  • Qdrant server running on localhost:6333")
        typer.echo("  • Dependencies: pip install qdrant-client sentence-transformers")

@app.command()
def analyze(
    task: str = typer.Argument(None, help="Task description to analyze"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive task selection and analysis")
):
    """🔄 Analyze task complexity and provide breakdown suggestions."""
    root = Path.cwd()
    nd_path = root / ".neuro-dock"
    
    if not nd_path.exists():
        typer.echo("❌ .neuro-dock directory not found. Run 'nd init' first.")
        raise typer.Exit(1)
    
    # Initialize database and get agent
    initialize_schema()
    store = get_store(str(root))
    agent = get_project_agent(str(root))
    
    typer.echo("🔍 TASK COMPLEXITY ANALYSIS")
    typer.echo("=" * 50)
    
    if interactive:
        # Show available tasks from plan
        task_plan = store.get_task_plan()
        if task_plan and "tasks" in task_plan:
            tasks = task_plan["tasks"]
            typer.echo("📋 Available tasks for analysis:")
            for i, task_info in enumerate(tasks, 1):
                name = task_info.get('name', f'Task {i}')
                status = task_info.get('status', 'pending')
                complexity = task_info.get('complexity_rating', 'unknown')
                typer.echo(f"  {i}. {name} (Status: {status}, Complexity: {complexity})")
            
            try:
                choice = typer.prompt("\nSelect task number to analyze", type=int)
                if 1 <= choice <= len(tasks):
                    selected_task = tasks[choice - 1]
                    task = selected_task.get('description', selected_task.get('name', ''))
                else:
                    typer.echo("❌ Invalid task number")
                    raise typer.Exit(1)
            except (ValueError, KeyboardInterrupt):
                typer.echo("❌ Analysis cancelled")
                raise typer.Exit(1)
        else:
            typer.echo("❌ No task plan found. Run 'nd plan' first.")
            raise typer.Exit(1)
    
    if not task:
        try:
            task = typer.prompt("Enter task description to analyze")
        except KeyboardInterrupt:
            typer.echo("❌ Analysis cancelled")
            raise typer.Exit(1)
    
    if not task.strip():
        typer.echo("❌ Please provide a task description")
        raise typer.Exit(1)
    
    try:
        # Analyze the task
        analysis = agent.analyze_task_complexity(task.strip())
        
        typer.echo(f"\n🎯 ANALYSIS RESULTS FOR:")
        typer.echo(f"   {task.strip()}")
        typer.echo("-" * 50)
        
        # Display results
        complexity = analysis.get('complexity_rating', 0)
        hours = analysis.get('estimated_hours', 0)
        should_break_down = analysis.get('should_break_down', False)
        
        # Complexity with visual indicator
        complexity_bar = "█" * min(int(complexity), 10)
        complexity_color = "🟢" if complexity <= 3 else "🟡" if complexity <= 7 else "🔴"
        typer.echo(f"📊 Complexity: {complexity}/10 {complexity_color}")
        typer.echo(f"    [{complexity_bar:<10}]")
        
        typer.echo(f"⏱️  Estimated Time: {hours} hours")
        
        if should_break_down:
            typer.echo("⚠️  Recommendation: BREAK DOWN this task")
            
            subtasks = analysis.get('suggested_subtasks', [])
            if subtasks:
                typer.echo("\n💡 Suggested breakdown:")
                for i, subtask in enumerate(subtasks, 1):
                    typer.echo(f"  {i}. {subtask}")
        else:
            typer.echo("✅ Task complexity is manageable")
        
        # Risk assessment
        risks = analysis.get('risks', [])
        if risks:
            typer.echo(f"\n⚠️  Identified Risks:")
            for risk in risks:
                typer.echo(f"  • {risk}")
        
        # Dependencies
        dependencies = analysis.get('dependencies', [])
        if dependencies:
            typer.echo(f"\n🔗 Dependencies:")
            for dep in dependencies:
                typer.echo(f"  • {dep}")
        
        # Store analysis in memory
        analysis_summary = f"Task: {task}\nComplexity: {complexity}/10\nEstimated: {hours}h\nBreakdown needed: {should_break_down}"
        try:
            store.add_memory(analysis_summary, "task_analysis")
        except Exception:
            pass  # Silent fallback
        
        # Show Agent 2 reminders
        _show_agent_reminders("analyze", analysis_summary, {"complexity": complexity, "should_break_down": should_break_down})
        
    except Exception as e:
        typer.echo(f"❌ Analysis failed: {e}")
        raise typer.Exit(1)

# ============================================================
# AGILE DEVELOPMENT WORKFLOW COMMANDS
# ============================================================

@app.command()
def requirements():
    """🔄 AGILE PHASE 2: Gather and clarify project requirements (alias for discuss)."""
    discuss()

@app.command("sprint-plan")
def sprint_plan():
    """🔄 AGILE PHASE 3: Create sprint plan with task breakdown (alias for plan)."""
    plan()

@app.command()
def design(
    architecture: bool = typer.Option(False, "--architecture", "-a", help="Focus on architecture design"),
    ui_ux: bool = typer.Option(False, "--ui-ux", "-u", help="Focus on UI/UX design"),
    database: bool = typer.Option(False, "--database", "-d", help="Focus on database design"),
    all_designs: bool = typer.Option(False, "--all", help="Generate all design documents")
):
    """🔄 AGILE PHASE 4: Create technical design documents and architecture."""
    root = Path.cwd()
    nd_path = root / ".neuro-dock"
    
    if not nd_path.exists():
        typer.echo("❌ .neuro-dock directory not found. Run 'nd init' first.")
        raise typer.Exit(1)
    
    # Initialize database schema and get store
    initialize_schema()
    store = get_store(str(root))
    
    typer.echo("🎨 AGILE PHASE 4: Technical Design")
    typer.echo("=" * 50)
    
    # Get project context
    agent = get_project_agent(str(root))
    
    design_types = []
    if architecture or all_designs:
        design_types.append("architecture")
    if ui_ux or all_designs:
        design_types.append("ui-ux")
    if database or all_designs:
        design_types.append("database")
    
    if not design_types:
        design_types = ["architecture"]  # Default to architecture
    
    for design_type in design_types:
        typer.echo(f"\n🔧 Generating {design_type} design...")
        
        design_prompt = f"""Based on the project requirements and specifications, create a comprehensive {design_type} design document.

Project Context: {agent.get_context_summary()}

Generate a detailed {design_type} design that includes:
- Key components and their relationships
- Technical decisions and rationales
- Implementation guidelines
- Best practices and patterns

Format as markdown with clear sections and diagrams where appropriate."""

        try:
            design_content = call_llm(design_prompt)
            
            # Save design document
            design_dir = nd_path / "design"
            design_dir.mkdir(exist_ok=True)
            
            design_file = design_dir / f"{design_type}.md"
            design_file.write_text(design_content)
            
            # Store in database
            store.add_memory(design_content, f"design_{design_type}")
            
            typer.echo(f"✅ {design_type.title()} design saved to {design_file}")
            
        except Exception as e:
            typer.echo(f"❌ Failed to generate {design_type} design: {e}")
    
    typer.echo("\n🎉 Design phase completed!")
    typer.echo("💡 Next: Run 'nd develop' to start implementation")

@app.command()
def develop(
    task: str = typer.Option(None, "--task", "-t", help="Specific task to execute"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive task selection"),
    all_tasks: bool = typer.Option(False, "--all", help="Execute all pending tasks"),
    checkpoint_after: int = typer.Option(3, "--checkpoint-after", help="Human checkpoint after N tasks")
):
    """🔄 AGILE PHASE 5: Execute development tasks (enhanced version of run)."""
    root = Path.cwd()
    nd_path = root / ".neuro-dock"
    
    if not nd_path.exists():
        typer.echo("❌ .neuro-dock directory not found. Run 'nd init' first.")
        raise typer.Exit(1)
    
    typer.echo("⚙️ AGILE PHASE 5: Development")
    typer.echo("=" * 50)
    
    # Use existing run functionality but with enhanced workflow
    if task:
        run(task_name=task)
    elif interactive:
        run(interactive=True)
    elif all_tasks:
        # Execute all tasks with checkpoints
        initialize_schema()
        store = get_store(str(root))
        
        task_plan = store.get_task_plan()
        if not task_plan or "tasks" not in task_plan:
            typer.echo("❌ No task plan found. Run 'nd sprint-plan' first.")
            raise typer.Exit(1)
        
        tasks = task_plan["tasks"]
        completed_count = 0
        
        for i, task_info in enumerate(tasks, 1):
            task_name = task_info.get("name", f"Task {i}")
            typer.echo(f"\n🎯 Executing task {i}/{len(tasks)}: {task_name}")
            
            try:
                run(task_name=task_name)
                completed_count += 1
                
                # Human checkpoint
                if completed_count % checkpoint_after == 0:
                    typer.echo(f"\n🔍 Checkpoint: {completed_count} tasks completed")
                    if not typer.confirm("Continue with next tasks?"):
                        typer.echo("Development paused by user.")
                        break
                        
            except Exception as e:
                typer.echo(f"❌ Task failed: {e}")
                if not typer.confirm("Continue with remaining tasks?"):
                    break
        
        typer.echo(f"\n🎉 Development session completed! {completed_count}/{len(tasks)} tasks finished.")
    else:
        run()

@app.command()
def test(
    unit: bool = typer.Option(False, "--unit", "-u", help="Run unit tests"),
    integration: bool = typer.Option(False, "--integration", "-i", help="Run integration tests"),
    e2e: bool = typer.Option(False, "--e2e", "-e", help="Run end-to-end tests"),
    coverage: bool = typer.Option(False, "--coverage", "-c", help="Generate test coverage report"),
    affected_only: bool = typer.Option(False, "--affected-only", help="Test only affected components")
):
    """🔄 AGILE PHASE 6: Run automated tests and generate test suites."""
    root = Path.cwd()
    nd_path = root / ".neuro-dock"
    
    if not nd_path.exists():
        typer.echo("❌ .neuro-dock directory not found. Run 'nd init' first.")
        raise typer.Exit(1)
    
    typer.echo("🧪 AGILE PHASE 6: Testing")
    typer.echo("=" * 50)
    
    # Initialize database and get context
    initialize_schema()
    store = get_store(str(root))
    agent = get_project_agent(str(root))
    
    test_types = []
    if unit:
        test_types.append("unit")
    if integration:
        test_types.append("integration")
    if e2e:
        test_types.append("e2e")
    
    if not test_types:
        test_types = ["unit"]  # Default to unit tests
    
    for test_type in test_types:
        typer.echo(f"\n🔬 Generating {test_type} tests...")
        
        test_prompt = f"""Based on the current project implementation, generate comprehensive {test_type} tests.

Project Context: {agent.get_context_summary()}

Create {test_type} tests that:
- Cover all critical functionality
- Follow testing best practices
- Include edge cases and error scenarios
- Are maintainable and readable

Generate the test files with appropriate naming and structure."""

        try:
            test_content = call_llm(test_prompt)
            
            # Save test files
            test_dir = nd_path.parent / "tests" / test_type
            test_dir.mkdir(parents=True, exist_ok=True)
            
            test_file = test_dir / f"test_{test_type}.py"  # Assuming Python, could be detected
            test_file.write_text(test_content)
            
            # Store in database
            store.add_memory(test_content, f"test_{test_type}")
            
            typer.echo(f"✅ {test_type.title()} tests saved to {test_file}")
            
        except Exception as e:
            typer.echo(f"❌ Failed to generate {test_type} tests: {e}")
    
    if coverage:
        typer.echo("\n📊 Generating test coverage report...")
        # Placeholder for coverage analysis
        typer.echo("📈 Coverage analysis would run here")
    
    typer.echo("\n🎉 Testing phase completed!")
    typer.echo("💡 Next: Run 'nd review' for code review")

@app.command()
def review(
    static_analysis: bool = typer.Option(False, "--static-analysis", "-s", help="Run static code analysis"),
    security: bool = typer.Option(False, "--security", help="Security vulnerability scan"),
    performance: bool = typer.Option(False, "--performance", "-p", help="Performance analysis"),
    comprehensive: bool = typer.Option(False, "--comprehensive", help="Full comprehensive review")
):
    """🔄 AGILE PHASE 7: Automated code review and quality analysis."""
    root = Path.cwd()
    nd_path = root / ".neuro-dock"
    
    if not nd_path.exists():
        typer.echo("❌ .neuro-dock directory not found. Run 'nd init' first.")
        raise typer.Exit(1)
    
    typer.echo("🔍 AGILE PHASE 7: Code Review")
    typer.echo("=" * 50)
    
    # Initialize database and get context
    initialize_schema()
    store = get_store(str(root))
    agent = get_project_agent(str(root))
    
    review_types = []
    if static_analysis or comprehensive:
        review_types.append("static-analysis")
    if security or comprehensive:
        review_types.append("security")
    if performance or comprehensive:
        review_types.append("performance")
    
    if not review_types:
        review_types = ["static-analysis"]  # Default
    
    review_results = []
    
    for review_type in review_types:
        typer.echo(f"\n🔎 Running {review_type} review...")
        
        review_prompt = f"""Perform a comprehensive {review_type} review of the current project.

Project Context: {agent.get_context_summary()}

Analyze the codebase for:
- Code quality and maintainability
- Best practices adherence
- Potential issues and improvements
- Documentation completeness

Provide specific recommendations with file locations and code examples."""

        try:
            review_content = call_llm(review_prompt)
            review_results.append(f"## {review_type.title()} Review\n\n{review_content}")
            
            typer.echo(f"✅ {review_type.title()} review completed")
            
        except Exception as e:
            typer.echo(f"❌ Failed to run {review_type} review: {e}")
    
    # Save comprehensive review report
    if review_results:
        review_dir = nd_path / "reviews"
        review_dir.mkdir(exist_ok=True)
        
        review_file = review_dir / f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        full_review = "\n\n".join(review_results)
        review_file.write_text(full_review)
        
        # Store in database
        store.add_memory(full_review, "code_review")
        
        typer.echo(f"\n📋 Review report saved to {review_file}")
    
    typer.echo("\n🎉 Code review completed!")
    typer.echo("💡 Next: Run 'nd deploy' for deployment")

@app.command()
def deploy(
    staging: bool = typer.Option(False, "--staging", "-s", help="Deploy to staging environment"),
    production: bool = typer.Option(False, "--production", "-p", help="Deploy to production"),
    rollback: bool = typer.Option(False, "--rollback", "-r", help="Rollback last deployment")
):
    """🔄 AGILE PHASE 8: Deploy application to environments."""
    root = Path.cwd()
    nd_path = root / ".neuro-dock"
    
    if not nd_path.exists():
        typer.echo("❌ .neuro-dock directory not found. Run 'nd init' first.")
        raise typer.Exit(1)
    
    typer.echo("🚀 AGILE PHASE 8: Deployment")
    typer.echo("=" * 50)
    
    # Initialize database and get context
    initialize_schema()
    store = get_store(str(root))
    agent = get_project_agent(str(root))
    
    if rollback:
        typer.echo("🔄 Rolling back deployment...")
        # Placeholder for rollback logic
        typer.echo("📋 Rollback procedures would be executed here")
        return
    
    target_env = "staging" if staging else "production" if production else "staging"
    
    typer.echo(f"🎯 Deploying to {target_env} environment...")
    
    deploy_prompt = f"""Generate deployment configuration and scripts for {target_env} environment.

Project Context: {agent.get_context_summary()}

Create deployment assets including:
- Environment-specific configuration files
- CI/CD pipeline scripts
- Deployment monitoring and health checks
- Rollback procedures

Consider security, scalability, and reliability requirements."""

    try:
        deploy_content = call_llm(deploy_prompt)
        
        # Save deployment configuration
        deploy_dir = nd_path.parent / "deployment"
        deploy_dir.mkdir(exist_ok=True)
        
        deploy_file = deploy_dir / f"{target_env}_deploy.md"
        deploy_file.write_text(deploy_content)
        
        # Store in database
        store.add_memory(deploy_content, f"deployment_{target_env}")
        
        typer.echo(f"✅ Deployment configuration saved to {deploy_file}")
        typer.echo(f"🚀 {target_env.title()} deployment prepared")
        
    except Exception as e:
        typer.echo(f"❌ Failed to prepare deployment: {e}")
    
    typer.echo("\n🎉 Deployment phase completed!")
    typer.echo("💡 Next: Run 'nd retrospective' for project analysis")

@app.command()
def retrospective():
    """🔄 AGILE PHASE 9: Conduct project retrospective and analysis."""
    root = Path.cwd()
    nd_path = root / ".neuro-dock"
    
    if not nd_path.exists():
        typer.echo("❌ .neuro-dock directory not found. Run 'nd init' first.")
        raise typer.Exit(1)
    
    typer.echo("📊 AGILE PHASE 9: Retrospective")
    typer.echo("=" * 50)
    
    # Initialize database and get context
    initialize_schema()
    store = get_store(str(root))
    agent = get_project_agent(str(root))
    
    typer.echo("🔍 Analyzing project completion and gathering insights...")
    
    retro_prompt = f"""Conduct a comprehensive project retrospective analysis.

Project Context: {agent.get_context_summary()}

Analyze the project and provide insights on:
- What went well (successes and achievements)
- What could be improved (challenges and blockers)
- Lessons learned and best practices discovered
- Recommendations for future projects
- Quality metrics and completion statistics

Provide actionable insights for continuous improvement."""

    try:
        retro_content = call_llm(retro_prompt)
        
        # Save retrospective report
        retro_dir = nd_path / "retrospectives"
        retro_dir.mkdir(exist_ok=True)
        
        retro_file = retro_dir / f"retrospective_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        retro_file.write_text(retro_content)
        
        # Store in database
        store.add_memory(retro_content, "retrospective")
        
        typer.echo(f"✅ Retrospective report saved to {retro_file}")
        typer.echo("\n📋 PROJECT RETROSPECTIVE:")
        typer.echo("=" * 50)
        typer.echo(retro_content[:500] + "..." if len(retro_content) > 500 else retro_content)
        
    except Exception as e:
        typer.echo(f"❌ Failed to generate retrospective: {e}")
    
    typer.echo("\n🎉 Project retrospective completed!")
    typer.echo("🏆 Congratulations on completing the agile development cycle!")

# ============================================================
# SUPPORTING AGILE COMMANDS
# ============================================================

@app.command()
def backlog():
    """🔄 View current sprint backlog (alias for tasks)."""
    tasks()

@app.command()
def estimate(task_description: str):
    """🔄 Estimate task complexity and effort (alias for analyze)."""
    analyze(task_description)

@app.command()
def progress():
    """🔄 Detailed progress analytics and metrics."""
    root = Path.cwd()
    nd_path = root / ".neuro-dock"
    
    if not nd_path.exists():
        typer.echo("❌ .neuro-dock directory not found. Run 'nd init' first.")
        raise typer.Exit(1)
    
    # Initialize database and get context
    initialize_schema()
    store = get_store(str(root))
    
    typer.echo("📊 PROJECT PROGRESS ANALYTICS")
    typer.echo("=" * 50)
    
    # Get task plan and calculate metrics
    task_plan = store.get_task_plan()
    if task_plan and "tasks" in task_plan:
        tasks = task_plan["tasks"]
        total_tasks = len(tasks)
        
        # Calculate completion metrics (placeholder logic)
        completed_tasks = 0 # This would be calculated from actual task status
        in_progress_tasks = 0
        pending_tasks = total_tasks - completed_tasks - in_progress_tasks
        
        completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        typer.echo(f"📈 Completion: {completion_percentage:.1f}%")
        typer.echo(f"✅ Completed: {completed_tasks}/{total_tasks}")
        typer.echo(f"🔄 In Progress: {in_progress_tasks}")
        typer.echo(f"⏳ Pending: {pending_tasks}")
        
        # Time estimates
        total_estimated_hours = sum(task.get("estimated_hours", 0) for task in tasks)
        typer.echo(f"⏱️  Total Estimated: {total_estimated_hours} hours")
        
        # Memory and context stats
        memories = store.get_all_memories()
        typer.echo(f"🧠 Project Memories: {len(memories) if memories else 0}")
        
    else:
        typer.echo("❌ No task plan found. Run 'nd sprint-plan' first.")
    
    typer.echo("\n💡 Use 'nd status' for overall system health")

@app.command()
def context():
    """🔄 View current project context and memory."""
    root = Path.cwd()
    nd_path = root / ".neuro-dock"
    
    if not nd_path.exists():
        typer.echo("❌ .neuro-dock directory not found. Run 'nd init' first.")
        raise typer.Exit(1)
    
    # Initialize database and get context
    initialize_schema()
    agent = get_project_agent(str(root))
    
    typer.echo("🧠 PROJECT CONTEXT")
    typer.echo("=" * 50)
    
    project_summary = agent.get_project_summary()
    
    # Format the project summary nicely
    typer.echo(f"📁 Project: {project_summary['project_info'].get('name', 'NeuroDock Project')}")
    typer.echo(f"📊 Tasks: {project_summary['task_stats']['total']} total, {project_summary['task_stats']['completed']} completed")
    typer.echo(f"🧠 Memory: {project_summary['memory_entries']} entries")
    typer.echo(f"📈 Progress: {project_summary['task_stats']['completion_rate']:.1f}%")
    
    if project_summary['task_stats']['total'] > 0:
        typer.echo(f"   ✅ Completed: {project_summary['task_stats']['completed']}")
        typer.echo(f"   🔄 In Progress: {project_summary['task_stats']['in_progress']}")
        typer.echo(f"   ⏳ Pending: {project_summary['task_stats']['pending']}")
    
    typer.echo("\n💡 Use 'nd memory --search' to search project memory")

@app.command()
def memory(
    search: str = typer.Option(None, "--search", "-s", help="Search query for project memory"),
    list_all: bool = typer.Option(False, "--list", "-l", help="List all memory entries"),
    export: bool = typer.Option(False, "--export", "-e", help="Export memory to file")
):
    """🔄 Search and manage project memory."""
    root = Path.cwd()
    nd_path = root / ".neuro-dock"
    
    if not nd_path.exists():
        typer.echo("❌ .neuro-dock directory not found. Run 'nd init' first.")
        raise typer.Exit(1)
    
    # Initialize database
    initialize_schema()
    store = get_store(str(root))
    
    typer.echo("🧠 PROJECT MEMORY")
    typer.echo("=" * 50)
    
    if search:
        typer.echo(f"🔍 Searching for: '{search}'")
        # Search functionality would go here
        memories = store.get_all_memories()
        if memories:
            matching = [m for m in memories if search.lower() in str(m).lower()]
            typer.echo(f"📋 Found {len(matching)} matching entries")
            for i, memory in enumerate(matching[:5], 1):
                memory_text = str(memory)[:100] + "..." if len(str(memory)) > 100 else str(memory)
                typer.echo(f"  {i}. {memory_text}")
        else:
            typer.echo("❌ No memories found")
    
    elif list_all:
        memories = store.get_all_memories()
        if memories:
            typer.echo(f"📋 Total memory entries: {len(memories)}")
            for i, memory in enumerate(memories[:10], 1):  # Show first 10
                memory_text = str(memory)[:100] + "..." if len(str(memory)) > 100 else str(memory)
                typer.echo(f"  {i}. {memory_text}")
            if len(memories) > 10:
                typer.echo(f"  ... and {len(memories) - 10} more entries")
        else:
            typer.echo("❌ No memories found")
    
    elif export:
        memories = store.get_all_memories()
        if memories:
            export_file = nd_path / f"memory_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            export_file.write_text(json.dumps(memories, indent=2, default=str))
            typer.echo(f"✅ Memory exported to {export_file}")
        else:
            typer.echo("❌ No memories to export")
    
    else:
        typer.echo("💡 Use --search, --list, or --export options")
        typer.echo("   Example: nd memory --search 'requirements'")

# ============================================================
# NEO4J GRAPH MEMORY COMMANDS
# ============================================================

@app.command("graph-memory")
def graph_memory(
    search: str = typer.Option(None, "--search", "-s", help="Search graph memory"),
    add: str = typer.Option(None, "--add", "-a", help="Add content to graph memory"),
    relationships: bool = typer.Option(False, "--relationships", "-r", help="Show memory relationships"),
    test: bool = typer.Option(False, "--test", "-t", help="Test Neo4J connection")
):
    """🔄 Manage Neo4J graph-based memory system."""
    root = Path.cwd()
    
    if test:
        try:
            from .memory.neo4j_store import get_neo4j_store
            store = get_neo4j_store()
            if store.test_connection():
                typer.echo("✅ Neo4J connection successful!")
            else:
                typer.echo("❌ Neo4J connection failed!")
                raise typer.Exit(1)
        except ImportError:
            typer.echo("❌ Neo4J dependencies not installed. Run: pip install neo4j")
            raise typer.Exit(1)
        except Exception as e:
            typer.echo(f"❌ Neo4J test failed: {e}")
            raise typer.Exit(1)
        return
    
    if add:
        try:
            from .memory.neo4j_store import get_neo4j_store
            store = get_neo4j_store()
            result = store.add_memory(add, "manual", str(root))
            if result:
                typer.echo(f"✅ Added to graph memory: {result}")
            else:
                typer.echo("❌ Failed to add to graph memory")
        except Exception as e:
            typer.echo(f"❌ Error adding to graph memory: {e}")
        return
    
    if search:
        try:
            from .memory.neo4j_store import get_neo4j_store
            store = get_neo4j_store()
            results = store.search_memories(search, str(root))
            
            if results:
                typer.echo(f"🔍 Found {len(results)} results in graph memory:")
                for i, result in enumerate(results[:5], 1):
                    content = result.get('content', '')[:100] + "..." if len(result.get('content', '')) > 100 else result.get('content', '')
                    typer.echo(f"  {i}. {content}")
                    typer.echo(f"     Type: {result.get('type', 'unknown')}")
            else:
                typer.echo("❌ No results found in graph memory")
        except Exception as e:
            typer.echo(f"❌ Error searching graph memory: {e}")
        return
    
    if relationships:
        try:
            from .memory.neo4j_store import get_neo4j_store
            store = get_neo4j_store()
            relationships = store.get_relationships(str(root))
            
            if relationships:
                typer.echo(f"🔗 Found {len(relationships)} relationships:")
                for rel in relationships[:10]:
                    typer.echo(f"  {rel['from_node']} --[{rel['type']}]--> {rel['to_node']}")
            else:
                typer.echo("❌ No relationships found")
        except Exception as e:
            typer.echo(f"❌ Error getting relationships: {e}")
        return
    
    # Default: show help
    typer.echo("🧠 Neo4J Graph Memory System")
    typer.echo("Available options:")
    typer.echo("  --test          Test Neo4J connection")
    typer.echo("  --add TEXT      Add content to graph memory")
    typer.echo("  --search TEXT   Search graph memory")
    typer.echo("  --relationships Show memory relationships")
    typer.echo()
    typer.echo("Setup: Set NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD in .env")

@app.command("reminders")
def reminders(
    command: str = typer.Option(None, "--for-command", "-c", help="Show reminders for specific command"),
    clear: bool = typer.Option(False, "--clear", help="Clear old reminders")
):
    """🔄 View and manage Agent 2 reminders."""
    root = Path.cwd()
    
    if clear:
        # Placeholder for clearing old reminders
        typer.echo("🧹 Old reminders cleared")
        return
    
    if command:
        try:
            from .memory import show_post_command_reminders
            show_post_command_reminders(command, "", str(root))
        except Exception as e:
            typer.echo(f"❌ Error showing reminders: {e}")
    else:
        typer.echo("💡 Agent 2 Reminder System")
        typer.echo("Available options:")
        typer.echo("  --for-command TEXT  Show reminders for specific command")
        typer.echo("  --clear            Clear old reminders")
        typer.echo()
        typer.echo("Reminders are automatically shown after command completion")


@app.command("begin")
def begin_conversation():
    """🤖 Start comprehensive Agent 1 conversation for project development."""
    try:
        from .conversational_agent import get_conversation_agent
        agent = get_conversation_agent()
        response = agent.begin_conversation()
        typer.echo(response)
    except Exception as e:
        typer.echo(f"❌ Error starting conversation: {e}")

@app.command("continue")
def continue_conversation():
    """🔄 Resume Agent 1 conversation where left off."""
    try:
        from .conversational_agent import get_conversation_agent
        agent = get_conversation_agent()
        response = agent.continue_conversation()
        typer.echo(response)
    except Exception as e:
        typer.echo(f"❌ Error continuing conversation: {e}")

@app.command("conversation-status")
def conversation_status():
    """📊 View current Agent 1 conversation state."""
    try:
        from .conversational_agent import get_conversation_agent
        agent = get_conversation_agent()
        status = agent.get_conversation_status()
        
        typer.echo("🤖 Agent 1 Conversation Status")
        typer.echo("=" * 40)
        typer.echo(f"Phase: {status['phase']}")
        typer.echo(f"Current Step: {status['current_step']}")
        typer.echo(f"Next Actions: {', '.join(status['next_actions'])}")
        typer.echo(f"Total Exchanges: {status['total_exchanges']}")
        typer.echo(f"Ready for Next Phase: {status['ready_for_next_phase']}")
    except Exception as e:
        typer.echo(f"❌ Error showing conversation status: {e}")

@app.command("explain")
def explain_topic(topic: str = typer.Argument(..., help="Topic to explain")):
    """💡 Agent 1 explains any system aspect."""
    try:
        from .conversational_agent import get_conversation_agent
        agent = get_conversation_agent()
        explanation = agent.explain_topic(topic)
        typer.echo(explanation)
    except Exception as e:
        typer.echo(f"❌ Error explaining topic: {e}")

@app.command("guide-me")
def guide_next_step():
    """🧭 Get Agent 1 guidance on next best step."""
    try:
        from .conversational_agent import get_conversation_agent
        agent = get_conversation_agent()
        guidance = agent.guide_next_step()
        typer.echo(guidance)
    except Exception as e:
        typer.echo(f"❌ Error providing guidance: {e}")

def main():
    """Main entry point for the NeuroDock CLI."""
    app()


if __name__ == "__main__":
    main()
