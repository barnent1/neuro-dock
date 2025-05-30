# NeuroDock MCP Server

Model Context Protocol (MCP) server for NeuroDock project management. This server provides AI assistants with access to NeuroDock's project management capabilities through standardized MCP tools.

## Features

The NeuroDock MCP server exposes 7 powerful tools for AI-human collaboration:

- **`neurodock_get_project_status`** - Get current project status and activity
- **`neurodock_list_tasks`** - List and filter project tasks
- **`neurodock_update_task`** - Update task status and notes
- **`neurodock_create_task`** - Create new tasks
- **`neurodock_add_memory`** - Store project information and decisions
- **`neurodock_search_memory`** - Search project history and knowledge
- **`neurodock_get_project_context`** - Get comprehensive project context

## Installation

Install globally using npx:

```bash
npx @neurodock/mcp-server
```

Or install the package:

```bash
npm install -g @neurodock/mcp-server
```

## Requirements

- **Node.js** 18+ (for npx execution)
- **Python** 3.10+ (for MCP server implementation)
- **NeuroDock** CLI installed and configured

The server will automatically install Python dependencies on first run.

## Usage

### With Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json`):

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

### With Other MCP Clients

The server can be used with any MCP-compatible client by running:

```bash
npx @neurodock/mcp-server
```

## Configuration

The server automatically detects:

- NeuroDock installation directory
- Project database location
- Current project context

No additional configuration is required if NeuroDock is properly installed.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │    │   Node.js       │    │   Python MCP    │
│  (Claude, etc.) │◄──►│   Wrapper       │◄──►│    Server       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                               ┌─────────────────┐
                                               │   NeuroDock     │
                                               │   CLI & DB      │
                                               └─────────────────┘
```

- **Node.js Wrapper**: Handles `npx` execution and process management
- **Python Server**: Implements MCP protocol with FastMCP
- **NeuroDock Integration**: Connects to CLI commands and SQLite database

## Development

### Local Development

```bash
# Clone the repository
git clone <repo-url>
cd neuro-dock/mcp-server

# Install dependencies
npm install
pip install -r requirements.txt

# Run directly
node src/index.js
# Or
python3 src/server.py
```

### Testing

```bash
# Test the server
npm test

# Test with MCP Inspector
npx @modelcontextprotocol/inspector npx @neurodock/mcp-server
```

## Tool Reference

### neurodock_get_project_status

Get current project status including recent tasks, memories, and git information.

**Parameters:**
- `project_path` (optional): Path to specific project directory

### neurodock_list_tasks

List tasks with optional filtering.

**Parameters:**
- `status` (optional): Filter by status (pending, in_progress, completed, failed, all)
- `limit` (optional): Maximum results (default: 10)

### neurodock_update_task

Update an existing task.

**Parameters:**
- `task_id` (required): Task ID to update
- `status` (optional): New status
- `notes` (optional): Additional notes

### neurodock_create_task

Create a new task.

**Parameters:**
- `description` (required): Task description
- `priority` (optional): Priority level (low, medium, high)
- `category` (optional): Task category

### neurodock_add_memory

Store important project information.

**Parameters:**
- `content` (required): Information to store
- `category` (optional): Memory category (note, decision, requirement, etc.)
- `tags` (optional): Array of tags for organization

### neurodock_search_memory

Search stored project memories.

**Parameters:**
- `query` (required): Search terms
- `category` (optional): Filter by category
- `limit` (optional): Maximum results (default: 5)

### neurodock_get_project_context

Get comprehensive project context.

**Parameters:**
- `include_files` (optional): Include file structure (default: true)
- `include_git` (optional): Include git status (default: true)

## License

MIT License - see LICENSE file for details.

## Contributing

See the main NeuroDock repository for contribution guidelines.
