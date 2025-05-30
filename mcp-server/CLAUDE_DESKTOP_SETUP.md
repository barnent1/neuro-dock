# Claude Desktop Configuration for NeuroDock MCP Server

## Setup Instructions

1. **Locate Claude Desktop Config File**
   ```bash
   # macOS
   ~/Library/Application Support/Claude/claude_desktop_config.json
   
   # Windows  
   %APPDATA%\Claude\claude_desktop_config.json
   
   # Linux
   ~/.config/Claude/claude_desktop_config.json
   ```

2. **Add NeuroDock MCP Server Configuration**

   Add this to your `claude_desktop_config.json`:

   ```json
   {
     "mcpServers": {
       "neurodock": {
         "command": "python3",
         "args": ["/Users/barnent1/.neuro-dock/mcp-server/src/server.py"],
         "cwd": "/Users/barnent1/.neuro-dock",
         "env": {
           "PYTHONPATH": "/Users/barnent1/.neuro-dock/src"
         }
       }
     }
   }
   ```

   **Important**: Update the paths to match your actual NeuroDock installation directory.

3. **Restart Claude Desktop**

   After saving the configuration file, restart Claude Desktop for the changes to take effect.

## Usage Examples

### Basic Project Status
```
Check my project status using the neurodock tools
```

### Create and Manage Tasks
```
Create a new high-priority task: "Implement user authentication"
List all pending tasks
Update task status to in-progress for task ID 5
```

### Memory and Knowledge Management
```
Add this decision to memory: "We chose React over Vue for better TypeScript support"
Search memories for "authentication" decisions
```

### Discussion Workflows
```
Start a discussion about "API design for user management module"
Continue the discussion with: "We should consider rate limiting"
Get the status of all current discussions
```

### Agile Workflows
```
Use the sprint planning prompt for Sprint 3
Generate a retrospective template for the last sprint
Create a daily standup format for today
```

### Project Context
```
Get comprehensive project context including files and recent activity
Show me the project file structure
Get all current tasks and recent memories
```

## Available Resources

You can access these resources directly in Claude:

- **Project Files**: `neurodock://project/files`
- **Tasks**: `neurodock://project/tasks`  
- **Memories**: `neurodock://project/memory`
- **Full Context**: `neurodock://project/context`

## Available Prompts

Use these prompts for structured workflows:

- **Requirements Gathering**: `neurodock-requirements-gathering`
- **Sprint Planning**: `neurodock-sprint-planning`
- **Retrospectives**: `neurodock-retrospective`
- **Daily Standups**: `neurodock-daily-standup`

## Troubleshooting

### Server Not Starting
1. Check Python 3 is installed: `python3 --version`
2. Verify NeuroDock is properly installed
3. Check file paths in the configuration
4. Look at Claude Desktop logs for error messages

### Tools Not Available
1. Ensure you're in a NeuroDock project directory
2. Run `nd setup` to initialize the project database
3. Check that all NeuroDock dependencies are installed

### Permission Issues
1. Make sure the server.py file is executable
2. Check directory permissions for the NeuroDock installation
3. Verify Python can import the NeuroDock modules

## Features

✅ **10 Tools** - Complete project management functionality  
✅ **4 Resources** - Direct access to project data  
✅ **4 Prompts** - Agile workflow templates  
✅ **Discussion System** - Interactive conversation workflows  
✅ **Vector Search** - Intelligent memory search  
✅ **Full Integration** - Native NeuroDock core systems  

The MCP server provides seamless integration between Claude Desktop and your NeuroDock projects, enabling natural language interaction with your project management workflows.
