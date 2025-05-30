# VS Code MCP Configuration for NeuroDock

## Overview

VS Code now has native MCP (Model Context Protocol) support built-in. You can configure the NeuroDock MCP server to work with VS Code's chat interface without needing any extensions.

## Configuration Options

### Option 1: Workspace Settings (Recommended)

Create or edit `.vscode/settings.json` in your NeuroDock project:

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

### Option 2: User Settings (Global)

Edit your user settings (`~/Library/Application Support/Code/User/settings.json` on macOS):

```json
{
    "mcp": {
        "servers": {
            "neurodock": {
                "type": "stdio",
                "command": "python3",
                "args": [
                    "/Users/barnent1/.neuro-dock/mcp-server/src/server.py"
                ],
                "cwd": "/Users/barnent1/.neuro-dock",
                "env": {
                    "PYTHONPATH": "/Users/barnent1/.neuro-dock/src"
                }
            }
        }
    }
}
```

**Note**: Update the paths to match your actual NeuroDock installation directory.

## Usage in VS Code

### 1. Open VS Code Chat
- Press `Ctrl+Shift+I` (Windows/Linux) or `Cmd+Shift+I` (macOS)
- Or use the Command Palette: `View: Toggle Chat`

### 2. Use NeuroDock Tools
Once the MCP server is configured, you can use natural language to interact with your NeuroDock project:

```
@neurodock what's my current project status?
@neurodock create a high priority task for user authentication
@neurodock show me all pending tasks
@neurodock add this to memory: we decided to use TypeScript for better type safety
@neurodock search memories for authentication decisions
@neurodock start a discussion about API design
```

### 3. Available Features

#### **Project Management**
- Get project status and overview
- Create, list, and update tasks
- Track project progress and statistics

#### **Memory & Knowledge**
- Store important decisions and requirements
- Search through project memories with vector search
- Access project context and history

#### **Discussion Workflows**
- Start interactive discussions on topics
- Continue existing conversations
- Track discussion status and participants

#### **Agile Templates**
- Requirements gathering sessions
- Sprint planning workflows
- Retrospective meetings
- Daily standup formats

## Troubleshooting

### MCP Server Not Found
1. Verify Python 3 is installed: `python3 --version`
2. Check that the paths in settings.json are correct
3. Ensure NeuroDock is properly installed in the specified directory

### Server Fails to Start
1. Test the server manually:
   ```bash
   cd /Users/barnent1/.neuro-dock
   python3 mcp-server/src/server.py
   ```
2. Check for missing dependencies:
   ```bash
   pip install -r mcp-server/requirements.txt
   ```

### Tools Not Available
1. Make sure you're in a NeuroDock project directory
2. Run `nd setup` to initialize the project database
3. Check VS Code's Output panel for MCP server logs

### Permission Issues
1. Make sure the server.py file has execute permissions
2. Verify directory permissions for the NeuroDock installation
3. Check that Python can import the NeuroDock modules

## Advanced Configuration

### Custom Environment Variables
```json
{
    "mcp": {
        "servers": {
            "neurodock": {
                "type": "stdio",
                "command": "python3",
                "args": ["mcp-server/src/server.py"],
                "cwd": "${workspaceFolder}",
                "env": {
                    "PYTHONPATH": "${workspaceFolder}/src",
                    "NEURODOCK_DEBUG": "true",
                    "NEURODOCK_LOG_LEVEL": "INFO"
                }
            }
        }
    }
}
```

### Multiple Server Configurations
```json
{
    "mcp": {
        "servers": {
            "neurodock-dev": {
                "type": "stdio",
                "command": "python3",
                "args": ["mcp-server/src/server.py"],
                "cwd": "${workspaceFolder}",
                "env": {
                    "NEURODOCK_ENV": "development"
                }
            },
            "neurodock-prod": {
                "type": "stdio", 
                "command": "python3",
                "args": ["mcp-server/src/server.py"],
                "cwd": "${workspaceFolder}",
                "env": {
                    "NEURODOCK_ENV": "production"
                }
            }
        }
    }
}
```

## Features Available in VS Code

✅ **Native Integration** - No extensions required  
✅ **10 MCP Tools** - Complete project management functionality  
✅ **4 Resources** - Direct access to project data  
✅ **4 Prompts** - Agile workflow templates  
✅ **Chat Interface** - Natural language interaction  
✅ **Context Awareness** - Understands your workspace  
✅ **Real-time Updates** - Live project status  

## Getting Started

1. **Configure MCP Server**: Add the configuration to your VS Code settings
2. **Open NeuroDock Project**: Open your NeuroDock project in VS Code
3. **Start Chatting**: Use `@neurodock` in the VS Code chat to interact with your project
4. **Explore Features**: Try different commands and workflows

The integration provides a seamless way to manage your NeuroDock projects directly from VS Code using natural language through the built-in chat interface.
