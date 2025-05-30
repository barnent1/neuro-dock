# VS Code MCP Integration - Complete Setup Guide

## Overview

This guide documents the complete VS Code integration setup for the NeuroDock MCP server using VS Code's native MCP support through GitHub Copilot's agent mode.

## Configuration Files

### 1. VS Code Settings (`.vscode/settings.json`)

```json
{
    "chat.mcp.enabled": true,
    "chat.mcp.discovery.enabled": true,
    "chat.agent.enabled": true,
    "python.defaultInterpreterPath": "python3",
    "python.terminal.activateEnvironment": true,
    "files.associations": {
        "*.nd": "yaml",
        "neurodock.config": "json"
    },
    "editor.codeActionsOnSave": {
        "source.organizeImports": "explicit"
    },
    "chat.editor.fontSize": 14,
    "chat.editor.wordWrap": "on"
}
```

**Key Settings Explained:**
- `chat.mcp.enabled: true` - Enables MCP support in VS Code
- `chat.mcp.discovery.enabled: true` - Enables autodiscovery of MCP servers from other tools
- `chat.agent.enabled: true` - Enables agent mode (required for MCP functionality)

### 2. MCP Server Configuration (`.vscode/mcp.json`)

```json
{
  "servers": {
    "neurodock": {
      "type": "stdio",
      "command": "python3",
      "args": [
        "/Users/barnent1/.neuro-dock/mcp-server/src/server.py"
      ],
      "env": {
        "PYTHONPATH": "/Users/barnent1/.neuro-dock"
      }
    }
  }
}
```

**Configuration Details:**
- **Server Name**: `neurodock` - Descriptive name for the MCP server
- **Type**: `stdio` - Standard input/output communication protocol
- **Command**: `python3` - Python interpreter to run the server
- **Args**: Full path to the NeuroDock MCP server script
- **Environment**: Sets PYTHONPATH to include NeuroDock core modules

## How to Use

### 1. Enable Agent Mode

1. Open the Chat view in VS Code (`Ctrl+Alt+I` on Windows/Linux, `⌃⌘I` on Mac)
2. Select **Agent** from the chat mode dropdown
3. Or use the direct link: `vscode://GitHub.Copilot-Chat/chat?mode=agent`

### 2. Access NeuroDock Tools

Once in agent mode, you can:

- **View Available Tools**: Click the Tools button to see all 10 NeuroDock tools
- **Use Tools in Prompts**: Reference tools directly with `#toolname`
- **Natural Language**: Ask questions that will automatically invoke NeuroDock tools

### 3. Available NeuroDock Tools

The MCP server provides 10 tools for interacting with NeuroDock:

1. **neurodock_create_project** - Create new NeuroDock projects
2. **neurodock_list_projects** - List all available projects
3. **neurodock_get_project_info** - Get detailed project information
4. **neurodock_add_memory** - Add memories to the vector store
5. **neurodock_search_memories** - Search through stored memories
6. **neurodock_get_memory** - Retrieve specific memories by ID
7. **neurodock_start_discussion** - Start new interactive discussions
8. **neurodock_continue_discussion** - Continue existing discussions
9. **neurodock_get_discussion_status** - Check discussion status
10. **neurodock_agent_query** - Query the NeuroDock agent system

### 4. Example Usage

```
# Start a new project
Create a new NeuroDock project for machine learning research

# Search memories
Find all memories related to neural networks

# Start a discussion
Begin a discussion about implementing a transformer model
```

## Verification

### Test MCP Server
```bash
cd /Users/barnent1/.neuro-dock
python3 mcp-server/test_server.py
```

Expected output: All 5 tests should pass.

### Check VS Code Integration
1. Open VS Code in the NeuroDock workspace
2. Open Chat view and select Agent mode
3. Click Tools button - you should see "neurodock" server with 10 tools
4. Try a simple prompt: "List my NeuroDock projects"

## Troubleshooting

### MCP Server Not Loading
- Check VS Code Output panel for MCP server logs
- Verify Python path and NeuroDock installation
- Ensure all dependencies are installed: `pip install -r requirements.txt`

### Agent Mode Not Available
- Verify VS Code version 1.99+ is installed
- Check that GitHub Copilot extension is active
- Confirm `chat.agent.enabled: true` in settings

### Tools Not Appearing
- Restart the MCP server: Command Palette → "MCP: List Servers" → Select neurodock → Restart
- Check MCP server logs for errors
- Verify `.vscode/mcp.json` configuration

## Architecture

```
VS Code GitHub Copilot Agent Mode
           ↓
    MCP Client (VS Code)
           ↓
   MCP Server (NeuroDock)
           ↓
    NeuroDock Core Systems
    (store, agent, memory)
```

## Security

- MCP servers run with user permissions
- VS Code prompts for confirmation before tool execution
- Use "Continue" dropdown to auto-approve trusted tools
- Set `chat.tools.autoApprove: true` for automatic approval (use with caution)

## Next Steps

1. **Explore Tools**: Try different NeuroDock tools in agent mode
2. **Create Workflows**: Combine multiple tools for complex tasks
3. **Custom Instructions**: Add `.github/copilot-instructions.md` for tool usage guidelines
4. **Share Configuration**: Team members can use the same `.vscode/mcp.json` file

## References

- [VS Code MCP Documentation](https://code.visualstudio.com/docs/copilot/chat/mcp-servers)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [GitHub Copilot Agent Mode](https://code.visualstudio.com/docs/copilot/chat/chat-agent-mode)
