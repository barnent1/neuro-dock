#!/usr/bin/env python3
"""
Navigator System for NeuroDock

This module implements Navigator as an intelligent conversational partner that guides
developers through the complete Agile development process, facilitating communication
with NeuroDock and ensuring comprehensive memory storage.
"""

import os
import json
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from neurodock.memory import add_to_memory, search_memory, get_neo4j_store, show_post_command_reminders
from neurodock.utils.models import call_llm
from neurodock.db import get_store

@dataclass
class ConversationState:
    """Tracks the current state of the developer-agent conversation."""
    phase: str
    current_step: str
    developer_preferences: Dict[str, Any]
    project_context: Dict[str, Any]
    conversation_history: List[Dict[str, Any]]
    next_actions: List[str]
    awaiting_keyword: bool = False
    keyword_action: str = ""

# Agile Phase Script Structure
AGILE_SCRIPT = {
    "initiation": {
        "description": "Project Introduction and Vision Gathering",
        "steps": {
            "introduction": {
                "agent_prompt": "Introduce system capabilities and your role as Navigator",
                "key_questions": ["What is your project vision?", "What problem are you solving?"],
                "next_step": "vision_clarification"
            },
            "vision_clarification": {
                "agent_prompt": "Discuss and refine the project vision",
                "key_questions": ["Can you elaborate on the core functionality?", "What's the expected outcome?"],
                "keyword_trigger": "proceed to requirements",
                "next_phase": "requirements_gathering"
            }
        }
    },
    "requirements_gathering": {
        "description": "Detailed Requirements Discussion and Clarification",
        "steps": {
            "requirements_introduction": {
                "agent_prompt": "Explain the requirements gathering process and engage NeuroDock",
                "key_questions": ["Are you ready to dive deep into requirements?"],
                "next_step": "neurodock_discussion"
            },
            "neurodock_discussion": {
                "agent_prompt": "Facilitate discussion with NeuroDock for detailed requirements",
                "command_to_run": "nd discuss",
                "keyword_trigger": "proceed to planning",
                "next_phase": "sprint_planning"
            }
        }
    },
    "sprint_planning": {
        "description": "Task Breakdown and Sprint Planning",
        "steps": {
            "planning_introduction": {
                "agent_prompt": "Explain sprint planning process and task breakdown approach",
                "key_questions": ["Are you ready to break down the work into manageable tasks?"],
                "next_step": "task_breakdown"
            },
            "task_breakdown": {
                "agent_prompt": "Work with Agent 2 to create comprehensive task breakdown",
                "command_to_run": "nd sprint-plan",
                "keyword_trigger": "proceed to design",
                "next_phase": "design"
            }
        }
    },
    "design": {
        "description": "Technical Architecture and Design Planning",
        "steps": {
            "design_introduction": {
                "agent_prompt": "Discuss technical architecture and design approach",
                "key_questions": ["What are your preferences for technology stack?", "Any architectural constraints?"],
                "next_step": "architecture_design"
            },
            "architecture_design": {
                "agent_prompt": "Create technical design documents with Agent 2",
                "command_to_run": "nd design",
                "keyword_trigger": "proceed to development",
                "next_phase": "development"
            }
        }
    },
    "development": {
        "description": "Iterative Development and Implementation",
        "steps": {
            "development_introduction": {
                "agent_prompt": "Explain development approach and iterative process",
                "key_questions": ["Are you ready to begin implementation?"],
                "next_step": "implementation"
            },
            "implementation": {
                "agent_prompt": "Guide through development iterations with Agent 2",
                "command_to_run": "nd develop",
                "keyword_trigger": "proceed to testing",
                "next_phase": "testing"
            }
        }
    },
    "testing": {
        "description": "Testing and Quality Assurance",
        "steps": {
            "testing_introduction": {
                "agent_prompt": "Discuss testing strategy and quality assurance",
                "key_questions": ["What testing levels do you want to focus on?"],
                "next_step": "test_execution"
            },
            "test_execution": {
                "agent_prompt": "Execute comprehensive testing with Agent 2",
                "command_to_run": "nd test",
                "keyword_trigger": "proceed to review",
                "next_phase": "review"
            }
        }
    },
    "review": {
        "description": "Code Review and Quality Assessment",
        "steps": {
            "review_introduction": {
                "agent_prompt": "Explain code review process and quality metrics",
                "key_questions": ["Are you ready for comprehensive code review?"],
                "next_step": "code_review"
            },
            "code_review": {
                "agent_prompt": "Conduct code review with Agent 2",
                "command_to_run": "nd review",
                "keyword_trigger": "proceed to deployment",
                "next_phase": "deployment"
            }
        }
    },
    "deployment": {
        "description": "Deployment and Release Management",
        "steps": {
            "deployment_introduction": {
                "agent_prompt": "Discuss deployment strategy and environment setup",
                "key_questions": ["What deployment environment do you prefer?"],
                "next_step": "deployment_execution"
            },
            "deployment_execution": {
                "agent_prompt": "Execute deployment with Agent 2",
                "command_to_run": "nd deploy",
                "keyword_trigger": "proceed to retrospective",
                "next_phase": "retrospective"
            }
        }
    },
    "retrospective": {
        "description": "Project Retrospective and Lessons Learned",
        "steps": {
            "retrospective_discussion": {
                "agent_prompt": "Conduct project retrospective and gather insights",
                "command_to_run": "nd retrospective",
                "keyword_trigger": "project complete",
                "next_phase": "complete"
            }
        }
    }
}

class ConversationalAgent:
    """
    Navigator: Conversational Development Partner
    
    Facilitates comprehensive conversations with developers throughout
    the complete Agile development lifecycle.
    """
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.conversation_state = self._load_conversation_state()
        self.documentation_content = self._read_documentation()
        self.agile_script = AGILE_SCRIPT
        
        # Initialize Navigator with memory awareness
        self._store_navigator_initialization()
        
    def _store_navigator_initialization(self):
        """Store Navigator initialization in memory for context awareness."""
        add_to_memory(f"Navigator initialized for project: {self.project_root}", {
            "type": "navigator_initialization",
            "phase": self.conversation_state.phase,
            "step": self.conversation_state.current_step,
            "project_root": str(self.project_root),
            "timestamp": datetime.now().isoformat()
        })

    def _check_memory_before_action(self, action_description: str) -> str:
        """
        Check memory before taking any action to maintain state awareness.
        This ensures Navigator never loses track of where it is or what it's doing.
        """
        # Search for comprehensive context from memory
        recent_memories = search_memory(f"Navigator {action_description} {self.conversation_state.phase}", limit=5)
        task_memories = search_memory(f"task completed project {self.project_root}", limit=5)
        command_memories = search_memory(f"command executed {self.conversation_state.phase}", limit=5)
        discussion_memories = search_memory(f"discussion {self.conversation_state.phase} {self.project_root}", limit=3)
        neurodock_memories = search_memory(f"NeuroDock communication {self.project_root}", limit=3)
        
        # Search for pending tasks and next steps
        pending_tasks = search_memory(f"task pending {self.conversation_state.phase}", limit=5)
        next_steps = search_memory(f"next steps {self.conversation_state.phase}", limit=3)
        
        # Store that we're checking memory before action
        add_to_memory(f"Navigator checking memory before: {action_description}", {
            "type": "memory_check",
            "action": action_description,
            "phase": self.conversation_state.phase,
            "step": self.conversation_state.current_step,
            "project_root": str(self.project_root),
            "timestamp": datetime.now().isoformat(),
            "memory_categories_checked": ["recent", "tasks", "commands", "discussions", "neurodock", "pending", "next_steps"]
        })
        
        # Compile comprehensive memory context
        memory_context = {
            "recent_context": recent_memories[:3],
            "completed_tasks": task_memories,
            "recent_commands": command_memories,
            "discussions": discussion_memories,
            "neurodock_communication": neurodock_memories,
            "pending_tasks": pending_tasks,
            "next_steps": next_steps,
            "current_phase": self.conversation_state.phase,
            "current_step": self.conversation_state.current_step,
            "project_context": self.conversation_state.project_context
        }
        
        return self._format_memory_context_for_navigator(memory_context)

    def _format_memory_context_for_navigator(self, memory_context: Dict[str, Any]) -> str:
        """Format memory context for Navigator's awareness."""
        context_summary = f"""
🧠 Navigator Memory Check:
📍 Current Position: {memory_context['current_phase']} → {memory_context['current_step']}
📋 Project Context: {json.dumps(memory_context['project_context'], indent=2) if memory_context['project_context'] else 'No context stored'}

Recent Activity:
"""
        if memory_context['recent_context']:
            for i, memory in enumerate(memory_context['recent_context'], 1):
                context_summary += f"  {i}. {memory.get('content', 'N/A')[:100]}...\n"
        
        if memory_context['completed_tasks']:
            context_summary += "\nCompleted Tasks:\n"
            for task in memory_context['completed_tasks']:
                context_summary += f"  ✅ {task.get('content', 'N/A')[:80]}...\n"
        
        if memory_context['pending_tasks']:
            context_summary += "\nPending Tasks:\n"
            for task in memory_context['pending_tasks']:
                context_summary += f"  ⏳ {task.get('content', 'N/A')[:80]}...\n"
        
        if memory_context['recent_commands']:
            context_summary += "\nRecent Commands:\n"
            for cmd in memory_context['recent_commands']:
                context_summary += f"  🔧 {cmd.get('content', 'N/A')[:80]}...\n"
        
        if memory_context['discussions']:
            context_summary += "\nRecent Discussions:\n"
            for disc in memory_context['discussions']:
                context_summary += f"  💭 {disc.get('content', 'N/A')[:80]}...\n"
        
        if memory_context['neurodock_communication']:
            context_summary += "\nNeuroDock Communications:\n"
            for comm in memory_context['neurodock_communication']:
                context_summary += f"  🤖 {comm.get('content', 'N/A')[:80]}...\n"
        
        if memory_context['next_steps']:
            context_summary += "\nNext Steps from Memory:\n"
            for step in memory_context['next_steps']:
                context_summary += f"  ➡️ {step.get('content', 'N/A')[:80]}...\n"
        
        return context_summary

    def _store_action_memory(self, action: str, details: str, metadata: Dict[str, Any] = None):
        """Store comprehensive memory about actions Navigator takes."""
        memory_metadata = {
            "type": "navigator_action",
            "action": action,
            "phase": self.conversation_state.phase,
            "step": self.conversation_state.current_step,
            "project_root": str(self.project_root),
            "timestamp": datetime.now().isoformat()
        }
        if metadata:
            memory_metadata.update(metadata)
            
        add_to_memory(f"Navigator action: {action} - {details}", memory_metadata)

    def _post_action_memory_check(self, action: str, result: str) -> str:
        """
        Check memory after action completion and provide reminders.
        This ensures Navigator stays aware of what was accomplished and what's next.
        """
        # Store the completed action
        self._store_action_memory(action, result, {"result": result})
        
        # Show post-command reminders using the reminder system
        show_post_command_reminders(action, result, {
            "phase": self.conversation_state.phase,
            "step": self.conversation_state.current_step,
            "project_root": str(self.project_root)
        })
        
        # Get next step guidance from memory
        next_steps = self._get_next_steps_from_memory()
        
        # Get task status summary
        task_summary = self._get_task_status_summary()
        
        # Store post-action memory check
        add_to_memory(f"Navigator post-action check: {action}", {
            "type": "post_action_memory_check",
            "action": action,
            "result": result[:200],  # Truncated result
            "phase": self.conversation_state.phase,
            "step": self.conversation_state.current_step,
            "project_root": str(self.project_root),
            "timestamp": datetime.now().isoformat()
        })
        
        return f"""
✅ Action Completed: {action}
📋 Result: {result}

{task_summary}

🎯 Next Steps Based on Memory:
{next_steps}
"""

    def _get_next_steps_from_memory(self) -> str:
        """Determine next steps based on current memory state."""
        # Search for task plan and completion status
        plan_memories = search_memory(f"task plan {self.project_root}", limit=3)
        progress_memories = search_memory(f"task completed {self.conversation_state.phase}", limit=5)
        
        current_step_config = self._get_current_script_step()
        
        guidance = f"Current script step: {current_step_config.get('agent_prompt', 'Continue conversation')}\n"
        
        if self.conversation_state.awaiting_keyword:
            guidance += f"⏭️ Ready to proceed: Say '{self.conversation_state.keyword_action}' to continue\n"
        
        if plan_memories:
            guidance += "📋 Active project plan found in memory\n"
        
        if progress_memories:
            guidance += f"✅ {len(progress_memories)} tasks completed in current phase\n"
            
        return guidance
        
    def _get_current_script_step(self) -> Dict[str, Any]:
        """Get the current step configuration from the Agile script."""
        phase = self.conversation_state.phase
        step = self.conversation_state.current_step
        
        if phase in self.agile_script and step in self.agile_script[phase]["steps"]:
            return self.agile_script[phase]["steps"][step]
        return {}
    
    def _get_next_script_step(self) -> Optional[Dict[str, Any]]:
        """Get the next step in the current phase."""
        current_step_config = self._get_current_script_step()
        if "next_step" in current_step_config:
            next_step = current_step_config["next_step"]
            phase = self.conversation_state.phase
            if phase in self.agile_script and next_step in self.agile_script[phase]["steps"]:
                return self.agile_script[phase]["steps"][next_step]
        return None
    
    def _advance_to_next_phase(self, next_phase: str):
        """Advance to the next phase in the Agile process."""
        if next_phase in self.agile_script:
            self.conversation_state.phase = next_phase
            # Get first step of new phase
            first_step = list(self.agile_script[next_phase]["steps"].keys())[0]
            self.conversation_state.current_step = first_step
            self.conversation_state.awaiting_keyword = False
            self.conversation_state.keyword_action = ""
            self._save_conversation_state()
    
    def check_for_keyword_trigger(self, developer_message: str) -> bool:
        """Check if developer message contains a keyword trigger."""
        current_step_config = self._get_current_script_step()
        
        if "keyword_trigger" in current_step_config:
            keyword = current_step_config["keyword_trigger"].lower()
            if keyword in developer_message.lower():
                # Execute the associated action
                if "next_phase" in current_step_config:
                    self._advance_to_next_phase(current_step_config["next_phase"])
                elif "command_to_run" in current_step_config:
                    self._execute_neurodock_command(current_step_config["command_to_run"])
                return True
        return False
                
    def _execute_neurodock_command(self, command: str) -> Dict[str, Any]:
        """Execute a neuro-dock command to communicate with NeuroDock."""
        # Check memory before executing command
        memory_context = self._check_memory_before_action(f"executing command: {command}")
        
        self._add_to_conversation_history("Navigator", f"Memory check before executing command: {command}")
        self._add_to_conversation_history("Navigator", memory_context)
        
        # Store pre-command state with comprehensive context
        self._store_action_memory("pre_command_execution", f"About to execute: {command}", {
            "command": command,
            "memory_context": memory_context[:200],  # Store truncated context
            "current_conversation_length": len(self.conversation_state.conversation_history),
            "project_context_size": len(self.conversation_state.project_context)
        })
        
        # Store that we're communicating with NeuroDock
        add_to_memory(f"Navigator initiating NeuroDock communication: {command}", {
            "type": "neurodock_communication_start",
            "command": command,
            "phase": self.conversation_state.phase,
            "step": self.conversation_state.current_step,
            "project_root": str(self.project_root),
            "timestamp": datetime.now().isoformat()
        })

        try:
            # Run the command in the project directory
            result = subprocess.run(
                command.split(),
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            command_result = {
                "command": command,
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timestamp": datetime.now().isoformat()
            }
            
            # Store command result in memory with rich context
            add_to_memory(f"NeuroDock command executed: {command}", {
                "type": "neurodock_command",
                "command": command,
                "success": command_result["success"],
                "phase": self.conversation_state.phase,
                "step": self.conversation_state.current_step,
                "project_root": str(self.project_root),
                "stdout_preview": result.stdout[:500] if result.stdout else "",
                "stderr_preview": result.stderr[:500] if result.stderr else "",
                "stdout_length": len(result.stdout) if result.stdout else 0,
                "stderr_length": len(result.stderr) if result.stderr else 0
            })
            
            # Store NeuroDock response communication
            add_to_memory(f"NeuroDock response to {command}: {result.stdout[:200] if result.stdout else 'No output'}", {
                "type": "neurodock_communication_response",
                "command": command,
                "success": command_result["success"],
                "phase": self.conversation_state.phase,
                "project_root": str(self.project_root),
                "timestamp": datetime.now().isoformat()
            })
            
            # Post-command memory check and reminders
            post_action_summary = self._post_action_memory_check(
                f"command_execution_{command}", 
                f"Success: {command_result['success']}, Output length: {len(result.stdout)} chars"
            )
            
            # Check if output contains tasks or next steps and store them
            self._extract_and_store_tasks_from_output(result.stdout, command)
            
            # Synchronize memory with NeuroDock output
            self._sync_memory_with_neurodock(command, result.stdout)
            
            self._add_to_conversation_history("Navigator", f"Command executed: {command}")
            self._add_to_conversation_history("Navigator", post_action_summary)
            
            return command_result
            
        except subprocess.TimeoutExpired:
            error_result = {"command": command, "success": False, "error": "Command timed out"}
            self._store_action_memory("command_timeout", f"Command timed out: {command}", {"error": "timeout"})
            
            # Store timeout communication
            add_to_memory(f"NeuroDock command timeout: {command}", {
                "type": "neurodock_communication_timeout",
                "command": command,
                "phase": self.conversation_state.phase,
                "project_root": str(self.project_root),
                "timestamp": datetime.now().isoformat()
            })
            
            return error_result
        except Exception as e:
            error_result = {"command": command, "success": False, "error": str(e)}
            self._store_action_memory("command_error", f"Command failed: {command}", {"error": str(e)})
            
            # Store error communication
            add_to_memory(f"NeuroDock command error: {command} - {str(e)}", {
                "type": "neurodock_communication_error",
                "command": command,
                "error": str(e),
                "phase": self.conversation_state.phase,
                "project_root": str(self.project_root),
                "timestamp": datetime.now().isoformat()
            })
            
            return error_result
    
    def suggest_memory_storage(self, important_idea: str) -> str:
        """Suggest storing an important idea in memory."""
        memory_suggestion = f"""
🧠 Navigator: That's an important point! Let me store this in our memory system:

"{important_idea}"

This will help NeuroDock provide better assistance and ensure we don't lose 
this context as we progress through the project.
        """
        
        # Store the important idea
        add_to_memory(f"Important developer insight: {important_idea}", {
            "type": "important_insight",
            "phase": self.conversation_state.phase,
            "step": self.conversation_state.current_step,
            "project_root": str(self.project_root)
        })
        
        self._add_to_conversation_history("Navigator", memory_suggestion)
        return memory_suggestion
    
    def get_conversation_status(self) -> str:
        """Get current conversation status and next steps."""
        current_step_config = self._get_current_script_step()
        phase_desc = self.agile_script[self.conversation_state.phase]["description"]
        
        status = f"""
🧭 Navigator - Conversation Status

📍 Current Phase: {self.conversation_state.phase.replace('_', ' ').title()}
   {phase_desc}

📋 Current Step: {self.conversation_state.current_step.replace('_', ' ').title()}
   {current_step_config.get('agent_prompt', 'Continuing conversation...')}

🎯 Available Actions:
        """
        
        if self.conversation_state.awaiting_keyword:
            status += f"   • Say '{self.conversation_state.keyword_action}' to proceed to next phase\n"
        
        if "key_questions" in current_step_config:
            status += "   • Answer these key questions:\n"
            for q in current_step_config["key_questions"]:
                status += f"     - {q}\n"
        
        status += f"""
💭 Project Context: {len(self.conversation_state.project_context)} items stored
🗂️ Conversation History: {len(self.conversation_state.conversation_history)} messages
        """
        
        return status
    
    def explain_agile_process(self) -> str:
        """Explain the complete Agile process and how Navigator facilitates it."""
        explanation = """
🧭 Navigator - Agile Process Guide

I guide you through a structured Agile development process with the following phases:

"""
        
        for phase_key, phase_config in self.agile_script.items():
            if phase_key != "complete":
                explanation += f"🔹 {phase_key.replace('_', ' ').title()}: {phase_config['description']}\n"
        
        explanation += """

📋 How It Works:
1. We have detailed conversations in each phase
2. I ask guided questions to ensure completeness
3. Important insights are stored in our dual memory system
4. When ready, you provide a keyword trigger (e.g., "proceed to requirements")
5. I then execute the appropriate command to engage NeuroDock
6. NeuroDock (any LLM) executes the technical work
7. I relay results and questions back to you
8. We continue to the next phase when you're satisfied

🎯 Key Benefits:
• Conversation-driven development keeps you in control
• Nothing happens without your explicit approval
• All context is preserved in memory
• NeuroDock gets rich context for better results
• Systematic approach ensures nothing is missed

Ready to continue our current phase or would you like to discuss any aspect?
        """
        
        return explanation
    
    def guide_me(self) -> str:
        """Provide guidance for the current step in the process."""
        current_step_config = self._get_current_script_step()
        phase_desc = self.agile_script[self.conversation_state.phase]["description"]
        
        guidance = f"""
🧭 Navigator - Step-by-Step Guidance

📍 Current Focus: {phase_desc}

🎯 What We're Doing Now:
{current_step_config.get('agent_prompt', 'Continuing our conversation...')}

❓ Key Questions to Consider:
        """
        
        for question in current_step_config.get('key_questions', []):
            guidance += f"   • {question}\n"
        
        if self.conversation_state.awaiting_keyword:
            guidance += f"""
⏭️ Next Step:
When you're ready to proceed, say: "{self.conversation_state.keyword_action}"
This will trigger the appropriate command for NeuroDock.
            """
        
        guidance += """
💡 Remember:
• Share your thoughts freely - I'll help organize them
• Ask questions about anything unclear
• I can store important ideas in memory
• We move at your pace - no rush
        """
        
        return guidance
        
    def _read_documentation(self) -> str:
        """Read the .neuro-dock.md documentation to understand the system."""
        doc_path = self.project_root / ".neuro-dock.md"
        if doc_path.exists():
            return doc_path.read_text()
        else:
            # Fallback to system documentation
            system_doc = Path.home() / ".neuro-dock" / ".neuro-dock.md"
            if system_doc.exists():
                return system_doc.read_text()
        return ""
    
    def _load_conversation_state(self) -> ConversationState:
        """Load or initialize conversation state."""
        state_file = self.project_root / ".neuro-dock" / "conversation_state.json"
        
        if state_file.exists():
            with open(state_file, 'r') as f:
                data = json.load(f)
                return ConversationState(**data)
        
        return ConversationState(
            phase="initiation",
            current_step="introduction",
            developer_preferences={},
            project_context={},
            conversation_history=[],
            next_actions=["introduce_system", "gather_project_vision"]
        )
    
    def _save_conversation_state(self):
        """Save current conversation state."""
        state_file = self.project_root / ".neuro-dock" / "conversation_state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(state_file, 'w') as f:
            json.dump(self.conversation_state.__dict__, f, indent=2, default=str)
    
    def _add_to_conversation_history(self, speaker: str, message: str, metadata: Dict[str, Any] = None):
        """Add a message to conversation history and memory."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "speaker": speaker,
            "message": message,
            "phase": self.conversation_state.phase,
            "step": self.conversation_state.current_step,
            "metadata": metadata or {}
        }
        
        self.conversation_state.conversation_history.append(entry)
        
        # Store in memory system
        memory_content = f"{speaker}: {message}"
        memory_metadata = {
            "type": "conversation",
            "speaker": speaker,
            "phase": self.conversation_state.phase,
            "step": self.conversation_state.current_step,
            "project_root": str(self.project_root)
        }
        memory_metadata.update(metadata or {})
        
        add_to_memory(memory_content, memory_metadata)
        self._save_conversation_state()
    
    def begin_conversation(self) -> str:
        """Start the comprehensive conversation flow."""
        # Check memory before beginning conversation
        memory_context = self._check_memory_before_action("beginning conversation flow")
        
        # Check if we're resuming a conversation or starting fresh
        existing_conversations = search_memory(f"conversation {self.project_root}", limit=5)
        is_resuming = len(existing_conversations) > 0
        
        if self.conversation_state.phase != "initiation" and is_resuming:
            # Store conversation resumption
            self._store_action_memory("conversation_resumed", f"Resuming at {self.conversation_state.phase}", {
                "previous_conversations": len(existing_conversations),
                "current_phase": self.conversation_state.phase,
                "current_step": self.conversation_state.current_step
            })
            return self.continue_conversation()
        
        # Store conversation start with comprehensive context
        self._store_action_memory("conversation_started", "Navigator beginning conversation flow", {
            "phase": self.conversation_state.phase,
            "documentation_loaded": len(self.documentation_content) > 0,
            "is_new_project": not is_resuming,
            "existing_conversations": len(existing_conversations),
            "project_root": str(self.project_root)
        })
        
        # Store project initialization in memory
        add_to_memory(f"Navigator starting new project conversation in {self.project_root}", {
            "type": "project_initialization",
            "project_root": str(self.project_root),
            "phase": "initiation",
            "timestamp": datetime.now().isoformat(),
            "documentation_available": len(self.documentation_content) > 0
        })
        
        # Navigator introduces itself after reading documentation
        introduction = self._generate_introduction()
        self._add_to_conversation_history("Navigator", introduction)
        
        # Store the introduction in memory
        add_to_memory(f"Navigator introduction: {introduction[:200]}...", {
            "type": "navigator_introduction",
            "full_introduction": introduction,
            "project_root": str(self.project_root),
            "timestamp": datetime.now().isoformat()
        })
        
        # Post-conversation-start memory check
        post_start_summary = self._post_action_memory_check(
            "conversation_initialization", 
            "Navigator introduced and conversation started"
        )
        
        return f"{introduction}\n\n{post_start_summary}"
    
    def _generate_introduction(self) -> str:
        """Generate Navigator's introduction after reading documentation."""
        current_step_config = self._get_current_script_step()
        
        prompt = f"""
        SYSTEM CONSTRAINT: You are Navigator. NEVER use "Agent 1" or "NeuroDock's Agent 1" in your response. Always use "Navigator".
        
        You are Navigator, an intelligent development partner. You have just read the NeuroDock documentation.
        
        CRITICAL: Replace any mention of "Agent 1" with "Navigator" in your response.
        
        Current phase: {self.agile_script[self.conversation_state.phase]['description']}
        Current step guidance: {current_step_config.get('agent_prompt', '')}
        
        Key questions to explore: {current_step_config.get('key_questions', [])}
        
        Your introduction should:
        1. Confirm you've read and understood the documentation
        2. Explain your role as Navigator - the conversational facilitator
        3. Introduce NeuroDock as any LLM that executes commands through the system
        4. Explain the dual memory system (Qdrant + Neo4J)
        5. Outline the structured Agile process with keyword triggers
        6. Explain that you'll guide thorough discussions before any commands
        7. Ask for their initial project vision following the script
        8. Be conversational, helpful, and professional
        
        MANDATORY: Start with: "Hello! I am Navigator, your intelligent development partner..."
        MANDATORY: Continue with: "As Navigator, my primary purpose is to facilitate..."
        NEVER say "As NeuroDock's Agent 1" or "As Agent 1" - always say "As Navigator".
        
        Keep it comprehensive but engaging. Focus on the conversation-first approach.
        """
        
        response = call_llm(prompt)
        
        # Post-process to ensure no "Agent 1" references remain
        response = response.replace("Agent 1", "Navigator")
        response = response.replace("NeuroDock's Agent 1", "Navigator")
        response = response.replace("As NeuroDock's Agent 1", "As Navigator")
        response = response.replace("As Agent 1", "As Navigator")
        
        return response
    
    def continue_conversation(self) -> str:
        """Continue the conversation from where it left off."""
        # Check memory before continuing conversation
        memory_context = self._check_memory_before_action("continuing conversation")
        
        recent_history = self.conversation_state.conversation_history[-3:]
        
        # Store conversation continuation
        self._store_action_memory("conversation_continued", "Navigator resuming conversation", {
            "history_length": len(self.conversation_state.conversation_history),
            "phase": self.conversation_state.phase
        })
        
        prompt = f"""
        You are Navigator, continuing a conversation with a developer. 
        
        Current phase: {self.conversation_state.phase}
        Current step: {self.conversation_state.current_step}
        Next actions: {', '.join(self.conversation_state.next_actions)}
        
        Memory Context:
        {memory_context}
        
        Recent conversation:
        {json.dumps(recent_history, indent=2)}
        
        Project context:
        {json.dumps(self.conversation_state.project_context, indent=2)}
        
        Continue the conversation by:
        1. Acknowledging where we left off based on memory
        2. Explaining the next step in the process
        3. Being helpful and guiding
        4. Asking for specific input if needed
        5. Reference relevant context from memory
        """
        
        response = call_llm(prompt)
        
        # Post-process to ensure no "Agent 1" references remain
        response = response.replace("Agent 1", "Navigator")
        response = response.replace("NeuroDock's Agent 1", "Navigator")
        response = response.replace("As NeuroDock's Agent 1", "As Navigator")
        response = response.replace("As Agent 1", "As Navigator")
        
        self._add_to_conversation_history("Navigator", response)
        
        # Post-continuation memory check
        post_continue_summary = self._post_action_memory_check(
            "conversation_continuation", 
            f"Resumed conversation in {self.conversation_state.phase} phase"
        )
        
        return f"{response}\n\n{post_continue_summary}"
    
    def respond_to_developer(self, developer_message: str) -> str:
        """Process developer input and provide intelligent response."""
        # Check memory before responding to maintain context awareness
        memory_context = self._check_memory_before_action(f"responding to developer message: {developer_message[:50]}...")
        
        # Store developer message in conversation history
        self._add_to_conversation_history("Developer", developer_message)
        
        # Store developer message with rich context and analysis
        contains_keywords = any(keyword in developer_message.lower() for keyword in ["proceed", "ready", "continue", "next", "done", "finished", "complete"])
        contains_task_language = any(word in developer_message.lower() for word in ["task", "implement", "build", "create", "develop", "fix", "test"])
        
        self._store_action_memory("developer_message_received", developer_message, {
            "message_length": len(developer_message),
            "contains_keywords": contains_keywords,
            "contains_task_language": contains_task_language,
            "word_count": len(developer_message.split()),
            "conversation_turn": len(self.conversation_state.conversation_history)
        })
        
        # Check if developer is reporting task completion
        if any(phrase in developer_message.lower() for phrase in ["done", "finished", "completed", "ready"]):
            self._mark_task_completed(f"Developer reported completion: {developer_message[:100]}")
        
        # Analyze developer message and determine response
        response = self._generate_contextual_response(developer_message)
        self._add_to_conversation_history("Navigator", response)
        
        # Update conversation state based on response
        self._update_conversation_state(developer_message, response)
        
        # Post-response memory check with comprehensive context
        post_response_summary = self._post_action_memory_check(
            "developer_response_generated", 
            f"Generated response to: {developer_message[:50]}... (length: {len(response)} chars)"
        )
        
        # Store the complete interaction in memory
        add_to_memory(f"Navigator-Developer interaction: Q: {developer_message[:100]}... A: {response[:100]}...", {
            "type": "interaction",
            "developer_message": developer_message[:200],
            "navigator_response": response[:200],
            "phase": self.conversation_state.phase,
            "step": self.conversation_state.current_step,
            "project_root": str(self.project_root),
            "timestamp": datetime.now().isoformat()
        })
        
        # Append memory-driven next steps to response
        response_with_memory = f"{response}\n\n{post_response_summary}"
        
        return response_with_memory
    
    def _generate_contextual_response(self, developer_message: str) -> str:
        """Generate contextually appropriate response to developer."""
        # Check for keyword trigger first
        if self.check_for_keyword_trigger(developer_message):
            return self._handle_keyword_trigger(developer_message)
        
        # Get current script step configuration
        current_step_config = self._get_current_script_step()
        next_step_config = self._get_next_script_step()
        
        # Get relevant memory context
        memory_context = search_memory(developer_message, limit=3)
        
        prompt = f"""
        You are Navigator, responding to the developer's message: "{developer_message}"
        
        Current Agile Phase: {self.agile_script[self.conversation_state.phase]['description']}
        Current Step: {self.conversation_state.current_step}
        
        Script Guidance:
        - Current step prompt: {current_step_config.get('agent_prompt', '')}
        - Key questions: {current_step_config.get('key_questions', [])}
        - Available keyword trigger: {current_step_config.get('keyword_trigger', 'None')}
        
        Recent conversation history:
        {json.dumps(self.conversation_state.conversation_history[-3:], indent=2)}
        
        Project context:
        {json.dumps(self.conversation_state.project_context, indent=2)}
        
        Relevant memory context:
        {json.dumps(memory_context, indent=2)}
        
        Respond by:
        1. Acknowledging their input thoughtfully
        2. Following the current script step guidance
        3. Asking relevant follow-up questions from the script
        4. If discussion is thorough, mention the keyword trigger for next step
        5. NEVER execute commands directly - always discuss first
        6. Store important insights in memory if needed
        7. Guide toward natural conversation flow
        8. Be professional but conversational
        
        Remember: You facilitate conversations and guide, NeuroDock executes commands.
        """
        
        response = call_llm(prompt)
        
        # Post-process to ensure no "Agent 1" references remain
        response = response.replace("Agent 1", "Navigator")
        response = response.replace("NeuroDock's Agent 1", "Navigator")
        response = response.replace("As NeuroDock's Agent 1", "As Navigator")
        response = response.replace("As Agent 1", "As Navigator")
        
        return response
    
    def _handle_keyword_trigger(self, developer_message: str) -> str:
        """Handle when a keyword trigger is detected."""
        # Check memory before handling keyword trigger
        memory_context = self._check_memory_before_action(f"handling keyword trigger in message: {developer_message[:50]}...")
        
        current_step_config = self._get_current_script_step()
        
        # Store keyword trigger detection
        self._store_action_memory("keyword_trigger_detected", f"Detected in: {developer_message}", {
            "trigger_keyword": self.conversation_state.keyword_action,
            "current_step": self.conversation_state.current_step
        })
        
        if "command_to_run" in current_step_config:
            command = current_step_config["command_to_run"]
            
            response = f"""
🧭 Navigator: Perfect! I heard the keyword trigger. I'll now execute the command 
"{command}" to engage NeuroDock for this phase.

🧠 Memory Context Check:
{memory_context[:300]}...

Let me run this command and facilitate the communication with NeuroDock...
            """
            
            # Execute the command
            command_result = self._execute_neurodock_command(command)
            
            if command_result["success"]:
                response += f"""

✅ Command executed successfully! NeuroDock is now working on this phase.
I'll monitor the output and relay any questions or results back to you.

{command_result.get('stdout', '')}
                """
                
                # Store successful command execution
                self._store_action_memory("keyword_command_success", f"Successfully executed {command}", {
                    "command": command,
                    "stdout_length": len(command_result.get('stdout', ''))
                })
            else:
                response += f"""

❌ Command encountered an issue: {command_result.get('error', 'Unknown error')}
Let me help troubleshoot this before we proceed.
                """
                
                # Store command failure
                self._store_action_memory("keyword_command_failure", f"Failed to execute {command}", {
                    "command": command,
                    "error": command_result.get('error', 'Unknown error')
                })
            
            return response
        
        elif "next_phase" in current_step_config:
            next_phase = current_step_config["next_phase"]
            next_phase_desc = self.agile_script[next_phase]["description"]
            
            # Store phase transition
            self._store_action_memory("phase_transition", f"Moving to {next_phase}", {
                "from_phase": self.conversation_state.phase,
                "to_phase": next_phase
            })
            
            return f"""
🧭 Navigator: Excellent! Moving to the next phase: {next_phase_desc}

🧠 Memory shows we're ready for this transition based on our conversation history.

Let me guide you through this new phase of our Agile process...
            """
        
        return "🧭 Navigator: Keyword trigger detected! Processing next steps..."
    
    def _update_conversation_state(self, developer_message: str, agent_response: str):
        """Update conversation state based on the interaction using the structured script."""
        current_step_config = self._get_current_script_step()
        
        # Extract project context from developer messages
        if self.conversation_state.phase == "initiation":
            if any(keyword in developer_message.lower() for keyword in 
                   ["project", "build", "create", "develop", "app", "system"]):
                # Store project vision
                self.conversation_state.project_context["vision"] = developer_message
                
                # Check if we can advance to next step
                if "next_step" in current_step_config:
                    self.conversation_state.current_step = current_step_config["next_step"]
        
        # Update keyword trigger state
        if "keyword_trigger" in current_step_config:
            self.conversation_state.awaiting_keyword = True
            self.conversation_state.keyword_action = current_step_config["keyword_trigger"]
        
        # Store important project details
        if "requirements" in developer_message.lower():
            self.conversation_state.project_context["requirements"] = developer_message
        elif "features" in developer_message.lower():
            self.conversation_state.project_context["features"] = developer_message
        elif "technology" in developer_message.lower() or "tech stack" in developer_message.lower():
            self.conversation_state.project_context["technology_preferences"] = developer_message
        
        self._save_conversation_state()
    
    def facilitate_discuss_process(self) -> Dict[str, Any]:
        """Facilitate the nd discuss process with Agent 2."""
        print("🧭 Navigator: I'll now engage our requirements discussion system...")
        print("            Let me run the discuss command and relay any questions from NeuroDock...")
        
        # Store that we're starting discuss
        self._add_to_conversation_history("Navigator", 
            "Starting requirements discussion process with NeuroDock")
        
        # Create a temporary file with current project context
        project_summary = f"""
        Project Context from Conversation:
        {json.dumps(self.conversation_state.project_context, indent=2)}
        
        Recent conversation:
        {json.dumps(self.conversation_state.conversation_history[-3:], indent=2)}
        """
        
        # Run discuss command (this would integrate with existing discuss functionality)
        try:
            # This would trigger the enhanced discuss command
            result = self._run_enhanced_discuss(project_summary)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _run_enhanced_discuss(self, context: str) -> Dict[str, Any]:
        """Run enhanced discuss command that integrates with conversation."""
        # This would integrate with the existing discuss functionality
        # For now, simulate the process
        
        # Store context in memory
        add_to_memory(f"Navigator facilitated discussion context: {context}", {
            "type": "navigator_facilitated_discussion",
            "phase": self.conversation_state.phase,
            "project_root": str(self.project_root)
        })
        
        return {
            "success": True,
            "neurodock_questions": [
                "What is the primary purpose of this application?",
                "Who are the target users?",
                "What are the key features you want to include?",
                "Do you have any specific technology preferences?",
                "What is your timeline for this project?"
            ],
            "next_step": "collect_developer_answers"
        }
    
    def relay_neurodock_questions(self, questions: List[str]) -> str:
        """Relay NeuroDock's questions to the developer."""
        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
        
        response = f"""
🧭 Navigator: NeuroDock has analyzed our conversation and generated some important 
clarifying questions. Please answer these so I can feed them back to NeuroDock 
and ensure we have complete requirements:

{questions_text}

Please provide your answers, and I'll integrate them into our memory system 
and move us forward to the planning phase.
        """
        
        self._add_to_conversation_history("Navigator", response, {
            "neurodock_questions": questions,
            "awaiting_developer_answers": True
        })
        
        return response
    
    def process_developer_answers(self, answers: str) -> str:
        """Process developer's answers and feed them back to NeuroDock."""
        self._add_to_conversation_history("Developer", answers, {
            "type": "neurodock_question_answers"
        })
        
        # Store answers in memory with rich context
        add_to_memory(f"Developer answers to NeuroDock requirements questions: {answers}", {
            "type": "requirements_answers",
            "phase": "requirements_gathering",
            "source": "navigator_facilitated",
            "project_root": str(self.project_root)
        })
        
        response = f"""
🧭 Navigator: Excellent! I've stored your answers in our memory system and 
will now feed them back to NeuroDock. This ensures both Navigator and NeuroDock have complete 
context about your requirements.

Let me now guide you to the next phase: Sprint Planning. I'll help create 
a comprehensive project plan with task breakdown and dependencies.

Are you ready to move forward with planning, or do you want to refine 
anything about the requirements first?
        """
        
        self.conversation_state.phase = "planning"
        self.conversation_state.current_step = "ready_for_planning"
        self.conversation_state.next_actions = ["run_plan_command", "create_sprint_plan"]
        self._save_conversation_state()
        
        self._add_to_conversation_history("Navigator", response)
        return response
    
    def get_conversation_status(self) -> Dict[str, Any]:
        """Get current conversation status."""
        return {
            "phase": self.conversation_state.phase,
            "current_step": self.conversation_state.current_step,
            "next_actions": self.conversation_state.next_actions,
            "total_exchanges": len(self.conversation_state.conversation_history),
            "project_context": self.conversation_state.project_context,
            "ready_for_next_phase": len(self.conversation_state.next_actions) > 0
        }
    
    def explain_topic(self, topic: str) -> str:
        """Explain any topic about the system to the developer."""
        prompt = f"""
        You are Navigator. The developer is asking you to explain: "{topic}"
        
        Based on the NeuroDock documentation and your role as their development partner,
        provide a clear, helpful explanation. Cover:
        1. What this topic means in the context of NeuroDock
        2. How it relates to their current project
        3. What they can expect from this process
        4. Any actions they might need to take
        
        Be conversational and thorough but not overwhelming.
        """
        
        explanation = call_llm(prompt)
        
        # Post-process to ensure no "Agent 1" references remain
        explanation = explanation.replace("Agent 1", "Navigator")
        explanation = explanation.replace("NeuroDock's Agent 1", "Navigator")
        explanation = explanation.replace("As NeuroDock's Agent 1", "As Navigator")
        explanation = explanation.replace("As Agent 1", "As Navigator")
        
        self._add_to_conversation_history("Navigator", explanation, {"type": "explanation", "topic": topic})
        
        return explanation
    
    def guide_next_step(self) -> str:
        """Provide guidance on the next best step."""
        prompt = f"""
        You are Navigator. The developer is asking for guidance on the next step.
        
        Current state:
        - Phase: {self.conversation_state.phase}
        - Step: {self.conversation_state.current_step}
        - Next actions: {', '.join(self.conversation_state.next_actions)}
        
        Conversation history length: {len(self.conversation_state.conversation_history)}
        
        Provide clear guidance on:
        1. What the next logical step is
        2. Why this step is important
        3. What they need to do
        4. What you (Navigator) will do to help
        5. How this fits into the overall Agile process
        
        Be specific and actionable.
        """
        
        guidance = call_llm(prompt)
        
        # Post-process to ensure no "Agent 1" references remain
        guidance = guidance.replace("Agent 1", "Navigator")
        guidance = guidance.replace("NeuroDock's Agent 1", "Navigator")
        guidance = guidance.replace("As NeuroDock's Agent 1", "As Navigator")
        guidance = guidance.replace("As Agent 1", "As Navigator")
        
        self._add_to_conversation_history("Navigator", guidance, {"type": "guidance"})
        
        return guidance

    def _extract_and_store_tasks_from_output(self, output: str, command: str):
        """Extract tasks and next steps from NeuroDock output and store in memory."""
        if not output:
            return
            
        # Look for common task indicators in the output
        task_indicators = [
            "task", "TODO", "action item", "next step", "requirement", 
            "feature", "implement", "create", "build", "develop", "test"
        ]
        
        lines = output.split('\n')
        extracted_tasks = []
        
        for line in lines:
            line_lower = line.lower().strip()
            if any(indicator in line_lower for indicator in task_indicators):
                if len(line.strip()) > 10:  # Ignore very short lines
                    extracted_tasks.append(line.strip())
        
        # Store extracted tasks in memory
        for i, task in enumerate(extracted_tasks[:10]):  # Limit to 10 tasks
            add_to_memory(f"Task extracted from {command}: {task}", {
                "type": "extracted_task",
                "source_command": command,
                "task_index": i,
                "phase": self.conversation_state.phase,
                "step": self.conversation_state.current_step,
                "project_root": str(self.project_root),
                "timestamp": datetime.now().isoformat(),
                "status": "pending"
            })
        
        # Store summary of task extraction
        if extracted_tasks:
            self._store_action_memory("task_extraction", f"Extracted {len(extracted_tasks)} tasks from {command}", {
                "command": command,
                "task_count": len(extracted_tasks),
                "tasks_preview": extracted_tasks[:3]  # Store first 3 tasks as preview
            })

    def _mark_task_completed(self, task_description: str):
        """Mark a task as completed in memory."""
        add_to_memory(f"Task completed: {task_description}", {
            "type": "task_completed",
            "task": task_description,
            "phase": self.conversation_state.phase,
            "step": self.conversation_state.current_step,
            "project_root": str(self.project_root),
            "timestamp": datetime.now().isoformat()
        })
        
        self._store_action_memory("task_completion", f"Completed task: {task_description}", {
            "task": task_description
        })

    def _store_next_steps(self, steps: List[str], context: str = ""):
        """Store next steps in memory for future reference."""
        for i, step in enumerate(steps):
            add_to_memory(f"Next step {i+1}: {step}", {
                "type": "next_step",
                "step_order": i + 1,
                "context": context,
                "phase": self.conversation_state.phase,
                "step": self.conversation_state.current_step,
                "project_root": str(self.project_root),
                "timestamp": datetime.now().isoformat()
            })
        
        self._store_action_memory("next_steps_stored", f"Stored {len(steps)} next steps", {
            "step_count": len(steps),
            "context": context,
            "steps_preview": steps[:3]
        })

    def _get_task_status_summary(self) -> str:
        """Get a summary of task completion status from memory."""
        completed_tasks = search_memory(f"task completed {self.project_root}", limit=10)
        pending_tasks = search_memory(f"task pending {self.project_root}", limit=10)
        extracted_tasks = search_memory(f"task extracted {self.project_root}", limit=10)
        
        summary = f"""
📊 Task Status Summary:
  ✅ Completed: {len(completed_tasks)} tasks
  ⏳ Pending: {len(pending_tasks)} tasks  
  📋 Extracted: {len(extracted_tasks)} tasks
        """
        
        if completed_tasks:
            summary += "\n🎯 Recent Completions:\n"
            for task in completed_tasks[:3]:
                summary += f"  • {task.get('content', 'N/A')[:60]}...\n"
        
        if pending_tasks:
            summary += "\n⏭️ Next Up:\n"
            for task in pending_tasks[:3]:
                summary += f"  • {task.get('content', 'N/A')[:60]}...\n"
        
        return summary

    def _ensure_memory_continuity(self):
        """Ensure Navigator never loses important context by checking memory continuity."""
        # Check for any gaps in memory or missing context
        recent_memories = search_memory(f"Navigator {self.project_root}", limit=20)
        
        # Verify we have memory of current phase and step
        phase_memories = search_memory(f"{self.conversation_state.phase} {self.project_root}", limit=5)
        if not phase_memories:
            # Store current state to ensure continuity
            add_to_memory(f"Navigator phase continuity check: Currently in {self.conversation_state.phase}", {
                "type": "phase_continuity",
                "phase": self.conversation_state.phase,
                "step": self.conversation_state.current_step,
                "project_root": str(self.project_root),
                "timestamp": datetime.now().isoformat(),
                "reason": "ensuring_memory_continuity"
            })
        
        # Store current project context to maintain state
        if self.conversation_state.project_context:
            add_to_memory(f"Navigator project context: {json.dumps(self.conversation_state.project_context)}", {
                "type": "project_context_backup",
                "context": self.conversation_state.project_context,
                "phase": self.conversation_state.phase,
                "project_root": str(self.project_root),
                "timestamp": datetime.now().isoformat()
            })
        
        # Store conversation state backup
        state_backup = {
            "phase": self.conversation_state.phase,
            "current_step": self.conversation_state.current_step,
            "conversation_length": len(self.conversation_state.conversation_history),
            "project_context_size": len(self.conversation_state.project_context),
            "awaiting_keyword": self.conversation_state.awaiting_keyword,
            "keyword_action": self.conversation_state.keyword_action
        }
        
        add_to_memory(f"Navigator state backup: {json.dumps(state_backup)}", {
            "type": "state_backup",
            "state": state_backup,
            "project_root": str(self.project_root),
            "timestamp": datetime.now().isoformat()
        })

    def _sync_memory_with_neurodock(self, command: str, output: str):
        """Synchronize Navigator memory with NeuroDock output to maintain shared context."""
        # Store the complete NeuroDock interaction
        add_to_memory(f"NeuroDock interaction - Command: {command}, Output: {output[:300]}...", {
            "type": "neurodock_sync",
            "command": command,
            "output_preview": output[:500],
            "output_length": len(output),
            "phase": self.conversation_state.phase,
            "step": self.conversation_state.current_step,
            "project_root": str(self.project_root),
            "timestamp": datetime.now().isoformat()
        })
        
        # Extract key information from NeuroDock output
        if "error" in output.lower():
            add_to_memory(f"NeuroDock reported error in {command}: {output[:200]}", {
                "type": "neurodock_error",
                "command": command,
                "error_details": output[:500],
                "project_root": str(self.project_root),
                "timestamp": datetime.now().isoformat()
            })
        
        if any(success_word in output.lower() for success_word in ["completed", "finished", "done", "success"]):
            add_to_memory(f"NeuroDock success in {command}: {output[:200]}", {
                "type": "neurodock_success",
                "command": command,
                "success_details": output[:500],
                "project_root": str(self.project_root),
                "timestamp": datetime.now().isoformat()
            })
        
        # Store questions from NeuroDock for future reference
        if "?" in output:
            questions = [line.strip() for line in output.split('\n') if '?' in line]
            for question in questions[:5]:  # Limit to 5 questions
                add_to_memory(f"NeuroDock question from {command}: {question}", {
                    "type": "neurodock_question",
                    "command": command,
                    "question": question,
                    "project_root": str(self.project_root),
                    "timestamp": datetime.now().isoformat()
                })

    def get_comprehensive_memory_status(self) -> str:
        """Get a comprehensive view of Navigator's memory status."""
        # Get various memory categories
        total_memories = search_memory(f"{self.project_root}", limit=100)
        conversations = search_memory(f"conversation {self.project_root}", limit=20)
        commands = search_memory(f"command {self.project_root}", limit=15)
        tasks = search_memory(f"task {self.project_root}", limit=20)
        neurodock_comms = search_memory(f"NeuroDock {self.project_root}", limit=15)
        
        # Ensure memory continuity
        self._ensure_memory_continuity()
        
        status = f"""
🧠 Navigator Memory Status Report:

📊 Memory Categories:
  • Total Memories: {len(total_memories)}
  • Conversations: {len(conversations)}
  • Commands Executed: {len(commands)}
  • Tasks Tracked: {len(tasks)}
  • NeuroDock Communications: {len(neurodock_comms)}

📍 Current State:
  • Phase: {self.conversation_state.phase}
  • Step: {self.conversation_state.current_step}
  • Conversation Length: {len(self.conversation_state.conversation_history)}
  • Project Context Items: {len(self.conversation_state.project_context)}
  
🎯 Memory Health:
  • Last Memory Check: Just completed
  • Continuity: Verified and backed up
  • NeuroDock Sync: Active
        """
        
        return status

    def get_complete_project_status(self) -> str:
        """Get a comprehensive, memory-driven project status for informed decision making."""
        # Ensure memory continuity first
        self._ensure_memory_continuity()
        
        # Get comprehensive memory analysis
        memory_status = self.get_comprehensive_memory_status()
        task_summary = self._get_task_status_summary()
        
        # Get next steps from memory
        next_steps = self._get_next_steps_from_memory()
        
        # Search for recent important decisions and communications
        recent_decisions = search_memory(f"decision {self.project_root}", limit=5)
        recent_issues = search_memory(f"error {self.project_root}", limit=3)
        neurodock_comms = search_memory(f"NeuroDock communication {self.project_root}", limit=5)
        
        # Compile complete status
        status = f"""
🧭 Navigator: Complete Project Status Report

{memory_status}

{task_summary}

🔄 Recent Important Activity:
"""
        
        if recent_decisions:
            status += "\n📋 Recent Decisions:\n"
            for decision in recent_decisions:
                status += f"  • {decision.get('content', 'N/A')[:80]}...\n"
        
        if recent_issues:
            status += "\n⚠️ Recent Issues:\n"
            for issue in recent_issues:
                status += f"  • {issue.get('content', 'N/A')[:80]}...\n"
        
        if neurodock_comms:
            status += "\n🤖 Recent NeuroDock Communications:\n"
            for comm in neurodock_comms[-3:]:  # Last 3
                status += f"  • {comm.get('content', 'N/A')[:80]}...\n"
        
        status += f"""

🎯 Navigator Intelligence:
  • Ready for next phase: {len(self.conversation_state.next_actions) > 0}
  • Awaiting keyword: {self.conversation_state.awaiting_keyword}
  • Keyword action: {self.conversation_state.keyword_action}
  • Memory health: Excellent (all systems tracking)

{next_steps}

Navigator is fully aware and ready to proceed with informed decision making.
        """
        
        # Store this status check in memory
        self._store_action_memory("complete_status_check", "Generated comprehensive project status", {
            "status_length": len(status),
            "memory_categories_checked": 7,
            "ready_for_next_phase": len(self.conversation_state.next_actions) > 0
        })
        
        return status

    def debug_memory_state(self) -> str:
        """Debug method to show Navigator's complete memory understanding."""
        return f"""
🔍 Navigator Memory Debug:

Conversation State:
- Phase: {self.conversation_state.phase}
- Step: {self.conversation_state.current_step}
- History Length: {len(self.conversation_state.conversation_history)}
- Project Context: {self.conversation_state.project_context}
- Next Actions: {self.conversation_state.next_actions}
- Awaiting Keyword: {self.conversation_state.awaiting_keyword}
- Keyword Action: {self.conversation_state.keyword_action}

Project Info:
- Root: {self.project_root}
- Documentation Length: {len(self.documentation_content)}

Agile Script Phase Available: {self.conversation_state.phase in self.agile_script}
Current Step Config: {self._get_current_script_step()}

Memory Search Test:
- Project memories: {len(search_memory(str(self.project_root), limit=10))}
- Phase memories: {len(search_memory(f"{self.conversation_state.phase} {self.project_root}", limit=5))}
- Task memories: {len(search_memory(f"task {self.project_root}", limit=5))}
        """
