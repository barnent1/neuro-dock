# Using NeuroDock MCP Server on New Projects

This guide shows you how to set up and use the NeuroDock MCP server on any new project for AI-powered project management.

## Prerequisites

- **Node.js** 18+ (for MCP server)
- **Python** 3.10+ (for NeuroDock core functionality)
- **Claude Desktop** or other MCP-compatible AI client

## Setup Options

### Option 1: NPX (Easiest - No Installation)

Use the server directly without installation:

```bash
# In your project directory
npx @neurodock/mcp-server
```

### Option 2: Global Installation

Install globally for reuse across projects:

```bash
npm install -g @neurodock/mcp-server
neurodock-mcp
```

### Option 3: Local Project Installation

Install as a development dependency:

```bash
cd your-new-project
npm install --save-dev @neurodock/mcp-server
npx neurodock-mcp
```

## Quick Start for New Projects

### 1. Initialize NeuroDock in Your Project

```bash
cd your-new-project

# Initialize NeuroDock (creates .neuro-dock directory and config)
python3 -m pip install neurodock
neurodock init

# Or if you have NeuroDock already installed
python3 -c "
import os
from pathlib import Path

# Create basic NeuroDock structure
neuro_dir = Path('.neuro-dock')
neuro_dir.mkdir(exist_ok=True)

# Create basic config
config = {
    'project_name': os.path.basename(os.getcwd()),
    'initialized': True,
    'mcp_enabled': True
}

import json
with open(neuro_dir / 'config.json', 'w') as f:
    json.dump(config, f, indent=2)

print('✅ NeuroDock initialized for new project')
"
```

### 2. Configure Claude Desktop (Clean Approach)

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "neurodock": {
      "command": "npx",
      "args": ["@neurodock/mcp-server"]
    }
  }
}
```

The server automatically detects your project path by looking for:
1. `NEURODOCK_PROJECT_PATH` environment variable (if set)
2. `.neuro-dock` directory in current working directory 
3. NeuroDock source structure (`src/neurodock`)
4. Falls back to current directory

### 2a. Optional: Custom Project Path (.env approach)

If you need to override the project path, create a `.env` file in your project root:

```bash
# .env file in your project root
NEURODOCK_PROJECT_PATH=/path/to/your/project
```

Or set it globally in your shell:

```bash
# In your ~/.zshrc or ~/.bashrc
export NEURODOCK_PROJECT_PATH=/path/to/your/default/project
```

### 3. Start Using NeuroDock Tools

Once configured, you'll have access to these tools in Claude:

#### Project Management Tools:
- `neurodock_get_project_status` - Get project overview
- `neurodock_create_task` - Create new tasks
- `neurodock_list_tasks` - View all tasks
- `neurodock_update_task` - Update task status

#### Knowledge Management:
- `neurodock_add_memory` - Store important decisions
- `neurodock_search_memory` - Find past decisions/notes

#### Agile Workflow:
- `neurodock_start_discussion` - Begin requirements gathering
- `neurodock_continue_discussion` - Multi-round conversations

## Example Usage in Claude

### Starting a New Project Discussion

**You:** Use the `neurodock-requirements-gathering` prompt to help me plan a new web application.

**Claude:** I'll help you gather requirements systematically. Let me start a structured discussion...

*[Claude uses the MCP prompt template and starts gathering requirements]*

### Creating Tasks

**You:** Create a task for "Set up React project structure" with high priority.

**Claude:** I'll create that task for you using `neurodock_create_task`...

*[Task created and stored in your project's database]*

### Storing Decisions

**You:** Remember that we decided to use TypeScript and Tailwind CSS for this project.

**Claude:** I'll store that decision using `neurodock_add_memory`...

*[Decision stored with tags and searchable in the future]*

## Project Structure

After initialization, your project will have:

```
your-new-project/
├── .neuro-dock/
│   ├── config.json          # Project configuration
│   ├── database.db          # SQLite database (fallback)
│   └── memories/            # Stored project knowledge
├── src/                     # Your project code
├── package.json             # Your project dependencies
└── README.md               # Project documentation
```

## Advanced Configuration

### Custom Project Path

Set a custom project path in your environment:

```bash
export NEURODOCK_PROJECT_PATH="/path/to/your/project"
npx @neurodock/mcp-server
```

### Multiple Projects

Use different MCP server instances for different projects:

```json
{
  "mcpServers": {
    "neurodock-project-a": {
      "command": "npx",
      "args": ["@neurodock/mcp-server"],
      "env": {
        "NEURODOCK_PROJECT_PATH": "/path/to/project-a"
      }
    },
    "neurodock-project-b": {
      "command": "npx",
      "args": ["@neurodock/mcp-server"],
      "env": {
        "NEURODOCK_PROJECT_PATH": "/path/to/project-b"
      }
    }
  }
}
```

## Troubleshooting

### Python Dependencies

If you get Python import errors, install NeuroDock dependencies:

```bash
pip3 install -r requirements.txt
# or
pip3 install neurodock
```

### Database Connection

The MCP server will automatically fall back to SQLite if PostgreSQL/Qdrant aren't available, so it works out of the box on any project.

### Permission Issues

Make sure the MCP server has read/write access to your project directory:

```bash
chmod -R 755 your-project-directory
```

## Benefits

✅ **Instant AI Project Management** - Start using AI for project planning immediately
✅ **Zero Setup** - Works with NPX out of the box
✅ **Persistent Memory** - All decisions and tasks are saved
✅ **Agile Workflows** - Built-in requirements gathering and sprint planning
✅ **Cross-Project** - Use the same tools across all your projects

## Next Steps

1. **Try the requirements gathering**: Use the prompt templates to plan your project
2. **Create your first tasks**: Break down your project into manageable tasks
3. **Store decisions**: Keep track of technical decisions and rationale
4. **Use discussions**: Leverage multi-round AI conversations for complex planning

The NeuroDock MCP server transforms any project into an AI-powered, well-organized development workflow!
