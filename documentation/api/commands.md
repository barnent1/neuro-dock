# NeuroDock API Reference

## Overview

NeuroDock provides a comprehensive command-line interface (CLI) and programmatic API for interacting with the dual-agent system. This reference covers all available commands, parameters, and usage patterns.

## Command Structure

```bash
# Basic command structure
neurodock [GLOBAL_OPTIONS] <command> [COMMAND_OPTIONS] [ARGUMENTS]

# Alternative execution methods
python -m src.cli.main <command> [options]
python neurodock.py <command> [options]
```

## Global Options

| Option | Description | Default |
|--------|-------------|---------|
| `--config, -c` | Path to configuration file | `~/.neuro-dock/.neuro-dock.md` |
| `--verbose, -v` | Enable verbose logging | `false` |
| `--debug` | Enable debug mode | `false` |
| `--profile` | Profile to use | `default` |
| `--log-level` | Set logging level | `INFO` |
| `--no-color` | Disable colored output | `false` |

## Core Commands

### 1. Conversation Commands

#### `discuss` - Interactive Requirements Discussion

Start an interactive discussion session to clarify project goals and generate structured task plans. Features an enhanced Codex-style interface for new projects.

**Syntax:**
```bash
neurodock discuss [OPTIONS]
```

**Options:**
| Option | Description | Type | Default |
|--------|-------------|------|---------|
| `--dry-run` | Test interface without LLM calls | `boolean` | `false` |
| `--skip-init` | Skip auto-initialization | `boolean` | `false` |

**Enhanced Features:**
- **Smart Detection**: Automatically detects existing `prompt.txt` and adapts workflow
- **Codex-Style Interface**: Shows branded prompt interface for new projects
- **Auto-Initialization**: Creates `.neuro-dock` directory structure as needed
- **Visual Feedback**: Displays thinking animation during processing
- **Backward Compatibility**: Preserves existing workflow when `prompt.txt` exists

**Usage Examples:**

**First Time (New Project):**
```bash
cd my-project
neurodock discuss

🧠 NeuroDock
What would you like to build or clarify?
> I want to build a recipe site with search and markdown

( ● ) Thinking...

🎯 Starting interactive discussion...
[... clarification questions follow ...]
```

**Subsequent Runs (Existing Project):**
```bash
neurodock discuss

🎯 Starting interactive discussion...
📝 Initial prompt: I want to build a recipe site with search and markdown
[... proceeds directly to discussion ...]
```

**Complete Workflow:**
1. **Smart Detection**: Checks for existing `prompt.txt`
2. **Prompt Interface**: Shows Codex-style prompt if needed
3. **Auto-Save**: Saves user input to `prompt.txt`
4. **Thinking Animation**: Visual feedback while processing
5. **Full Discussion**: Continues with LLM-powered clarification
6. **Memory Integration**: Uses Qdrant vector memory for context
7. **Task Generation**: Creates structured `plan.yaml`
8. **File Management**: Updates `memory.json` and other files

**File Structure Created:**
```
.neuro-dock/
├── prompt.txt          # User's initial idea
├── memory.json         # Discussion history
├── plan.yaml          # Generated task plan
├── config.yaml        # Project configuration
├── tasklog.json       # Task execution log
└── outputs/           # Generated files
```

#### `discuss-status` - Check Discussion Status *(New!)*

Check the current status of an iterative discussion and determine what Navigator should do next.

**Syntax:**
```bash
neurodock discuss-status
```

**Purpose**: 
- Monitor multi-round discussion progress
- Provide guidance to Navigator on next actions
- Display pending questions and completion status

**Output:**
```bash
🗣️  Discussion Status Report
========================================
Status: questions_pending
Iteration: 1
Completion: 25%
Next Action: ask_developer_questions

📋 Pending Questions:
--------------------
1. What type of products will be sold on the website?
2. What payment methods should be supported?
3. Do you need inventory management features?
```

**Use Cases:**
- Navigator checking what questions to ask developer
- Monitoring discussion completion percentage
- Understanding next required action in workflow

#### `discuss-answer` - Provide Discussion Answers *(New!)*

Provide developer answers to continue iterative discussion process. Used by Navigator to feed developer responses back to the system.

**Syntax:**
```bash
echo "developer answers..." | neurodock discuss-answer
```

**Purpose**:
- Submit developer answers to system for analysis
- Continue iterative discussion workflow
- Enable multi-round question and answer cycles

**Input Method**: Expects answers via stdin (pipe input)

**Workflow:**
1. Navigator asks developer the pending questions
2. Navigator collects comprehensive answers
3. Navigator pipes answers using this command
4. System analyzes completeness and determines next steps

**Example:**
```bash
# Navigator provides answers from developer
echo "1. Digital products - software and courses
2. Stripe payment integration with credit cards  
3. Basic inventory tracking but not advanced warehouse management
4. Email/password auth plus Google OAuth
5. Expecting 1000-5000 users initially" | neurodock discuss-answer
```

**Response:**
```bash
📝 Processing answers and continuing discussion...
✅ Answers processed successfully!
💡 Next action: check_status_for_next_iteration
```

#### `chat` - Start Interactive Conversation

Start a conversation session with Agent 1.

**Syntax:**
```bash
neurodock chat [OPTIONS] [INITIAL_MESSAGE]
```

**Options:**
| Option | Description | Type | Default |
|--------|-------------|------|---------|
| `--session-id, -s` | Use specific session ID | `string` | auto-generated |
| `--project, -p` | Set project context | `string` | current directory |
| `--mode, -m` | Conversation mode | `interactive\|batch\|guided` | `interactive` |
| `--max-turns` | Maximum conversation turns | `integer` | unlimited |
| `--save-transcript` | Save conversation transcript | `boolean` | `true` |
| `--agent1-only` | Disable Agent 2 integration | `boolean` | `false` |

**Examples:**
```bash
# Start interactive conversation
neurodock chat

# Start with initial message
neurodock chat "Create a user authentication system"

# Start with specific session
neurodock chat --session-id user_session_123 "Continue previous work"

# Project-specific conversation
neurodock chat --project my-webapp "Add payment integration"

# Guided mode for structured conversations
neurodock chat --mode guided "I need help with database design"
```

**Response Format:**
```json
{
  "session_id": "uuid",
  "status": "active|completed|error",
  "agent_response": "Agent 1 response text",
  "context": {
    "project": "project_name",
    "phase": "current_agile_phase",
    "requirements": ["extracted", "requirements"],
    "next_steps": ["suggested", "actions"]
  },
  "agent2_tasks": [
    {
      "task_id": "uuid",
      "type": "implementation|testing|integration",
      "status": "queued|in_progress|completed",
      "description": "task description"
    }
  ]
}
```

#### `continue` - Continue Previous Conversation

Resume a previous conversation session.

**Syntax:**
```bash
neurodock continue [OPTIONS] <session_id> [MESSAGE]
```

**Options:**
| Option | Description | Type | Default |
|--------|-------------|------|---------|
| `--show-context` | Display conversation history | `boolean` | `false` |
| `--context-depth` | Number of previous messages to show | `integer` | `10` |

**Examples:**
```bash
# Continue session with new message
neurodock continue session_123 "Let's add error handling"

# Continue and show previous context
neurodock continue --show-context session_123

# Continue with limited context display
neurodock continue --context-depth 5 session_123 "Update the database schema"
```

#### `history` - View Conversation History

Display conversation history and session information.

**Syntax:**
```bash
neurodock history [OPTIONS] [SESSION_ID]
```

**Options:**
| Option | Description | Type | Default |
|--------|-------------|------|---------|
| `--limit, -n` | Limit number of sessions | `integer` | `10` |
| `--format` | Output format | `table\|json\|detailed` | `table` |
| `--project` | Filter by project | `string` | all projects |
| `--date-from` | Filter from date | `date` | no filter |
| `--date-to` | Filter to date | `date` | no filter |
| `--search` | Search in conversation content | `string` | no filter |

**Examples:**
```bash
# List recent sessions
neurodock history

# View specific session details
neurodock history session_123

# Search conversations
neurodock history --search "authentication"

# View project-specific history
neurodock history --project my-webapp --limit 20

# Export history as JSON
neurodock history --format json --limit 50 > conversations.json
```

### 2. Agent 2 Commands

#### `implement` - Execute Implementation Task

Directly invoke Agent 2 for implementation tasks.

**Syntax:**
```bash
neurodock implement [OPTIONS] <task_description>
```

**Options:**
| Option | Description | Type | Default |
|--------|-------------|------|---------|
| `--session-id, -s` | Associate with session | `string` | create new |
| `--task-type` | Type of implementation | `code\|test\|integration\|deploy` | `code` |
| `--files` | Target files to modify | `array` | auto-detect |
| `--dry-run` | Preview changes without executing | `boolean` | `false` |
| `--auto-test` | Run tests after implementation | `boolean` | `true` |
| `--backup` | Create backup before changes | `boolean` | `true` |

**Examples:**
```bash
# Implement feature
neurodock implement "Add user registration endpoint"

# Dry run to preview changes
neurodock implement --dry-run "Update database schema for user profiles"

# Implement with specific files
neurodock implement --files auth.py,models.py "Add OAuth2 support"

# Skip auto-testing
neurodock implement --auto-test false "Quick fix for login bug"
```

#### `test` - Run Test Suite

Execute tests through Agent 2.

**Syntax:**
```bash
neurodock test [OPTIONS] [TEST_PATTERN]
```

**Options:**
| Option | Description | Type | Default |
|--------|-------------|------|---------|
| `--type` | Test type | `unit\|integration\|e2e\|all` | `all` |
| `--coverage` | Generate coverage report | `boolean` | `false` |
| `--parallel` | Run tests in parallel | `boolean` | `true` |
| `--fail-fast` | Stop on first failure | `boolean` | `false` |
| `--verbose` | Verbose test output | `boolean` | `false` |

**Examples:**
```bash
# Run all tests
neurodock test

# Run specific test pattern
neurodock test test_auth*

# Run with coverage
neurodock test --coverage --type unit

# Integration tests only
neurodock test --type integration --verbose
```

#### `validate` - Validate Implementation

Check implementation quality and standards compliance.

**Syntax:**
```bash
neurodock validate [OPTIONS] [TARGET]
```

**Options:**
| Option | Description | Type | Default |
|--------|-------------|------|---------|
| `--checks` | Validation checks to run | `syntax\|style\|security\|performance\|all` | `all` |
| `--fix` | Auto-fix issues where possible | `boolean` | `false` |
| `--report` | Generate validation report | `boolean` | `true` |

**Examples:**
```bash
# Validate entire project
neurodock validate

# Validate specific file
neurodock validate src/auth.py

# Run security checks only
neurodock validate --checks security

# Validate and auto-fix
neurodock validate --fix --checks style
```

### 3. Memory and Context Commands

#### `memory` - Memory System Operations

Manage the memory system and context data.

**Syntax:**
```bash
neurodock memory <subcommand> [OPTIONS]
```

**Subcommands:**

##### `status` - Check Memory System Status
```bash
neurodock memory status [--detailed]
```

##### `search` - Search Memory Context
```bash
neurodock memory search [OPTIONS] <query>
```

**Options:**
| Option | Description | Type | Default |
|--------|-------------|------|---------|
| `--type` | Search type | `semantic\|keyword\|hybrid` | `semantic` |
| `--limit` | Number of results | `integer` | `10` |
| `--session` | Limit to session | `string` | all sessions |
| `--date-range` | Date range filter | `string` | no filter |

##### `export` - Export Memory Data
```bash
neurodock memory export [OPTIONS] <output_file>
```

**Options:**
| Option | Description | Type | Default |
|--------|-------------|------|---------|
| `--format` | Export format | `json\|csv\|sql` | `json` |
| `--include` | Data to include | `conversations\|implementations\|all` | `all` |
| `--session` | Specific session | `string` | all sessions |

##### `cleanup` - Clean Memory Data
```bash
neurodock memory cleanup [OPTIONS]
```

**Options:**
| Option | Description | Type | Default |
|--------|-------------|------|---------|
| `--older-than` | Remove data older than | `duration` | no deletion |
| `--dry-run` | Preview cleanup | `boolean` | `false` |
| `--orphaned` | Remove orphaned records | `boolean` | `false` |

**Examples:**
```bash
# Check memory system status
neurodock memory status --detailed

# Search for authentication-related conversations
neurodock memory search "user authentication" --type semantic

# Export recent conversations
neurodock memory export --include conversations conversations.json

# Cleanup old data (dry run)
neurodock memory cleanup --older-than 90d --dry-run
```

### 4. Project Initialization Commands

#### `init` - Initialize Current Directory

Initialize NeuroDock in the current project directory, setting up essential configuration and copying the Agent 1 template.

**Syntax:**
```bash
neurodock init
```

**Features:**
- **Database Verification**: Confirms PostgreSQL connection before proceeding
- **Project Structure**: Creates `.neuro-dock/` directory with essential configuration
- **Agent 1 Template**: Copies `.neuro-dock.md` template to project root for Agent 1 access
- **Smart Template Discovery**: Searches multiple locations for template file (repo root, current directory, package directory)
- **Documentation Links**: Provides helpful links to documentation resources

**File Structure Created:**
```
.neuro-dock/
├── config.yaml         # Project configuration
└── ...                 # Additional configuration files

.neuro-dock.md          # Agent 1 configuration template (copied to project root)
```

**Output Messages:**
- Database connection verification status
- Template copying confirmation
- Documentation links for further reference
- Next step suggestions

**Examples:**
```bash
# Initialize current directory
cd my-project
neurodock init

# Expected output:
✅ Database connection verified
✅ Agent 1 configuration template copied
✅ Project initialized in: /path/to/my-project
🚀 Ready to start! Try: nd discuss

📚 Documentation:
   • Project guide: .neuro-dock.md (copied to your project)
   • Full docs: https://github.com/barnent1/neuro-dock/tree/main/documentation
   • API reference: https://github.com/barnent1/neuro-dock/blob/main/documentation/api/commands.md
```

**Error Handling:**
- Prevents initialization if `.neuro-dock` already exists
- Displays helpful error messages for database connection issues
- Provides fallback guidance when template file cannot be found
- Suggests running `nd setup` for database configuration problems

### 5. Project Management Commands

#### `project` - Project Operations

Manage project configuration and settings.

**Syntax:**
```bash
neurodock project <subcommand> [OPTIONS]
```

**Subcommands:**

##### `init` - Initialize Project
```bash
neurodock project init [OPTIONS] [PROJECT_NAME]
```

**Options:**
| Option | Description | Type | Default |
|--------|-------------|------|---------|
| `--template` | Project template | `string` | `default` |
| `--language` | Primary language | `python\|javascript\|typescript\|java\|other` | auto-detect |
| `--framework` | Framework | `string` | auto-detect |

##### `config` - Project Configuration
```bash
neurodock project config [OPTIONS] [KEY] [VALUE]
```

**Options:**
| Option | Description | Type | Default |
|--------|-------------|------|---------|
| `--list` | List all configuration | `boolean` | `false` |
| `--delete` | Delete configuration key | `boolean` | `false` |
| `--global` | Global configuration | `boolean` | `false` |

##### `status` - Project Status
```bash
neurodock project status [OPTIONS]
```

**Examples:**
```bash
# Initialize new project
neurodock project init my-webapp --language python --framework fastapi

# View project configuration
neurodock project config --list

# Set project configuration
neurodock project config database.type postgresql

# Check project status
neurodock project status
```

### 6. System Commands

#### `system` - System Operations

System-level operations and diagnostics.

**Syntax:**
```bash
neurodock system <subcommand> [OPTIONS]
```

**Subcommands:**

##### `health` - System Health Check
```bash
neurodock system health [OPTIONS]
```

**Options:**
| Option | Description | Type | Default |
|--------|-------------|------|---------|
| `--detailed` | Detailed health report | `boolean` | `false` |
| `--fix` | Auto-fix issues | `boolean` | `false` |

##### `logs` - View System Logs
```bash
neurodock system logs [OPTIONS]
```

**Options:**
| Option | Description | Type | Default |
|--------|-------------|------|---------|
| `--follow, -f` | Follow log output | `boolean` | `false` |
| `--lines, -n` | Number of lines | `integer` | `100` |
| `--level` | Log level filter | `debug\|info\|warning\|error` | `info` |
| `--component` | Component filter | `agent1\|agent2\|memory\|cli` | all |

##### `reset` - Reset System State
```bash
neurodock system reset [OPTIONS]
```

**Options:**
| Option | Description | Type | Default |
|--------|-------------|------|---------|
| `--confirm` | Confirm reset operation | `boolean` | required |
| `--preserve-config` | Keep configuration | `boolean` | `true` |
| `--preserve-data` | Keep conversation data | `boolean` | `false` |

**Examples:**
```bash
# Check system health
neurodock system health --detailed

# Follow system logs
neurodock system logs --follow --level debug

# Reset system (with confirmation)
neurodock system reset --confirm --preserve-data
```

## Programmatic API

### Python API

#### Client Initialization

```python
from src.api.client import NeuroDockClient

# Initialize client
client = NeuroDockClient(
    config_path="~/.neuro-dock/.neuro-dock.md",
    profile="default"
)

# Initialize with custom settings
client = NeuroDockClient(
    config={
        "openai_api_key": "your_key",
        "database_url": "postgresql://...",
        "memory_enabled": True
    }
)
```

#### Conversation API

```python
# Start conversation
session = await client.chat.start_session(
    project="my-webapp",
    initial_message="Create a user authentication system"
)

# Continue conversation
response = await client.chat.send_message(
    session_id=session.id,
    message="Add OAuth2 support with Google and GitHub"
)

# Get conversation history
history = await client.chat.get_history(
    session_id=session.id,
    limit=20
)
```

#### Implementation API

```python
# Execute implementation
task = await client.agent2.implement(
    description="Add user registration endpoint",
    session_id=session.id,
    task_type="code",
    auto_test=True
)

# Check task status
status = await client.agent2.get_task_status(task.id)

# Get implementation results
result = await client.agent2.get_task_result(task.id)
```

#### Memory API

```python
# Search memory
results = await client.memory.search(
    query="user authentication",
    search_type="semantic",
    limit=10
)

# Get context for session
context = await client.memory.get_context(
    session_id=session.id,
    depth=15
)

# Store custom context
await client.memory.store_context(
    session_id=session.id,
    context_type="requirement",
    content="System must support SAML SSO"
)
```

### REST API

NeuroDock also provides a REST API for integration with external systems.

#### Authentication

```bash
# Set API key
export NEURODOCK_API_KEY="your_api_key"

# Or use in headers
curl -H "Authorization: Bearer your_api_key" \
     -H "Content-Type: application/json" \
     https://api.neurodock.local/v1/sessions
```

#### Endpoints

##### Start Conversation
```http
POST /v1/chat/sessions
Content-Type: application/json

{
  "project": "my-webapp",
  "initial_message": "Create user authentication",
  "mode": "interactive"
}
```

##### Send Message
```http
POST /v1/chat/sessions/{session_id}/messages
Content-Type: application/json

{
  "message": "Add OAuth2 support",
  "context": {
    "user_preferences": ["security", "ease_of_use"]
  }
}
```

##### Execute Implementation
```http
POST /v1/agent2/tasks
Content-Type: application/json

{
  "session_id": "uuid",
  "description": "Implement user registration",
  "task_type": "code",
  "options": {
    "auto_test": true,
    "backup": true
  }
}
```

##### Search Memory
```http
GET /v1/memory/search?q=authentication&type=semantic&limit=10
```

## Configuration Reference

### Main Configuration File

The `.neuro-dock.md` file serves as both configuration and context for Agent 1:

```markdown
# NeuroDock Configuration

## Project Context
- **Project Type**: Web Application
- **Primary Language**: Python
- **Framework**: FastAPI
- **Database**: PostgreSQL
- **Frontend**: React

## Agent 1 Settings
- **Conversation Style**: Professional, thorough
- **Agile Phase Focus**: Requirements, Implementation, Testing
- **Default Response Length**: Detailed
- **Auto-delegate to Agent 2**: true

## Agent 2 Settings
- **Auto-test**: true
- **Backup before changes**: true
- **Parallel execution**: true
- **Max concurrent tasks**: 3

## Memory System
- **Semantic search enabled**: true
- **Context depth**: 15 messages
- **Auto-cleanup**: 90 days
- **Vector similarity threshold**: 0.7

## LLM Configuration
- **Primary Provider**: OpenAI
- **Model**: gpt-4
- **Fallback Provider**: Anthropic
- **Fallback Model**: claude-3-sonnet
- **Temperature**: 0.1
- **Max Tokens**: 4000

## Conversation Preferences
- **Code examples**: Always include
- **Architecture diagrams**: When relevant
- **Step-by-step guides**: For complex tasks
- **Error handling**: Comprehensive
- **Testing approach**: TDD preferred
```

### Environment Variables

```bash
# Core API Keys
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
NEURODOCK_API_KEY=your_neurodock_api_key

# Database Configuration
DATABASE_URL=postgresql://user:pass@host:port/db
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_key
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

# System Configuration
NEURODOCK_CONFIG_PATH=~/.neuro-dock/.neuro-dock.md
NEURODOCK_LOG_LEVEL=INFO
NEURODOCK_DEBUG=false
NEURODOCK_PROFILE=default

# Performance Settings
NEURODOCK_MAX_WORKERS=4
NEURODOCK_TIMEOUT=300
NEURODOCK_MEMORY_CACHE_TTL=3600

# Security Settings
NEURODOCK_SECURE_MODE=true
NEURODOCK_RATE_LIMIT=100
NEURODOCK_MAX_SESSION_DURATION=3600
```

## Error Codes and Handling

### Common Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| `E001` | Configuration file not found | Create `.neuro-dock.md` or specify path |
| `E002` | API key invalid or missing | Check environment variables |
| `E003` | Database connection failed | Verify database configuration |
| `E004` | Memory system unavailable | Check Qdrant/Neo4J connectivity |
| `E005` | Agent 2 execution failed | Check implementation logs |
| `E006` | Session not found | Verify session ID |
| `E007` | Invalid command syntax | Check command reference |
| `E008` | Rate limit exceeded | Wait or check rate limit settings |
| `E009` | Memory quota exceeded | Clean up old data |
| `E010` | Validation failed | Check input parameters |

### Error Response Format

```json
{
  "error": {
    "code": "E005",
    "message": "Agent 2 execution failed",
    "details": "Implementation task timeout after 300 seconds",
    "context": {
      "session_id": "uuid",
      "task_id": "uuid",
      "timestamp": "2024-01-15T10:30:00Z"
    },
    "suggestions": [
      "Check system resources",
      "Increase timeout setting",
      "Retry with smaller task scope"
    ]
  }
}
```

## Rate Limits and Quotas

### Default Limits

| Resource | Limit | Period |
|----------|-------|--------|
| API Requests | 1000 | per hour |
| Chat Messages | 100 | per hour |
| Implementation Tasks | 20 | per hour |
| Memory Searches | 500 | per hour |
| File Operations | 50 | per minute |

### Quota Management

```bash
# Check current usage
neurodock system quota --show

# Request quota increase
neurodock system quota --request-increase --resource api_requests --limit 2000
```

## Examples and Use Cases

### Complete Workflow Example

```bash
# 1. Initialize project
neurodock project init my-webapp --language python --framework fastapi

# 2. Start conversation
neurodock chat "I want to build a user management system with authentication"

# 3. Continue with specific requirements
neurodock continue session_123 "Add support for role-based access control"

# 4. Direct implementation
neurodock implement "Create database migrations for user roles"

# 5. Test implementation
neurodock test --type integration --coverage

# 6. Validate results
neurodock validate --checks all

# 7. View conversation history
neurodock history --project my-webapp --format detailed
```

### Batch Processing Example

```bash
# Create batch task file
cat > tasks.json << EOF
{
  "project": "my-webapp",
  "tasks": [
    {
      "type": "conversation",
      "message": "Design user authentication system"
    },
    {
      "type": "implementation",
      "description": "Implement JWT token handling"
    },
    {
      "type": "test",
      "pattern": "test_auth*",
      "coverage": true
    }
  ]
}
EOF

# Execute batch
neurodock batch --file tasks.json --sequential
```

This comprehensive API reference covers all available commands, options, and usage patterns for NeuroDock's dual-agent system. For additional examples and advanced usage, see the [Development Guide](../development/getting-started.md).
