#!/usr/bin/env python3
"""
Conversational Agent 1 System for NeuroDock

This module implements Agent 1 as an intelligent conversational partner that guides
developers through the complete Agile development process, facilitating communication
with Agent 2 and ensuring comprehensive memory storage.
"""

import os
import json
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from neurodock.memory import add_to_memory, search_memory
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
                "agent_prompt": "Introduce system capabilities and your role as Agent 1",
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
                "agent_prompt": "Explain the requirements gathering process and engage Agent 2",
                "key_questions": ["Are you ready to dive deep into requirements?"],
                "next_step": "agent2_discussion"
            },
            "agent2_discussion": {
                "agent_prompt": "Facilitate discussion with Agent 2 for detailed requirements",
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
    Agent 1: Conversational Development Partner
    
    Facilitates comprehensive conversations with developers throughout
    the complete Agile development lifecycle.
    """
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.conversation_state = self._load_conversation_state()
        self.documentation_content = self._read_documentation()
        self.agile_script = AGILE_SCRIPT
        
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
                    self._execute_agent2_command(current_step_config["command_to_run"])
    def _execute_agent2_command(self, command: str) -> Dict[str, Any]:
        """Execute a neuro-dock command to communicate with Agent 2."""
        self._add_to_conversation_history("Agent1", f"Executing command: {command}")
        
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
            
            # Store command result in memory
            add_to_memory(f"Agent 2 command executed: {command}", {
                "type": "agent2_command",
                "command": command,
                "success": command_result["success"],
                "phase": self.conversation_state.phase,
                "project_root": str(self.project_root)
            })
            
            return command_result
            
        except subprocess.TimeoutExpired:
            return {"command": command, "success": False, "error": "Command timed out"}
        except Exception as e:
            return {"command": command, "success": False, "error": str(e)}
    
    def suggest_memory_storage(self, important_idea: str) -> str:
        """Suggest storing an important idea in memory."""
        memory_suggestion = f"""
🧠 Agent 1: That's an important point! Let me store this in our memory system:

"{important_idea}"

This will help Agent 2 provide better assistance and ensure we don't lose 
this context as we progress through the project.
        """
        
        # Store the important idea
        add_to_memory(f"Important developer insight: {important_idea}", {
            "type": "important_insight",
            "phase": self.conversation_state.phase,
            "step": self.conversation_state.current_step,
            "project_root": str(self.project_root)
        })
        
        self._add_to_conversation_history("Agent1", memory_suggestion)
        return memory_suggestion
    
    def get_conversation_status(self) -> str:
        """Get current conversation status and next steps."""
        current_step_config = self._get_current_script_step()
        phase_desc = self.agile_script[self.conversation_state.phase]["description"]
        
        status = f"""
🤖 Agent 1 - Conversation Status

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
        """Explain the complete Agile process and how Agent 1 facilitates it."""
        explanation = """
🤖 Agent 1 - Agile Process Guide

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
5. I then execute the appropriate command to engage Agent 2
6. Agent 2 (any LLM) executes the technical work
7. I relay results and questions back to you
8. We continue to the next phase when you're satisfied

🎯 Key Benefits:
• Conversation-driven development keeps you in control
• Nothing happens without your explicit approval
• All context is preserved in memory
• Agent 2 gets rich context for better results
• Systematic approach ensures nothing is missed

Ready to continue our current phase or would you like to discuss any aspect?
        """
        
        return explanation
    
    def guide_me(self) -> str:
        """Provide guidance for the current step in the process."""
        current_step_config = self._get_current_script_step()
        phase_desc = self.agile_script[self.conversation_state.phase]["description"]
        
        guidance = f"""
🤖 Agent 1 - Step-by-Step Guidance

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
This will trigger the appropriate command for Agent 2.
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
        if self.conversation_state.phase != "initiation":
            return self.continue_conversation()
        
        # Agent 1 introduces itself after reading documentation
        introduction = self._generate_introduction()
        self._add_to_conversation_history("Agent1", introduction)
        
        return introduction
    
    def _generate_introduction(self) -> str:
        """Generate Agent 1's introduction after reading documentation."""
        current_step_config = self._get_current_script_step()
        
        prompt = f"""
        You are Agent 1, an intelligent development partner. You have just read the NeuroDock documentation.
        
        Current phase: {self.agile_script[self.conversation_state.phase]['description']}
        Current step guidance: {current_step_config.get('agent_prompt', '')}
        
        Key questions to explore: {current_step_config.get('key_questions', [])}
        
        Your introduction should:
        1. Confirm you've read and understood the documentation
        2. Explain your role as Agent 1 - the conversational facilitator
        3. Introduce Agent 2 as any LLM that executes commands through the system
        4. Explain the dual memory system (Qdrant + Neo4J)
        5. Outline the structured Agile process with keyword triggers
        6. Explain that you'll guide thorough discussions before any commands
        7. Ask for their initial project vision following the script
        8. Be conversational, helpful, and professional
        
        Keep it comprehensive but engaging. Focus on the conversation-first approach.
        """
        
        return call_llm(prompt)
    
    def continue_conversation(self) -> str:
        """Continue the conversation from where it left off."""
        recent_history = self.conversation_state.conversation_history[-3:]
        
        prompt = f"""
        You are Agent 1, continuing a conversation with a developer. 
        
        Current phase: {self.conversation_state.phase}
        Current step: {self.conversation_state.current_step}
        Next actions: {', '.join(self.conversation_state.next_actions)}
        
        Recent conversation:
        {json.dumps(recent_history, indent=2)}
        
        Project context:
        {json.dumps(self.conversation_state.project_context, indent=2)}
        
        Continue the conversation by:
        1. Acknowledging where we left off
        2. Explaining the next step in the process
        3. Being helpful and guiding
        4. Asking for specific input if needed
        """
        
        response = call_llm(prompt)
        self._add_to_conversation_history("Agent1", response)
        return response
    
    def respond_to_developer(self, developer_message: str) -> str:
        """Process developer input and provide intelligent response."""
        self._add_to_conversation_history("Developer", developer_message)
        
        # Analyze developer message and determine response
        response = self._generate_contextual_response(developer_message)
        self._add_to_conversation_history("Agent1", response)
        
        # Update conversation state based on response
        self._update_conversation_state(developer_message, response)
        
        return response
    
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
        You are Agent 1, responding to the developer's message: "{developer_message}"
        
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
        
        Remember: You facilitate conversations and guide, Agent 2 executes commands.
        """
        
        return call_llm(prompt)
    
    def _handle_keyword_trigger(self, developer_message: str) -> str:
        """Handle when a keyword trigger is detected."""
        current_step_config = self._get_current_script_step()
        
        if "command_to_run" in current_step_config:
            command = current_step_config["command_to_run"]
            
            response = f"""
🤖 Agent 1: Perfect! I heard the keyword trigger. I'll now execute the command 
"{command}" to engage Agent 2 for this phase.

Let me run this command and facilitate the communication with Agent 2...
            """
            
            # Execute the command
            command_result = self._execute_agent2_command(command)
            
            if command_result["success"]:
                response += f"""

✅ Command executed successfully! Agent 2 is now working on this phase.
I'll monitor the output and relay any questions or results back to you.

{command_result.get('stdout', '')}
                """
            else:
                response += f"""

❌ Command encountered an issue: {command_result.get('error', 'Unknown error')}
Let me help troubleshoot this before we proceed.
                """
            
            return response
        
        elif "next_phase" in current_step_config:
            next_phase = current_step_config["next_phase"]
            next_phase_desc = self.agile_script[next_phase]["description"]
            
            return f"""
🤖 Agent 1: Excellent! Moving to the next phase: {next_phase_desc}

Let me guide you through this new phase of our Agile process...
            """
        
        return "🤖 Agent 1: Keyword trigger detected! Processing next steps..."
    
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
        print("🤖 Agent 1: I'll now engage our requirements discussion system...")
        print("            Let me run the discuss command and relay any questions from Agent 2...")
        
        # Store that we're starting discuss
        self._add_to_conversation_history("Agent1", 
            "Starting requirements discussion process with Agent 2")
        
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
        add_to_memory(f"Agent 1 facilitated discussion context: {context}", {
            "type": "agent1_facilitated_discussion",
            "phase": self.conversation_state.phase,
            "project_root": str(self.project_root)
        })
        
        return {
            "success": True,
            "agent2_questions": [
                "What is the primary purpose of this application?",
                "Who are the target users?",
                "What are the key features you want to include?",
                "Do you have any specific technology preferences?",
                "What is your timeline for this project?"
            ],
            "next_step": "collect_developer_answers"
        }
    
    def relay_agent2_questions(self, questions: List[str]) -> str:
        """Relay Agent 2's questions to the developer."""
        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
        
        response = f"""
🤖 Agent 1: Agent 2 has analyzed our conversation and generated some important 
clarifying questions. Please answer these so I can feed them back to Agent 2 
and ensure we have complete requirements:

{questions_text}

Please provide your answers, and I'll integrate them into our memory system 
and move us forward to the planning phase.
        """
        
        self._add_to_conversation_history("Agent1", response, {
            "agent2_questions": questions,
            "awaiting_developer_answers": True
        })
        
        return response
    
    def process_developer_answers(self, answers: str) -> str:
        """Process developer's answers and feed them back to Agent 2."""
        self._add_to_conversation_history("Developer", answers, {
            "type": "agent2_question_answers"
        })
        
        # Store answers in memory with rich context
        add_to_memory(f"Developer answers to Agent 2 requirements questions: {answers}", {
            "type": "requirements_answers",
            "phase": "requirements_gathering",
            "source": "agent1_facilitated",
            "project_root": str(self.project_root)
        })
        
        response = f"""
🤖 Agent 1: Excellent! I've stored your answers in our memory system and 
will now feed them back to Agent 2. This ensures both agents have complete 
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
        
        self._add_to_conversation_history("Agent1", response)
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
        You are Agent 1. The developer is asking you to explain: "{topic}"
        
        Based on the NeuroDock documentation and your role as their development partner,
        provide a clear, helpful explanation. Cover:
        1. What this topic means in the context of NeuroDock
        2. How it relates to their current project
        3. What they can expect from this process
        4. Any actions they might need to take
        
        Be conversational and thorough but not overwhelming.
        """
        
        explanation = call_llm(prompt)
        self._add_to_conversation_history("Agent1", explanation, {"type": "explanation", "topic": topic})
        
        return explanation
    
    def guide_next_step(self) -> str:
        """Provide guidance on the next best step."""
        prompt = f"""
        You are Agent 1. The developer is asking for guidance on the next step.
        
        Current state:
        - Phase: {self.conversation_state.phase}
        - Step: {self.conversation_state.current_step}
        - Next actions: {', '.join(self.conversation_state.next_actions)}
        
        Conversation history length: {len(self.conversation_state.conversation_history)}
        
        Provide clear guidance on:
        1. What the next logical step is
        2. Why this step is important
        3. What they need to do
        4. What you (Agent 1) will do to help
        5. How this fits into the overall Agile process
        
        Be specific and actionable.
        """
        
        guidance = call_llm(prompt)
        self._add_to_conversation_history("Agent1", guidance, {"type": "guidance"})
        
        return guidance

# Global conversation agent instance
_conversation_agent = None

def get_conversation_agent(project_root: str = None) -> ConversationalAgent:
    """Get the global conversation agent instance."""
    global _conversation_agent
    
    if not project_root:
        project_root = str(Path.cwd())
    
    if _conversation_agent is None or str(_conversation_agent.project_root) != project_root:
        _conversation_agent = ConversationalAgent(project_root)
    
    return _conversation_agent
