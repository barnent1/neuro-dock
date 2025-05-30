# VS Code MCP Integration for NeuroDock

## Setup

VS Code has native MCP support. To use the NeuroDock MCP server:

1. **Add to `.vscode/settings.json` in your workspace:**

```json
{
    "mcp": {
        "servers": {
            "neurodock": {
                "type": "stdio",
                "command": "python3",
                "args": [
                    "mcp-server/src/server.py"
                ],
                "cwd": "${workspaceFolder}",
                "env": {
                    "PYTHONPATH": "${workspaceFolder}/src"
                }
            }
        }
    }
}
```

## Usage

1. Open VS Code in your NeuroDock workspace
2. Open the chat panel (`Cmd+Shift+I` on macOS, `Ctrl+Shift+I` on Windows/Linux)
3. Use `@neurodock` commands:

```
@neurodock what's my project status?
@neurodock create a task for implementing authentication
@neurodock list all pending tasks
@neurodock add to memory: we decided to use FastAPI
@neurodock search memories about authentication
```

## Available Tools

- `neurodock_get_project_status` - Get project overview
- `neurodock_list_tasks` - List tasks with filtering
- `neurodock_create_task` - Create new tasks
- `neurodock_update_task` - Update task status
- `neurodock_add_memory` - Store project decisions
- `neurodock_search_memory` - Search project memory
- `neurodock_get_project_context` - Get full project context
- `neurodock_start_discussion` - Start interactive discussions
- `neurodock_continue_discussion` - Continue discussions
- `neurodock_get_discussion_status` - Check discussion status

That's it. No extensions needed.
