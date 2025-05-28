#!/usr/bin/env python3

import requests
import json
import yaml
from typing import Optional
from ..config import get_config
from .animation import thinking_context

# Get centralized configuration
config = get_config()

# Import memory functions with error handling
try:
    from ..memory.qdrant_store import search_memory, add_to_memory
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

def call_ollama(prompt: str, model: str = "openchat") -> str:
    """
    Send a prompt to a local Ollama model via API.
    
    Args:
        prompt: The prompt to send to the model
        model: The Ollama model to use (default: openchat)
        
    Returns:
        The model's response as a string
        
    Raises:
        requests.RequestException: If the API call fails
        KeyError: If the response format is unexpected
    """
    url = "http://localhost:11434/api/generate"
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        response_data = response.json()
        return response_data["response"]
        
    except requests.exceptions.ConnectionError:
        raise requests.RequestException(
            "Could not connect to Ollama at localhost:11434. "
            "Make sure Ollama is running and accessible."
        )
    except requests.exceptions.Timeout:
        raise requests.RequestException(
            f"Request to Ollama timed out after 60 seconds. "
            f"The model '{model}' might be taking too long to respond."
        )
    except KeyError as e:
        raise KeyError(f"Unexpected response format from Ollama: missing key {e}")

def call_llm(prompt: str, use: Optional[str] = None) -> str:
    """
    Call the appropriate LLM backend based on configuration.
    Automatically injects relevant memory context if available.
    
    Args:
        prompt: The prompt to send to the model
        use: Override the LLM backend ("ollama" or "claude"). 
             If None, uses NEURO_LLM environment variable.
             
    Returns:
        The model's response as a string
        
    Raises:
        ValueError: If an unknown LLM backend is specified
        ImportError: If Claude backend is requested but not available
        requests.RequestException: If Ollama API call fails
    """
    # Enhance prompt with memory context if available
    enhanced_prompt = prompt
    if MEMORY_AVAILABLE:
        try:
            # Search for relevant memories
            relevant_memories = search_memory(prompt, limit=5)
            if relevant_memories:
                memory_context = "\n".join([f"- {memory}" for memory in relevant_memories])
                enhanced_prompt = f"""Relevant prior discussion:
{memory_context}

Current request:
{prompt}"""
        except Exception as e:
            # Silent fallback - don't break the user experience
            pass
    
    # Determine which LLM to use
    llm_backend = use or config.llm_backend
    
    # Get the response with animated thinking indicator
    with thinking_context("( ● ) Thinking"):
        if llm_backend == "ollama":
            # Get the specific Ollama model from environment or use default
            ollama_model = config.ollama_model
            response = call_ollama(enhanced_prompt, model=ollama_model)
            
        elif llm_backend == "claude":
            try:
                from .claude import call_claude
                response = call_claude(enhanced_prompt)
            except ImportError:
                raise ImportError(
                    "Claude backend is not available. "
                    "Make sure utils/claude.py exists and call_claude() is implemented."
                )
                
        else:
            raise ValueError(
                f"Unknown LLM backend: '{llm_backend}'. "
                f"Supported backends are: 'ollama', 'claude'"
            )
    
    # Store the interaction in memory if available
    if MEMORY_AVAILABLE:
        try:
            # Store both the original prompt and the response
            add_to_memory(
                prompt, 
                {"type": "user_prompt", "llm_backend": llm_backend}
            )
            add_to_memory(
                response, 
                {"type": "llm_response", "llm_backend": llm_backend}
            )
        except Exception as e:
            # Silent fallback - don't break the user experience
            pass
    
    return response

def call_llm_plan(prompt: str, use: Optional[str] = None) -> str:
    """
    Call the appropriate LLM backend for planning tasks.
    
    This function enhances the user's prompt with specific instructions for
    generating structured YAML output suitable for the neuro-dock project plan.
    
    Args:
        prompt: The prompt to send to the model for planning
        use: Override the LLM backend ("ollama" or "claude")
        
    Returns:
        The model's planning response as a YAML-formatted string
    """
    # Enhance the prompt with YAML formatting instructions
    enhanced_prompt = f"""Based on the following project description, create a structured YAML plan for implementation:

{prompt}

Please respond with ONLY a valid YAML structure in the following format (no additional text or explanations):

project:
  name: "Your Project Name"
  description: "Brief description of the project"

tasks:
  - name: "Task 1 Name"
    description: "Detailed description of what this task accomplishes"
    type: "file_creation"
  - name: "Task 2 Name" 
    description: "Detailed description of what this task accomplishes"
    type: "documentation"

Make sure to:
1. Include 2-5 specific, actionable tasks
2. Use clear, descriptive task names
3. Provide detailed descriptions for each task
4. Use appropriate task types like "file_creation", "documentation", "configuration", etc.
5. Return ONLY the YAML content, no markdown code blocks or extra text"""

    response = call_llm(enhanced_prompt, use)
    
    # Clean up the response - remove markdown code blocks if present
    cleaned_response = response.strip()
    if cleaned_response.startswith('```yaml'):
        cleaned_response = cleaned_response[7:]  # Remove ```yaml
    elif cleaned_response.startswith('```'):
        cleaned_response = cleaned_response[3:]   # Remove ```
    if cleaned_response.endswith('```'):
        cleaned_response = cleaned_response[:-3]  # Remove ending ```
    
    cleaned_response = cleaned_response.strip()
    
    # Validate that the response is valid YAML
    try:
        yaml.safe_load(cleaned_response)
        return cleaned_response
    except yaml.YAMLError as e:
        # If YAML is invalid, return a fallback structure
        return f"""project:
  name: "Generated Project"
  description: "Project based on user requirements"

tasks:
  - name: "Implement Core Functionality"
    description: "Create the main functionality as described in the prompt"
    type: "file_creation"
  - name: "Create Documentation"
    description: "Add README and documentation files"
    type: "documentation"

# Note: Original LLM response was not valid YAML. Error: {str(e)}
# Original response: {response[:200]}..."""

def call_llm_code(prompt: str, use: Optional[str] = None) -> dict:
    """
    Call the appropriate LLM backend for code generation tasks.
    
    Args:
        prompt: The prompt to send to the model for code generation
        use: Override the LLM backend ("ollama" or "claude")
        
    Returns:
        A dictionary with the expected format:
        {
            "files": [
                {
                    "path": "relative/path/to/file.py",
                    "content": "# actual code content"
                }
            ],
            "explanation": "Description of what was generated"
        }
    """
    # Add context to the prompt to encourage structured output and real-world project layouts
    structured_prompt = f"""
{prompt}

CRITICAL: You MUST respond with ONLY valid JSON in the exact format shown below. No other text before or after the JSON.

For real-world project structures:
- Python: Use src/package_name/, tests/, requirements.txt, README.md, setup.py
- Web: Use index.html, css/, js/, components/ folders
- Node.js: Use package.json, src/, public/, etc.

JSON FORMAT (respond with ONLY this structure):
{{
    "files": [
        {{
            "path": "calculator.py",
            "content": "def add(x, y):\\n    return x + y\\n\\ndef subtract(x, y):\\n    return x - y"
        }},
        {{
            "path": "README.md", 
            "content": "# Calculator\\n\\nA simple Python calculator."
        }}
    ],
    "explanation": "Created a basic Python calculator with add/subtract functions and documentation."
}}

Respond with ONLY the JSON above. No additional text or explanations outside the JSON.
"""
    
    # Get the raw response from the LLM
    raw_response = call_llm(structured_prompt, use)
    
    # Try to parse the response as JSON with multiple strategies
    try:
        # Strategy 1: Try parsing the entire response as JSON
        try:
            response_data = json.loads(raw_response.strip())
            if "files" in response_data and "explanation" in response_data:
                return response_data
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Find JSON block between curly braces
        start_idx = raw_response.find('{')
        end_idx = raw_response.rfind('}') + 1
        
        if start_idx != -1 and end_idx != 0:
            json_part = raw_response[start_idx:end_idx]
            response_data = json.loads(json_part)
            
            # Validate the expected structure
            if "files" in response_data and "explanation" in response_data:
                return response_data
        
        # Strategy 3: Look for code blocks in the response and create a simple structure
        lines = raw_response.split('\n')
        potential_files = []
        current_file = None
        current_content = []
        
        for line in lines:
            if line.strip().startswith('```') and current_file is None:
                # Look for filename in the code block start
                if '```python' in line.lower():
                    current_file = {"path": "main.py", "content": ""}
                elif '```' in line and len(line.strip()) > 3:
                    filename = line.strip()[3:].strip()
                    current_file = {"path": filename or "code.txt", "content": ""}
                else:
                    current_file = {"path": "code.txt", "content": ""}
            elif line.strip() == '```' and current_file is not None:
                # End of code block
                current_file["content"] = '\n'.join(current_content)
                potential_files.append(current_file)
                current_file = None
                current_content = []
            elif current_file is not None:
                current_content.append(line)
        
        if potential_files:
            return {
                "files": potential_files,
                "explanation": "Extracted code blocks from the LLM response and created files."
            }
        
        # Fallback: Create a single file with the entire response
        return {
            "files": [
                {
                    "path": "generated_code.py",
                    "content": f"# Generated code\n# Original response:\n'''\n{raw_response}\n'''"
                }
            ],
            "explanation": "The LLM response could not be parsed as structured JSON. Check the generated file for the raw response."
        }
        
    except Exception as e:
        # Ultimate fallback if everything fails
        return {
            "files": [
                {
                    "path": "llm_response.txt",
                    "content": raw_response
                }
            ],
            "explanation": f"The LLM response could not be processed (error: {str(e)}). The raw response has been saved as a text file."
        }

def get_current_llm_backend() -> str:
    """
    Get the name of the currently configured LLM backend.
    
    Returns:
        The display name of the current LLM backend (e.g., "Ollama", "Claude")
    """
    llm_backend = config.llm_backend
    
    if llm_backend == "ollama":
        ollama_model = config.ollama_model
        return f"Ollama ({ollama_model})"
    elif llm_backend == "claude":
        return "Claude"
    else:
        return f"Unknown ({llm_backend})"
