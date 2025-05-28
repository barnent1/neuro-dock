#!/usr/bin/env python3

"""
Interactive discussion system for neuro-dock.
Handles back-and-forth clarification dialogue and task generation.
"""

import json
import yaml
import typer
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from .utils.models import call_llm
from .memory.qdrant_store import search_memory, add_to_memory
from .db import get_store


def run_interactive_discussion(nd_path: Path) -> bool:
    """
    Run the complete interactive discussion workflow.
    
    Args:
        nd_path: Path to the .neuro-dock directory
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get database store for this project
        store = get_store(str(nd_path.parent))
        
        # Load initial prompt from database
        initial_prompt_entry = store.get_latest_memory("user_prompt")
        if not initial_prompt_entry:
            typer.echo("❌ No user prompt found in database.")
            typer.echo("The discuss command should have already captured your initial prompt.")
            typer.echo("💡 This might indicate a database connection issue.")
            typer.echo("   Try running 'nd setup' to configure your database.")
            return False
        
        # Extract text from database entry
        if isinstance(initial_prompt_entry, dict):
            initial_prompt = initial_prompt_entry.get('text', '')
        else:
            initial_prompt = str(initial_prompt_entry) if initial_prompt_entry else ''
        
        if not initial_prompt.strip():
            typer.echo("❌ The user prompt in database is empty.")
            return False
            return False
        
        typer.echo("🤖 Starting interactive discussion to clarify your project goals...")
        typer.echo(f"📝 Initial prompt: {initial_prompt}")
        typer.echo()
        
        # Step 1: Clarification dialogue
        discussion_history = []
        clarified_prompt = _run_clarification_dialogue(initial_prompt, discussion_history, nd_path)
        
        if not clarified_prompt:
            typer.echo("❌ Discussion was cancelled or failed.")
            return False
        
        # Step 2: Task generation
        task_plan = _generate_task_plan(clarified_prompt, nd_path)
        
        if not task_plan:
            typer.echo("❌ Task plan generation failed.")
            return False
        
        # Step 3: Save results to database instead of flat files
        _save_discussion_results(store, discussion_history, clarified_prompt, task_plan)
        
        typer.echo("\n🎉 Discussion completed successfully!")
        typer.echo("💡 Next steps:")
        typer.echo("  • Review task plan: neuro-dock tasks")
        typer.echo("  • Run 'neuro-dock run' to execute tasks interactively")
        
        return True
        
    except KeyboardInterrupt:
        typer.echo("\n⚠️  Discussion interrupted by user.")
        return False
    except Exception as e:
        typer.echo(f"❌ Discussion failed: {e}", err=True)
        return False


def _run_clarification_dialogue(initial_prompt: str, discussion_history: List[Dict], nd_path: Path) -> Optional[str]:
    """Run the clarification Q&A dialogue."""
    
    typer.echo("🔍 Generating clarifying questions...")
    
    # Generate clarifying questions using LLM with memory context
    questions_prompt = f"""You are helping clarify a software project specification. The user provided this initial description:

"{initial_prompt}"

Generate 3-5 specific clarifying questions to better understand:
- The target users and use cases
- Technical requirements and constraints  
- Key features and functionality
- Deployment and scalability needs
- Integration requirements

Format as a numbered list of questions. Be specific and actionable."""

    try:
        questions_response = call_llm(questions_prompt)
        discussion_history.append({
            "role": "assistant", 
            "content": questions_response,
            "type": "clarification_questions",
            "timestamp": datetime.now().isoformat()
        })
        
        typer.echo("\n" + "="*60)
        typer.echo("❓ CLARIFYING QUESTIONS:")
        typer.echo("="*60)
        typer.echo(questions_response)
        typer.echo("="*60)
        
    except Exception as e:
        typer.echo(f"❌ Failed to generate questions: {e}", err=True)
        return None
    
    # Collect user answers
    typer.echo("\n📝 Please answer these questions to clarify your project:")
    typer.echo("(You can answer all at once or provide brief responses to each)")
    typer.echo()
    
    # Check if input is available from stdin (piped input)
    if not sys.stdin.isatty():
        # Read from stdin (piped input)
        user_answers = sys.stdin.read().strip()
        typer.echo(f"Your answers: {user_answers}")
    else:
        # Interactive mode
        try:
            user_answers = typer.prompt("Your answers")
        except (EOFError, KeyboardInterrupt):
            typer.echo("\n❌ Input cancelled.")
            return None
    
    if not user_answers.strip():
        typer.echo("❌ No answers provided.")
        return None
    discussion_history.append({
        "role": "user",
        "content": user_answers,
        "type": "clarification_answers",
        "timestamp": datetime.now().isoformat()
    })
    
    # Generate clarified specification
    typer.echo("\n🧠 Processing your answers...")
    
    summary_prompt = f"""Based on this discussion, create a clear and comprehensive project specification:

Initial request: "{initial_prompt}"

Clarifying questions: {questions_response}

User answers: {user_answers}

Write a detailed project specification that includes:
1. Project overview and goals
2. Target users and use cases
3. Core features and functionality
4. Technical requirements
5. Success criteria

Be specific and actionable. This will be used to generate implementation tasks."""

    try:
        clarified_spec = call_llm(summary_prompt)
        
        typer.echo("\n" + "="*60)
        typer.echo("📋 CLARIFIED PROJECT SPECIFICATION:")
        typer.echo("="*60)
        typer.echo(clarified_spec)
        typer.echo("="*60)
        
        # Confirm with user
        typer.echo()
        
        # Handle confirmation input
        if not sys.stdin.isatty():
            # For piped input, assume confirmed
            confirm = True
            typer.echo("✅ Specification confirmed (piped input mode)")
        else:
            # Interactive mode
            try:
                confirm = typer.confirm("Does this specification accurately capture your project goals?")
            except (EOFError, KeyboardInterrupt):
                typer.echo("\n❌ Confirmation cancelled.")
                return None
        
        if not confirm:
            typer.echo("Let's refine the specification...")
            
            # Handle refinement input
            if not sys.stdin.isatty():
                typer.echo("❌ Cannot refine specification in piped input mode.")
                typer.echo("💡 Use interactive mode for specification refinement.")
                return None
            else:
                try:
                    refinement = typer.prompt("What would you like to change or add?")
                except (EOFError, KeyboardInterrupt):
                    typer.echo("\n❌ Refinement cancelled.")
                    return None
            
            refinement_prompt = f"""The user wants to refine this project specification:

{clarified_spec}

User feedback: {refinement}

Please update the specification based on their feedback, keeping all the good parts and incorporating their changes."""
            
            clarified_spec = call_llm(refinement_prompt)
            
            typer.echo("\n" + "="*60)
            typer.echo("📋 REFINED PROJECT SPECIFICATION:")
            typer.echo("="*60)
            typer.echo(clarified_spec)
            typer.echo("="*60)
        
        discussion_history.append({
            "role": "assistant",
            "content": clarified_spec,
            "type": "clarified_specification",
            "timestamp": datetime.now().isoformat()
        })
        
        # Store clarified prompt in vector memory
        try:
            add_to_memory(
                clarified_spec,
                {"type": "clarified_specification", "source": "discuss_command"}
            )
        except Exception:
            pass  # Silent fallback
        
        return clarified_spec
        
    except Exception as e:
        typer.echo(f"❌ Failed to generate specification: {e}", err=True)
        return None


def _generate_task_plan(clarified_prompt: str, nd_path: Path) -> Optional[Dict[str, Any]]:
    """Generate structured task plan from clarified specification."""
    
    typer.echo("⚙️  Generating structured task plan...")
    
    # Detect project framework to provide better task structure
    framework = _detect_project_framework(nd_path)
    framework_context = ""
    if framework:
        framework_context = f"\nDetected framework: {framework}. Structure tasks accordingly."
    
    task_prompt = f"""Break down this project into structured development tasks:

{clarified_prompt}{framework_context}

Create a YAML structure with:
- project: metadata (name, description, created timestamp)
- phases: logical groupings of tasks
- Each task should have:
  - id: unique identifier (lowercase-with-hyphens)
  - title: short descriptive name
  - description: detailed task description
  - dependencies: list of task IDs this depends on (if any)
  - complexity: low/medium/high
  - estimated_hours: rough time estimate

Organize phases logically: setup → core features → testing → deployment
Break complex tasks into subtasks when appropriate.
Return ONLY valid YAML without any markdown formatting."""

    try:
        response = call_llm(task_prompt)
        
        # Clean the response to extract YAML
        yaml_content = response.strip()
        if yaml_content.startswith("```yaml"):
            yaml_content = yaml_content[7:]
        if yaml_content.startswith("```"):
            yaml_content = yaml_content[3:]
        if yaml_content.endswith("```"):
            yaml_content = yaml_content[:-3]
        yaml_content = yaml_content.strip()
        
        # Try to parse as YAML
        try:
            plan_data = yaml.safe_load(yaml_content)
            if isinstance(plan_data, dict):
                # Validate and show preview
                typer.echo("\n📊 Generated Task Plan Preview:")
                typer.echo("="*50)
                
                if "project" in plan_data:
                    project = plan_data["project"]
                    typer.echo(f"Project: {project.get('name', 'Unnamed')}")
                    typer.echo(f"Description: {project.get('description', 'No description')[:100]}...")
                    typer.echo()
                
                # Count and display tasks
                task_count = 0
                if "phases" in plan_data:
                    for phase_id, phase in plan_data["phases"].items():
                        typer.echo(f"📁 {phase.get('title', phase_id)}")
                        if "tasks" in phase:
                            for task in phase["tasks"]:
                                task_count += 1
                                typer.echo(f"  • {task.get('title', task.get('id', 'Unnamed'))}")
                
                typer.echo(f"\nTotal tasks: {task_count}")
                typer.echo("="*50)
                
                # Confirm with user
                if not sys.stdin.isatty():
                    # For piped input, assume confirmed
                    confirm = True
                    typer.echo("✅ Task plan confirmed (piped input mode)")
                else:
                    # Interactive mode
                    try:
                        confirm = typer.confirm("\nDoes this task plan look good?", default=True)
                    except (EOFError, KeyboardInterrupt):
                        typer.echo("\n❌ Task plan confirmation cancelled.")
                        return None
                
                if confirm:
                    return plan_data
                else:
                    typer.echo("Task plan generation cancelled by user.")
                    return None
                    
        except yaml.YAMLError as ye:
            typer.echo(f"❌ YAML parsing failed: {ye}")
            
    except Exception as e:
        typer.echo(f"❌ Failed to generate task plan: {e}", err=True)
    
    # Fallback: create a basic structure
    typer.echo("⚠️  Creating fallback task plan...")
    fallback_plan = {
        "project": {
            "name": "User Project",
            "description": clarified_prompt[:200] + "..." if len(clarified_prompt) > 200 else clarified_prompt,
            "created": datetime.now().isoformat()
        },
        "phases": {
            "setup": {
                "title": "Project Setup",
                "tasks": [
                    {
                        "id": "initial-setup",
                        "title": "Initial Project Setup",
                        "description": "Set up basic project structure and dependencies",
                        "dependencies": [],
                        "complexity": "low",
                        "estimated_hours": 2
                    }
                ]
            },
            "implementation": {
                "title": "Core Implementation", 
                "tasks": [
                    {
                        "id": "core-features",
                        "title": "Implement Core Features",
                        "description": clarified_prompt,
                        "dependencies": ["initial-setup"],
                        "complexity": "high",
                        "estimated_hours": 8
                    }
                ]
            }
        }
    }
    
    # Handle fallback confirmation
    if not sys.stdin.isatty():
        # For piped input, assume confirmed
        typer.echo("✅ Using fallback task plan (piped input mode)")
        return fallback_plan
    else:
        # Interactive mode
        try:
            confirm = typer.confirm("Use this basic task plan?", default=True)
            return fallback_plan if confirm else None
        except (EOFError, KeyboardInterrupt):
            typer.echo("\n❌ Fallback task plan cancelled.")
            return None


def _detect_project_framework(nd_path: Path) -> Optional[str]:
    """Detect the project framework based on existing files."""
    project_root = nd_path.parent
    
    # Check for common framework indicators
    if (project_root / "package.json").exists():
        try:
            pkg_json = json.loads((project_root / "package.json").read_text())
            deps = {**pkg_json.get("dependencies", {}), **pkg_json.get("devDependencies", {})}
            
            if "next" in deps:
                return "Next.js"
            elif "react" in deps:
                return "React"
            elif "vue" in deps:
                return "Vue.js"
            elif "express" in deps:
                return "Express.js (Node.js)"
            else:
                return "Node.js"
        except:
            return "Node.js"
    
    elif (project_root / "requirements.txt").exists() or (project_root / "pyproject.toml").exists():
        return "Python"
    
    elif (project_root / "Cargo.toml").exists():
        return "Rust"
    
    elif (project_root / "go.mod").exists():
        return "Go"
    
    elif (project_root / "Gemfile").exists():
        return "Ruby"
    
    return None


def _save_discussion_results(store, discussion_history: List[Dict], clarified_prompt: str, task_plan: Dict[str, Any]):
    """Save all results to database and vector memory."""
    
    # Save discussion history to database
    try:
        store.save_discussion_history(discussion_history)
        typer.echo("✅ Discussion history saved to database")
    except Exception as e:
        typer.echo(f"⚠️  Warning: Could not save discussion history to database: {e}")
    
    # Save clarified prompt to database
    try:
        store.add_memory(clarified_prompt, "clarified_prompt")
        typer.echo("✅ Clarified prompt saved to database")
    except Exception as e:
        typer.echo(f"⚠️  Warning: Could not save clarified prompt to database: {e}")
    
    # Save task plan to database
    try:
        # Flatten the task structure for CLI compatibility
        flattened_plan = _flatten_task_plan(task_plan)
        store.save_task_plan(flattened_plan)
        typer.echo("✅ Task plan saved to database")
    except Exception as e:
        typer.echo(f"⚠️  Warning: Could not save task plan to database: {e}")
    
    # Store in vector memory
    try:
        # Store clarified prompt
        add_to_memory(
            clarified_prompt,
            {"type": "clarified_specification", "source": "discuss_command"}
        )
        
        # Store task plan summary
        summary = f"Project Discussion Summary:\n{clarified_prompt}\n\nTasks generated: {_count_tasks_in_plan(task_plan)}"
        add_to_memory(
            summary,
            {"type": "discussion_summary", "source": "discuss_command"}
        )
        
        typer.echo("✅ Results stored in vector memory")
        
    except Exception:
        # Silent fallback if vector memory is unavailable
        pass


def _flatten_task_plan(plan_data: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten task plan from phases structure to flat tasks array for CLI compatibility."""
    flattened = {
        "project": plan_data.get("project", {}),
        "tasks": []
    }
    
    if "phases" in plan_data:
        # Extract tasks from phases
        for phase_id, phase in plan_data["phases"].items():
            if "tasks" in phase:
                for task in phase["tasks"]:
                    # Add phase context to task
                    task["phase"] = phase.get("title", phase_id)
                    flattened["tasks"].append(task)
    elif "tasks" in plan_data:
        # Already flat structure
        flattened["tasks"] = plan_data["tasks"]
    
    return flattened


def _count_tasks_in_plan(plan_data: Dict[str, Any]) -> int:
    """Count total tasks in a plan."""
    count = 0
    if "phases" in plan_data:
        for phase in plan_data["phases"].values():
            if "tasks" in phase:
                count += len(phase["tasks"])
    elif "tasks" in plan_data:
        count = len(plan_data["tasks"])
    return count
