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
    Run the complete interactive discussion workflow with iterative conversation support.
    Supports multiple rounds of Q&A between Developer → Navigator → NeuroDock.
    
    Args:
        nd_path: Path to the .neuro-dock directory
        
    Returns:
        True if completely successful (ready for planning), False otherwise
    """
    try:
        # Get database store for this project
        store = get_store(str(nd_path.parent))
        
        # Check for existing conversation state
        conversation_state = _load_discussion_state(store)
        
        # Debug: ensure conversation_state is valid
        if not isinstance(conversation_state, dict):
            typer.echo(f"❌ Invalid conversation state type: {type(conversation_state)}")
            return False
        
        if "status" not in conversation_state:
            typer.echo(f"❌ Missing 'status' in conversation state: {conversation_state}")
            return False
        
        if conversation_state["status"] == "new":
            # Start new discussion
            return _start_new_discussion(store, nd_path)
        elif conversation_state["status"] == "questions_pending":
            # Continue with questions from NeuroDock
            return _handle_pending_questions(store, nd_path, conversation_state)
        elif conversation_state["status"] == "awaiting_answers":
            # Process answers and continue iteration
            return _process_answers_and_continue(store, nd_path, conversation_state)
        elif conversation_state["status"] == "ready_for_planning":
            # Generate final task plan
            return _generate_final_plan(store, nd_path, conversation_state)
        else:
            typer.echo(f"❌ Unknown discussion state: {conversation_state['status']}")
            return False
            
    except Exception as e:
        typer.echo(f"❌ Discussion failed: {e}", err=True)
        return False


def _run_clarification_dialogue(initial_prompt: str, discussion_history: List[Dict], nd_path: Path) -> Optional[str]:
    """Run the clarification Q&A dialogue."""
    
    typer.echo("🔍 Generating clarifying questions...")
    
    # Get project context and memory to inform question generation
    project_context = ""
    try:
        # Check for existing project context or framework detection
        framework = _detect_project_framework(nd_path)
        if framework:
            project_context += f"\nDetected project framework: {framework}"
        
        # Search for relevant memory context
        memory_results = search_memory(initial_prompt, limit=3)
        if memory_results:
            project_context += f"\nRelevant project memory: {memory_results}"
    except Exception:
        # Continue without context if there are issues
        pass
    
    # Generate clarifying questions using LLM with memory context
    questions_prompt = f"""You are an expert software development consultant helping to clarify a project specification. The user provided this initial description:

"{initial_prompt}"

{project_context}

Analyze this project description and generate 3-5 highly specific clarifying questions that are most relevant for THIS particular project. 

Consider what's already clear from their description and focus your questions on the gaps and ambiguities that would be critical for implementation. The questions should be:

1. **Project-specific**: Tailored to the actual type of application/system they're describing
2. **Implementation-focused**: Help determine concrete technical decisions
3. **Priority-driven**: Address the most important unknowns first
4. **Context-aware**: Build on what they've already told you

Do NOT ask generic questions that apply to every software project. Instead, analyze their specific description and ask the questions that would be most valuable for understanding and implementing THEIR vision.

Format as a numbered list of questions."""

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
    
    # Instead of collecting user input in terminal, return questions to Navigator
    # The Navigator should handle these questions intelligently
    typer.echo("\n📝 Questions generated for Navigator to handle:")
    typer.echo("(Navigator will either ask you these questions or auto-answer based on context)")
    typer.echo()
    
    # Try to auto-answer questions based on context and memory
    user_answers = _auto_answer_questions(initial_prompt, questions_response, project_context)
    
    if user_answers:
        typer.echo(f"✅ Auto-answered based on context: {user_answers[:100]}...")
    else:
        # Return questions to Navigator instead of waiting for terminal input
        typer.echo("🔄 Questions returned to Navigator for handling")
        # Save questions to memory for Navigator to process
        try:
            store = get_store(str(nd_path.parent))
            store.add_memory(questions_response, "clarification_questions")
            typer.echo("💾 Questions saved to memory for Navigator processing")
        except Exception:
            pass
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
        
        # Enhanced YAML cleaning and extraction
        yaml_content = response.strip()
        
        # Remove all markdown code block formatting
        yaml_content = yaml_content.replace('```yaml', '').replace('```', '')
        
        # Handle document separators (split on --- and take first document)
        if '---' in yaml_content:
            yaml_parts = yaml_content.split('---')
            # Find the part that starts with project:, tasks:, or phases:
            for part in yaml_parts:
                part = part.strip()
                if part and any(part.startswith(prefix) for prefix in ['project:', 'tasks:', 'phases:']):
                    yaml_content = part
                    break
            else:
                # If no valid part found, use the first non-empty part
                yaml_content = next((part.strip() for part in yaml_parts if part.strip()), yaml_content)
        
        # Remove any leading explanatory text before the YAML
        lines = yaml_content.split('\n')
        yaml_start_idx = 0
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if stripped_line.startswith(('project:', 'tasks:', 'phases:')):
                yaml_start_idx = i
                break
        
        if yaml_start_idx > 0:
            yaml_content = '\n'.join(lines[yaml_start_idx:])
        
        yaml_content = yaml_content.strip()
        
        # Debug output for troubleshooting
        if not yaml_content:
            typer.echo(f"❌ Empty YAML content after cleaning. Original response length: {len(response)}")
            typer.echo(f"First 200 chars: {response[:200]}")
        
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
                    phases = plan_data["phases"]
                    if isinstance(phases, dict):
                        # Handle dictionary format (expected)
                        for phase_id, phase in phases.items():
                            if isinstance(phase, dict):
                                typer.echo(f"📁 {phase.get('title', phase_id)}")
                                if "tasks" in phase and isinstance(phase["tasks"], list):
                                    for task in phase["tasks"]:
                                        if isinstance(task, dict):
                                            task_count += 1
                                            typer.echo(f"  • {task.get('title', task.get('id', 'Unnamed'))}")
                    elif isinstance(phases, list):
                        # Handle list format (fallback)
                        for i, phase in enumerate(phases):
                            if isinstance(phase, dict):
                                phase_title = phase.get('title', f'Phase {i+1}')
                                typer.echo(f"📁 {phase_title}")
                                if "tasks" in phase and isinstance(phase["tasks"], list):
                                    for task in phase["tasks"]:
                                        if isinstance(task, dict):
                                            task_count += 1
                                            typer.echo(f"  • {task.get('title', task.get('id', 'Unnamed'))}")
                            elif isinstance(phase, str):
                                # Handle simple string phases
                                typer.echo(f"📁 {phase}")
                elif "tasks" in plan_data:
                    # Handle flat tasks structure
                    tasks = plan_data["tasks"]
                    if isinstance(tasks, list):
                        for task in tasks:
                            if isinstance(task, dict):
                                task_count += 1
                                typer.echo(f"  • {task.get('title', task.get('name', 'Unnamed'))}")
                
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
            typer.echo(f"📝 Raw YAML content that failed to parse:")
            typer.echo("-" * 40)
            # Show first few lines with line numbers for debugging
            lines = yaml_content.split('\n')[:10]
            for i, line in enumerate(lines, 1):
                typer.echo(f"{i:2}: {line}")
            if len(yaml_content.split('\n')) > 10:
                typer.echo(f"... ({len(yaml_content.split('\n')) - 10} more lines)")
            typer.echo("-" * 40)
            
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


def _auto_answer_questions(initial_prompt: str, questions: str, project_context: str) -> Optional[str]:
    """
    Try to auto-answer clarification questions based on context and memory.
    Returns answers if confident, None if Navigator should handle questions.
    """
    try:
        # Use LLM to determine if questions can be auto-answered
        auto_answer_prompt = f"""You are an intelligent project assistant. Given this project description and context, determine if you can confidently answer the clarification questions automatically.

PROJECT DESCRIPTION: "{initial_prompt}"

PROJECT CONTEXT: {project_context}

CLARIFICATION QUESTIONS: {questions}

INSTRUCTIONS:
1. Only auto-answer if you can make reasonable assumptions based on the project description
2. For a basic/simple project request, provide sensible defaults
3. If the questions require specific user input that can't be inferred, return "NAVIGATOR_HANDLE"
4. If you can answer, provide brief, practical answers that align with the project description

Your response should either be:
- "NAVIGATOR_HANDLE" (if questions need user input)
- A brief set of answers addressing the questions in order"""

        response = call_llm(auto_answer_prompt)
        
        if response and "NAVIGATOR_HANDLE" not in response.upper():
            return response
        else:
            return None
            
    except Exception:
        return None


def _load_discussion_state(store) -> Dict[str, Any]:
    """Load current discussion state from database."""
    try:
        state = store.get_latest_memory("discussion_state")
        if state:
            if isinstance(state, dict):
                # Handle database object format with 'text' field
                if 'text' in state:
                    return json.loads(state['text'])
                else:
                    return state
            elif isinstance(state, str):
                return json.loads(state)
        
        # Default new state
        return {
            "status": "new",
            "iteration": 0,
            "questions": [],
            "answers": [],
            "conversation_history": [],
            "unresolved_topics": []
        }
    except Exception as e:
        typer.echo(f"❌ Error loading discussion state: {e}")
        return {"status": "new", "iteration": 0}


def _start_new_discussion(store, nd_path: Path) -> bool:
    """Start a new discussion process."""
    # Load initial prompt from database
    initial_prompt_entry = store.get_latest_memory("user_prompt")
    if not initial_prompt_entry:
        typer.echo("❌ No user prompt found in database.")
        typer.echo("💡 Use Navigator to provide your project description first.")
        return False
    
    # Extract text from database entry
    if isinstance(initial_prompt_entry, dict):
        initial_prompt = initial_prompt_entry.get('text', '')
    else:
        initial_prompt = str(initial_prompt_entry) if initial_prompt_entry else ''
    
    if not initial_prompt.strip():
        typer.echo("❌ The user prompt in database is empty.")
        return False
    
    typer.echo("🤖 Starting interactive discussion to clarify your project goals...")
    typer.echo(f"📝 Initial prompt: {initial_prompt}")
    typer.echo()
    
    # Generate first round of questions
    questions = _generate_clarifying_questions(initial_prompt, [], nd_path)
    if not questions:
        typer.echo("❌ Failed to generate initial questions.")
        return False
    
    # Save discussion state
    discussion_state = {
        "status": "questions_pending",
        "iteration": 1,
        "initial_prompt": initial_prompt,
        "questions": questions,
        "answers": [],
        "conversation_history": [
            {
                "iteration": 1,
                "questions": questions,
                "timestamp": datetime.now().isoformat()
            }
        ],
        "unresolved_topics": []
    }
    
    store.add_memory(json.dumps(discussion_state), "discussion_state")
    
    # Display questions for Navigator to handle
    typer.echo("\n" + "="*60)
    typer.echo("❓ CLARIFYING QUESTIONS (for Navigator to process):")
    typer.echo("="*60)
    typer.echo(questions)
    typer.echo("="*60)
    typer.echo("\n🔄 Questions ready for Navigator to handle with Developer")
    typer.echo("💡 Navigator should ask these questions and then provide answers")
    
    # Return False because discussion is not complete - it's just starting
    # Navigator needs to collect answers before we can continue
    return False


def _handle_pending_questions(store, nd_path: Path, conversation_state: Dict) -> bool:
    """Handle case where questions are pending Navigator/Developer response."""
    typer.echo("📋 Questions are pending Developer responses via Navigator...")
    typer.echo("🔄 Current questions:")
    typer.echo("\n" + "="*60)
    typer.echo(conversation_state.get("questions", "No questions found"))
    typer.echo("="*60)
    typer.echo("\n💡 Navigator should collect answers and continue the process")
    # Return False because we're still waiting for Navigator input
    return False


def _process_answers_and_continue(store, nd_path: Path, conversation_state: Dict) -> bool:
    """Process answers and determine if more questions are needed."""
    # This would be called after Navigator provides answers
    answers = conversation_state.get("latest_answers", "")
    previous_qa = conversation_state.get("conversation_history", [])
    
    # Analyze if we need more clarification
    need_more_questions = _analyze_completeness(
        conversation_state.get("initial_prompt", ""),
        previous_qa,
        answers
    )
    
    if need_more_questions:
        # Generate follow-up questions
        follow_up_questions = _generate_follow_up_questions(
            conversation_state.get("initial_prompt", ""),
            previous_qa,
            answers,
            nd_path
        )
        
        if follow_up_questions:
            # Update discussion state for another iteration
            conversation_state["iteration"] += 1
            conversation_state["questions"] = follow_up_questions
            conversation_state["conversation_history"].append({
                "iteration": conversation_state["iteration"],
                "previous_answers": answers,
                "questions": follow_up_questions,
                "timestamp": datetime.now().isoformat()
            })
            
            store.add_memory(json.dumps(conversation_state), "discussion_state")
            
            typer.echo(f"\n🔄 Iteration {conversation_state['iteration']}: Additional questions needed")
            typer.echo("\n" + "="*60)
            typer.echo("❓ FOLLOW-UP QUESTIONS:")
            typer.echo("="*60)
            typer.echo(follow_up_questions)
            typer.echo("="*60)
            
            return True
    
    # Discussion is complete, ready for planning
    conversation_state["status"] = "ready_for_planning"
    store.add_memory(json.dumps(conversation_state), "discussion_state")
    
    typer.echo("\n✅ Discussion complete! All questions resolved.")
    typer.echo("🎯 Ready to generate comprehensive task plan...")
    
    return _generate_final_plan(store, nd_path, conversation_state)


def _generate_final_plan(store, nd_path: Path, conversation_state: Dict) -> bool:
    """Generate final task plan from complete conversation history."""
    # Compile complete specification from all Q&A iterations
    complete_spec = _compile_final_specification(conversation_state)
    
    # Generate task plan
    task_plan = _generate_task_plan(complete_spec, nd_path)
    
    if not task_plan:
        typer.echo("❌ Task plan generation failed.")
        return False
    
    # Save results
    _save_discussion_results(store, conversation_state["conversation_history"], complete_spec, task_plan)
    
    typer.echo("\n🎉 Discussion and planning completed successfully!")
    typer.echo("💡 Next steps:")
    typer.echo("  • Review task plan: nd plan")
    typer.echo("  • Start executing tasks: nd run")
    
    return True


def _generate_clarifying_questions(initial_prompt: str, previous_qa: List, nd_path: Path) -> Optional[str]:
    """Generate context-aware clarifying questions."""
    # Get project context and memory to inform question generation
    project_context = ""
    try:
        framework = _detect_project_framework(nd_path)
        if framework:
            project_context += f"\nDetected project framework: {framework}"
        
        memory_results = search_memory(initial_prompt, limit=3)
        if memory_results:
            project_context += f"\nRelevant project memory: {memory_results}"
    except Exception:
        pass
    
    questions_prompt = f"""You are an expert software development consultant helping to clarify a project specification. 

PROJECT DESCRIPTION: "{initial_prompt}"

PROJECT CONTEXT: {project_context}

PREVIOUS Q&A ITERATIONS: {json.dumps(previous_qa, indent=2) if previous_qa else "None - this is the first iteration"}

Generate 3-5 highly specific clarifying questions that are most relevant for THIS particular project. Focus on:

1. **Critical Implementation Details**: What's needed to build this successfully?
2. **User Experience**: How should users interact with the system?
3. **Technical Requirements**: What constraints or preferences exist?
4. **Scope Definition**: What's in/out of scope for the initial version?
5. **Success Criteria**: How will we know this project is complete?

Make questions project-specific, not generic. Address the most important unknowns that would impact development decisions.

Format as a numbered list of questions."""

    try:
        return call_llm(questions_prompt)
    except Exception as e:
        typer.echo(f"❌ Failed to generate questions: {e}")
        return None


def _generate_follow_up_questions(initial_prompt: str, previous_qa: List, latest_answers: str, nd_path: Path) -> Optional[str]:
    """Generate follow-up questions based on previous answers."""
    follow_up_prompt = f"""Based on this project discussion so far, determine if additional clarification is needed.

ORIGINAL PROJECT: "{initial_prompt}"

PREVIOUS Q&A HISTORY: {json.dumps(previous_qa, indent=2)}

LATEST ANSWERS: "{latest_answers}"

Analyze the conversation and determine if there are any:
1. Ambiguous or unclear responses that need clarification
2. Missing critical information for implementation
3. Contradictions that need resolution
4. Technical details that weren't addressed

If additional questions are needed, generate 2-4 specific follow-up questions.
If the discussion is sufficiently complete, respond with "DISCUSSION_COMPLETE".

Focus only on the most critical gaps that would impact development."""

    try:
        response = call_llm(follow_up_prompt)
        if "DISCUSSION_COMPLETE" in response.upper():
            return None
        return response
    except Exception as e:
        typer.echo(f"❌ Failed to generate follow-up questions: {e}")
        return None


def _analyze_completeness(initial_prompt: str, conversation_history: List, latest_answers: str) -> bool:
    """Analyze if the discussion is complete or needs more iteration."""
    completeness_prompt = f"""Analyze this project discussion for completeness:

ORIGINAL PROJECT: "{initial_prompt}"

CONVERSATION HISTORY: {json.dumps(conversation_history, indent=2)}

LATEST ANSWERS: "{latest_answers}"

Determine if the discussion provides sufficient information to:
1. Understand the project goals and scope
2. Identify core features and functionality
3. Make technical implementation decisions
4. Define success criteria
5. Begin detailed task planning

Respond with either:
- "COMPLETE" if discussion provides sufficient clarity for development
- "NEEDS_MORE" if critical information is still missing or unclear"""

    try:
        response = call_llm(completeness_prompt)
        return "NEEDS_MORE" in response.upper()
    except Exception:
        # If analysis fails, assume complete to avoid infinite loops
        return False


def _compile_final_specification(conversation_state: Dict) -> str:
    """Compile complete project specification from all conversation iterations."""
    compile_prompt = f"""Based on this complete project discussion, create a comprehensive project specification:

ORIGINAL PROJECT REQUEST: "{conversation_state.get('initial_prompt', '')}"

COMPLETE Q&A HISTORY: {json.dumps(conversation_state.get('conversation_history', []), indent=2)}

Create a detailed project specification that includes:
1. Project Overview and Goals
2. Target Users and Use Cases
3. Core Features and Functionality (prioritized)
4. Technical Requirements and Constraints
5. Success Criteria and Definition of Done
6. Implementation Approach and Architecture
7. Key Assumptions and Dependencies

Be specific and actionable. This specification will be used to generate implementation tasks."""

    try:
        return call_llm(compile_prompt)
    except Exception as e:
        typer.echo(f"❌ Failed to compile specification: {e}")
        return conversation_state.get('initial_prompt', '')


def provide_discussion_answers(answers: str, nd_path: Path) -> bool:
    """
    Allow Navigator to provide answers to discussion questions and continue iteration.
    This function is called by Navigator when Developer provides answers.
    
    Args:
        answers: Developer's answers to the current questions
        nd_path: Path to the .neuro-dock directory
        
    Returns:
        True if successful, False otherwise
    """
    try:
        store = get_store(str(nd_path.parent))
        conversation_state = _load_discussion_state(store)
        
        if conversation_state["status"] != "questions_pending":
            typer.echo(f"❌ No pending questions. Current status: {conversation_state['status']}")
            return False
        
        # Store the answers
        conversation_state["latest_answers"] = answers
        conversation_state["status"] = "awaiting_answers"
        
        # Add answers to conversation history
        if conversation_state.get("conversation_history"):
            current_iteration = conversation_state["conversation_history"][-1]
            current_iteration["answers"] = answers
            current_iteration["answered_timestamp"] = datetime.now().isoformat()
        
        store.add_memory(json.dumps(conversation_state), "discussion_state")
        
        typer.echo("✅ Answers received! Processing and determining next steps...")
        
        # Continue the discussion process
        return _process_answers_and_continue(store, nd_path, conversation_state)
        
    except Exception as e:
        typer.echo(f"❌ Failed to process answers: {e}")
        return False

def get_discussion_status(nd_path: Path) -> Dict[str, Any]:
    """
    Get current discussion status for Navigator to understand what's needed.
    
    Args:
        nd_path: Path to the .neuro-dock directory
        
    Returns:
        Dictionary with current discussion status and next actions
    """
    try:
        store = get_store(str(nd_path.parent))
        conversation_state = _load_discussion_state(store)
        
        status_info = {
            "status": conversation_state.get("status", "new"),
            "iteration": conversation_state.get("iteration", 0),
            "has_pending_questions": conversation_state.get("status") == "questions_pending",
            "current_questions": conversation_state.get("questions", ""),
            "total_iterations": len(conversation_state.get("conversation_history", [])),
            "next_action": _determine_next_action(conversation_state),
            "completion_percentage": _estimate_completion(conversation_state)
        }
        
        return status_info
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "next_action": "restart_discussion"
        }

def _determine_next_action(conversation_state: Dict) -> str:
    """Determine what Navigator should do next."""
    status = conversation_state.get("status", "new")
    
    if status == "new":
        return "run_discuss_command"
    elif status == "questions_pending":
        return "ask_developer_questions"
    elif status == "awaiting_answers":
        return "provide_answers_to_system"
    elif status == "ready_for_planning":
        return "generate_task_plan"
    else:
        return "check_discussion_state"

def _estimate_completion(conversation_state: Dict) -> int:
    """Estimate discussion completion percentage."""
    status = conversation_state.get("status", "new")
    iterations = conversation_state.get("iteration", 0)
    
    if status == "new":
        return 0
    elif status == "questions_pending" and iterations == 1:
        return 25
    elif status == "questions_pending" and iterations > 1:
        return 50 + min(iterations * 10, 25)
    elif status == "ready_for_planning":
        return 90
    else:
        return min(iterations * 20, 80)
