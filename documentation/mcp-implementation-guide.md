# NeuroDock MCP Server Implementation Guide

## Overview

This document contains all the essential information from the official Model Context Protocol (MCP) documentation that pertains to our NeuroDock implementation. **This is our single source of truth for MCP implementation - refer to this document to stay on track.**

## What We're Building

NeuroDock will communicate with AI agents (like Claude/GitHub Copilot) through an MCP server that provides:

1. **Tools** for agile workflow management (NOT code generation)
2. **Resources** for project context and memory access  
3. **Prompts** for structured agile conversations

**Key Principle**: NeuroDock handles planning, memory, and task management. The AI agent handles all code implementation.

## MCP Core Architecture

### Client-Server Communication
- **Host**: AI applications (Claude Desktop, VS Code with extensions)
- **Client**: Protocol clients that maintain 1:1 connections with servers  
- **Server**: NeuroDock MCP server providing agile workflow capabilities
- **Transport**: JSON-RPC 2.0 over stdio or HTTP with SSE

### Message Types
```typescript
// Requests expect responses
interface Request {
  method: string;
  params?: { ... };
}

// Results are successful responses  
interface Result {
  [key: string]: unknown;
}

// Errors indicate request failures
interface Error {
  code: number;
  message: string;
  data?: unknown;
}

// Notifications are one-way messages
interface Notification {
  method: string;
  params?: { ... };
}
```

### Connection Lifecycle
1. **Initialize**: Client sends `initialize` request with capabilities
2. **Handshake**: Server responds with its capabilities  
3. **Ready**: Client sends `initialized` notification
4. **Operation**: Normal request-response and notifications
5. **Shutdown**: Either party can terminate cleanly

## MCP Server Capabilities for NeuroDock

### 1. Tools - Agile Workflow Actions

Tools allow AI agents to execute NeuroDock functions. **These are model-controlled** - the AI decides when to use them.

#### Tool Structure
```typescript
{
  name: string;              // Unique identifier
  description?: string;      // Human-readable description  
  inputSchema: {             // JSON Schema for parameters
    type: "object",
    properties: { ... }      
  },
  annotations?: {            // Behavioral hints
    title?: string;          
    readOnlyHint?: boolean;    // true = no environment changes
    destructiveHint?: boolean; // true = may perform destructive updates
    idempotentHint?: boolean;  // true = repeatable with same result
    openWorldHint?: boolean;   // true = interacts with external entities
  }
}
```

#### NeuroDock Tools to Implement

**Project Management Tools:**
```typescript
// Get current project status and context
{
  name: "neurodock_get_project_status",
  description: "Get current project state, progress, and active tasks",
  inputSchema: { type: "object", properties: {} },
  annotations: { readOnlyHint: true, openWorldHint: false }
}

// List all project tasks with status
{
  name: "neurodock_list_tasks", 
  description: "View all project tasks and their current status",
  inputSchema: {
    type: "object",
    properties: {
      status_filter: { type: "string", enum: ["all", "pending", "in_progress", "completed"] }
    }
  },
  annotations: { readOnlyHint: true, openWorldHint: false }
}

// Update task status/progress
{
  name: "neurodock_update_task",
  description: "Mark tasks as complete or update progress", 
  inputSchema: {
    type: "object",
    properties: {
      task_id: { type: "string" },
      status: { type: "string", enum: ["pending", "in_progress", "completed"] },
      notes: { type: "string" }
    },
    required: ["task_id", "status"]
  },
  annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: true }
}
```

**Memory and Context Tools:**
```typescript
// Store important decisions/context
{
  name: "neurodock_add_memory",
  description: "Store important project decisions and context for future reference",
  inputSchema: {
    type: "object", 
    properties: {
      type: { type: "string", enum: ["decision", "requirement", "constraint", "note"] },
      content: { type: "string" },
      tags: { type: "array", items: { type: "string" } }
    },
    required: ["type", "content"]
  },
  annotations: { readOnlyHint: false, destructiveHint: false }
}

// Search project history/memory
{
  name: "neurodock_search_memory",
  description: "Search project history and past decisions",
  inputSchema: {
    type: "object",
    properties: {
      query: { type: "string" },
      limit: { type: "number", default: 10 }
    },
    required: ["query"]
  },
  annotations: { readOnlyHint: true, openWorldHint: false }
}
```

**Planning and Discussion Tools:**
```typescript
// Create new development tasks
{
  name: "neurodock_create_task", 
  description: "Add new development tasks to the project plan",
  inputSchema: {
    type: "object",
    properties: {
      title: { type: "string" },
      description: { type: "string" },
      type: { type: "string", enum: ["feature", "bug", "refactor", "test", "doc"] },
      priority: { type: "string", enum: ["low", "medium", "high", "critical"] },
      estimated_hours: { type: "number" }
    },
    required: ["title", "description", "type"]
  },
  annotations: { readOnlyHint: false, destructiveHint: false }
}

// Get full project context for AI decision-making
{
  name: "neurodock_get_project_context",
  description: "Get comprehensive project context including requirements, decisions, and current state",
  inputSchema: { type: "object", properties: {} },
  annotations: { readOnlyHint: true, openWorldHint: false }
}
```

**Discussion Flow Tools:**
```typescript
// Start iterative discussion process
{
  name: "neurodock_start_discussion",
  description: "Begin iterative requirements gathering discussion",
  inputSchema: {
    type: "object",
    properties: {
      initial_prompt: { type: "string" }
    },
    required: ["initial_prompt"]
  },
  annotations: { readOnlyHint: false, destructiveHint: false }
}

// Continue discussion iteration
{
  name: "neurodock_continue_discussion", 
  description: "Provide answers to discussion questions and continue iteration",
  inputSchema: {
    type: "object",
    properties: {
      answers: { type: "string" },
      discussion_id: { type: "string" }
    },
    required: ["answers"]
  },
  annotations: { readOnlyHint: false, destructiveHint: false }
}

// Check discussion status
{
  name: "neurodock_get_discussion_status",
  description: "Get current discussion state and next actions needed",
  inputSchema: {
    type: "object",
    properties: {
      discussion_id: { type: "string" }
    }
  },
  annotations: { readOnlyHint: true, openWorldHint: false }
}
```

#### Tool Implementation Pattern
```python
# In Python MCP server
@mcp.tool()
async def neurodock_get_project_status() -> str:
    """Get current project state, progress, and active tasks."""
    try:
        # Load project context from NeuroDock
        status = await get_project_status_from_neurodock()
        return json.dumps(status, indent=2)
    except Exception as e:
        return f"Error getting project status: {str(e)}"
```

### 2. Resources - Project Context Access

Resources provide read-only access to project data. **These are application-controlled** - the user/client decides when to use them.

#### Resource Structure
```typescript
{
  uri: string;           // Unique identifier (custom URI scheme)
  name: string;          // Human-readable name
  description?: string;  // Optional description
  mimeType?: string;     // Optional MIME type
}
```

#### NeuroDock Resources to Implement

**Project Resources:**
```typescript
// Current project configuration
{
  uri: "neurodock://project/config",
  name: "Project Configuration", 
  description: "Current project settings and metadata",
  mimeType: "application/json"
}

// Task plan and breakdown
{
  uri: "neurodock://project/plan", 
  name: "Project Plan",
  description: "Current task breakdown and project roadmap",
  mimeType: "application/json"
}

// Conversation history
{
  uri: "neurodock://project/discussions",
  name: "Discussion History",
  description: "Complete conversation and requirements gathering history", 
  mimeType: "application/json"
}

// Project memory/decisions
{
  uri: "neurodock://project/memory",
  name: "Project Memory",
  description: "Important decisions, constraints, and context",
  mimeType: "application/json"
}
```

**Dynamic Resources (using URI templates):**
```typescript
// Specific task details
{
  uriTemplate: "neurodock://tasks/{task_id}",
  name: "Task Details",
  description: "Detailed information about a specific task",
  mimeType: "application/json"
}

// Memory by type/tag
{
  uriTemplate: "neurodock://memory/{type}",
  name: "Memory by Type", 
  description: "Memory items filtered by type (decisions, requirements, etc)",
  mimeType: "application/json"
}
```

#### Resource Implementation Pattern  
```python
# List available resources
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  return {
    resources: [
      {
        uri: "neurodock://project/config",
        name: "Project Configuration",
        mimeType: "application/json"
      },
      # ... other resources
    ]
  }
})

# Read resource content
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  uri = request.params.uri
  if uri == "neurodock://project/config":
    config = await load_project_config()
    return {
      contents: [{
        uri: uri,
        mimeType: "application/json", 
        text: json.dumps(config, indent=2)
      }]
    }
})
```

### 3. Prompts - Structured Agile Workflows

Prompts provide templated workflows for specific agile activities. **These are user-controlled** - explicitly selected by user.

#### Prompt Structure
```typescript
{
  name: string;              // Unique identifier
  description?: string;      // Human-readable description
  arguments?: [              // Optional arguments
    {
      name: string;          // Argument identifier  
      description?: string;  // Argument description
      required?: boolean;    // Whether required
    }
  ]
}
```

#### NeuroDock Prompts to Implement

**Agile Workflow Prompts:**
```typescript
// Start new project discussion
{
  name: "neurodock-start-project",
  description: "Begin structured project planning conversation",
  arguments: [
    {
      name: "project_idea", 
      description: "Initial project concept or goals",
      required: true
    }
  ]
}

// Sprint planning session
{
  name: "neurodock-sprint-planning",
  description: "Plan next development sprint with task breakdown",
  arguments: [
    {
      name: "sprint_goal",
      description: "Main objective for this sprint", 
      required: false
    }
  ]
}

// Retrospective analysis
{
  name: "neurodock-retrospective",
  description: "Analyze completed work and identify improvements",
  arguments: [
    {
      name: "completed_tasks",
      description: "List of recently completed tasks",
      required: false
    }
  ]
}

// Requirements clarification
{
  name: "neurodock-clarify-requirements", 
  description: "Deep dive into specific feature requirements",
  arguments: [
    {
      name: "feature_description",
      description: "Feature that needs clarification",
      required: true
    }
  ]
}
```

#### Prompt Implementation Pattern
```python
# List available prompts
server.setRequestHandler(ListPromptsRequestSchema, async () => {
  return {
    prompts: [
      {
        name: "neurodock-start-project",
        description: "Begin structured project planning conversation",
        arguments: [
          {
            name: "project_idea",
            description: "Initial project concept or goals", 
            required: True
          }
        ]
      }
    ]
  }
})

# Get specific prompt
server.setRequestHandler(GetPromptRequestSchema, async (request) => {
  if request.params.name == "neurodock-start-project":
    project_idea = request.params.arguments.get("project_idea", "")
    return {
      messages: [
        {
          role: "user",
          content: {
            type: "text",
            text: f"Let's start planning a new project: {project_idea}\n\nI'd like to use the NeuroDock agile methodology to break this down systematically. Can you help me start with requirements gathering?"
          }
        }
      ]
    }
})
```

## Integration with NeuroDock System

### Data Flow Architecture
```
AI Agent (Claude/Copilot) 
    ↕ [MCP Protocol]
NeuroDock MCP Server
    ↕ [Direct calls]
NeuroDock Core System
    ↕ [Database/Memory]
PostgreSQL + Qdrant + Neo4j
```

### MCP Server Implementation Structure
```python
# neurodock-mcp-server/src/server.py
from mcp.server.fastmcp import FastMCP
import sys
import os

# Add NeuroDock core to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../src'))

from neurodock.db import get_store
from neurodock.discussion import run_interactive_discussion  
from neurodock.memory.qdrant_store import search_memory, add_to_memory
from neurodock.agent import ProjectAgent

# Initialize MCP server
mcp = FastMCP("neurodock")

# Tool implementations call into NeuroDock core
@mcp.tool()
async def neurodock_get_project_status() -> str:
    """Get current project state and progress."""
    # Call NeuroDock core functions
    agent = ProjectAgent(os.getcwd())
    context = agent.load_project_context()
    return json.dumps(context, indent=2)

# Resource implementations read from NeuroDock data
@mcp.resource("neurodock://project/config")
async def get_project_config() -> str:
    """Get project configuration."""
    # Load from NeuroDock config
    config_path = Path.cwd() / ".neuro-dock" / "config.yaml"
    if config_path.exists():
        return config_path.read_text()
    return "{}"

if __name__ == "__main__":
    mcp.run(transport='stdio')
```

## Error Handling Patterns

### Tool Error Handling
```python
try:
    result = perform_neurodock_operation()
    return {
        "content": [{"type": "text", "text": f"Success: {result}"}]
    }
except Exception as error:
    return {
        "isError": True,
        "content": [{"type": "text", "text": f"Error: {error.message}"}]
    }
```

### Standard MCP Error Codes
```python
enum ErrorCode {
    ParseError = -32700,
    InvalidRequest = -32600, 
    MethodNotFound = -32601,
    InvalidParams = -32602,
    InternalError = -32603
}
```

## Security Considerations

### Input Validation
- Validate all tool parameters against JSON Schema
- Sanitize file paths and system references
- Check parameter sizes and ranges
- Prevent injection attacks

### Access Control  
- Implement project-based authorization
- Validate user permissions for operations
- Rate limit requests appropriately
- Audit all tool usage

### Data Protection
- Don't expose sensitive internal data
- Log security-relevant errors
- Handle timeouts gracefully  
- Clean up resources after errors

## Testing and Debugging

### MCP Inspector Testing
```bash
# Test server with MCP Inspector
npx @modelcontextprotocol/inspector neurodock-mcp-server
```

### Claude Desktop Integration
```json
// ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "neurodock": {
      "command": "python",
      "args": ["/absolute/path/to/neurodock-mcp-server/src/server.py"],
      "env": {
        "NEURODOCK_DB_URL": "postgresql://localhost/neurodock"
      }
    }
  }
}
```

### Debugging Tools
```bash
# Follow Claude Desktop logs
tail -n 20 -F ~/Library/Logs/Claude/mcp*.log

# Enable Chrome DevTools in Claude Desktop
echo '{"allowDevTools": true}' > ~/Library/Application\ Support/Claude/developer_settings.json
```

## Implementation Checklist

### Phase 1: Basic MCP Server
- [ ] Set up FastMCP server with stdio transport
- [ ] Implement core project status tools
- [ ] Test with MCP Inspector
- [ ] Basic error handling

### Phase 2: NeuroDock Integration  
- [ ] Connect to NeuroDock core database/memory systems
- [ ] Implement all planned tools
- [ ] Add resource endpoints
- [ ] Test with Claude Desktop

### Phase 3: Advanced Features
- [ ] Implement prompts for agile workflows
- [ ] Add real-time updates/notifications
- [ ] Performance optimization
- [ ] Comprehensive error handling

### Phase 4: Production Ready
- [ ] Security hardening
- [ ] Monitoring and logging
- [ ] Documentation and examples
- [ ] Package for distribution

## Key Success Metrics

1. **Agent Productivity**: AI agents can efficiently plan projects using NeuroDock tools
2. **Memory Continuity**: Project context and decisions persist across sessions  
3. **Agile Workflow**: Complete agile process supported through MCP interface
4. **User Experience**: Seamless integration with AI assistant workflow
5. **Reliability**: Robust error handling and consistent performance

## Remember: What NeuroDock Does vs. What AI Agent Does

### NeuroDock Responsibilities (via MCP):
- Project planning and task breakdown
- Memory storage and retrieval
- Discussion facilitation and requirements gathering  
- Progress tracking and status reporting
- Agile workflow orchestration

### AI Agent Responsibilities:
- All code generation and implementation
- File system operations
- Running tests and builds
- Git operations and version control
- Technical decision-making during implementation

**The MCP server is the bridge that lets them work together effectively.**
