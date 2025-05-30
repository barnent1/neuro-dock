# NeuroDock 🧠⚓

> **AI-Human Collaborative Development Platform with MCP Integration**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-brightgreen.svg)](https://modelcontextprotocol.io/)

NeuroDock is an intelligent development orchestration platform designed for seamless AI-human collaboration. It provides task tracking, memory management, and project state persistence while enabling AI assistants to handle intelligent code generation and problem-solving through Model Context Protocol (MCP) integration.

## 🌟 Architecture Philosophy

**Three-Tier Design for Optimal AI-Human Collaboration:**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Human Dev     │────│  AI Assistant    │────│   NeuroDock     │
│  (Direction &   │    │ (Intelligence &  │    │ (Tasks, Memory  │
│   Oversight)    │    │  Execution)      │    │  & Persistence) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌──────────────────┐
                    │   MCP Server     │
                    │ (Task Management │
                    │  & Memory Tools) │
                    └──────────────────┘
```

1. **NeuroDock Core**: Reliable task tracking, memory management, project state
2. **MCP Server**: Provides AI assistants with tools to manage tasks and memory
3. **AI Assistant**: Intelligent code generation, adaptive problem-solving, error handling
4. **Human Developer**: Provides direction, oversight, and domain expertise

## 🚀 Key Features

### 🔗 **MCP Server Integration** *(Revolutionary!)*
- **Seamless AI Integration**: AI assistants can manage tasks and memory directly
- **Real-time Task Updates**: AI updates task status as work progresses
- **Memory-Aware Development**: AI has full project context and history
- **Adaptive Problem Solving**: AI can handle errors and edge cases intelligently
- **Tool-Based Interface**: Standardized MCP tools for task and memory management

### 🧠 **Intelligent Task Management**
- **AI-Managed Tasks**: Tasks tracked and updated by AI assistants automatically
- **Context-Aware Execution**: Full project memory available to AI during development
- **Error-Resilient**: AI can adapt and fix issues in real-time
- **Human Oversight**: Developers provide direction while AI handles execution

### 💾 **Persistent Memory System**
- **Cross-Session Continuity**: Complete project state preserved across sessions
- **Rich Context**: Conversations, decisions, and project history maintained
- **Vector + Relational Storage**: Qdrant + PostgreSQL for comprehensive memory
- **AI-Accessible**: Memory system designed for AI assistant consumption

### 🎯 **Development Workflow**
- **Conversational Planning**: Start with natural language project descriptions
- **Intelligent Breakdown**: AI creates detailed, manageable tasks
- **Adaptive Execution**: AI handles coding while tracking progress
- **Human Direction**: Developers guide direction and review outcomes

## 🚀 Quick Start

### Installation

```bash
# Install NeuroDock
pip install -e .

# Setup system and database
nd setup

# Start a new project
mkdir my-project && cd my-project
nd init
```

### Basic Workflow

```bash
# Start project discussion
nd discuss

# Generate task plan
nd plan

# Start MCP server for AI integration
nd mcp-server

# Now your AI assistant can manage development using MCP tools!
```

### With AI Assistant Integration

```bash
# In your AI environment (Claude, ChatGPT, etc.)
# Connect to the NeuroDock MCP server
# The AI can now:
# - View and update tasks
# - Access project memory
# - Track development progress
# - Handle errors intelligently
```

## 🛠️ MCP Tools Available to AI

When connected via MCP server, AI assistants have access to:

- `get_tasks()` - Retrieve current task list and status
- `update_task(task_id, status, notes)` - Update task progress
- `get_project_memory()` - Access full project context and history
- `add_memory(content, type)` - Store important decisions or information
- `get_project_status()` - Get overall project health and progress
- `create_task(name, description, type)` - Add new tasks as needed

## 🏗️ Development Process

### 1. Project Initiation
```bash
nd init               # Initialize project
nd discuss           # Clarify requirements
nd plan              # Generate task breakdown
```

### 2. AI-Managed Development
```bash
nd mcp-server        # Start MCP server
# AI assistant connects and begins development
# Tasks are automatically tracked and updated
# Memory is preserved throughout the process
```

### 3. Human Oversight
- Review AI progress through task updates
- Provide direction and course corrections
- Approve major architectural decisions
- Handle domain-specific requirements

## 📁 Project Structure

```
my-project/
├── .neuro-dock/           # NeuroDock project data
│   ├── config.yml         # Project configuration
│   ├── tasks.json         # Task definitions and status
│   └── memory/            # Project memory storage
├── src/                   # Your source code (managed by AI)
├── docs/                  # Documentation (auto-generated)
└── tests/                 # Tests (AI-generated)
```

## 🔧 Configuration

### Environment Setup (.env)
```bash
# LLM Configuration
NEURO_LLM=ollama
NEURO_OLLAMA_MODEL=mixtral

# Database Configuration
POSTGRES_URL=postgresql://user:pass@localhost:5432/neurodock

# MCP Server Configuration
MCP_SERVER_PORT=3000
MCP_SERVER_HOST=localhost
```

### Project Configuration (.neuro-dock/config.yml)
```yaml
project:
  name: "My Project"
  description: "Project description"
  type: "web-app"
  
mcp:
  enabled: true
  port: 3000
  
ai_settings:
  auto_task_updates: true
  memory_integration: true
  error_handling: adaptive
```

## 🎯 Use Cases

### For Individual Developers
- **Rapid Prototyping**: AI handles boilerplate while you focus on business logic
- **Learning**: AI explains decisions and teaches best practices
- **Error Resolution**: AI fixes common issues automatically

### For Development Teams
- **Consistent Development**: Standardized AI-assisted workflow
- **Knowledge Sharing**: Shared memory across team members
- **Quality Assurance**: AI enforces coding standards and best practices

### For Complex Projects
- **Large Codebases**: AI maintains context across entire project
- **Multiple Technologies**: AI adapts to different tech stacks
- **Long-term Maintenance**: Project memory enables consistent evolution

## 🔐 Advanced Features

### Multi-LLM Support
- **Ollama**: Local models for privacy and control
- **Claude**: Enterprise-grade reasoning and code generation
- **OpenAI**: GPT models for specific use cases
- **Custom**: Integrate any LLM via standardized interface

### Enterprise Integration
- **Version Control**: Git integration with intelligent commit messages
- **CI/CD**: Integration with build and deployment pipelines
- **Team Collaboration**: Shared project memory and task tracking
- **Security**: Secure handling of sensitive project data

### Extensibility
- **Custom MCP Tools**: Add project-specific tools for AI assistants
- **Plugin System**: Extend functionality with custom modules
- **API Integration**: Connect to external services and databases
- **Workflow Customization**: Adapt to specific development methodologies

## 📚 Documentation

- **[MCP Integration Guide](documentation/mcp/integration.md)** - Complete MCP setup and usage
- **[Task Management](documentation/tasks/management.md)** - AI-managed task workflows
- **[Memory System](documentation/memory/system.md)** - Project memory and context
- **[Configuration](documentation/config/settings.md)** - All configuration options
- **[API Reference](documentation/api/reference.md)** - Complete API documentation

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup
```bash
git clone https://github.com/neurodock/neurodock.git
cd neurodock
pip install -e .[dev]
pytest tests/
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) for AI integration standards
- [Typer](https://typer.tiangolo.com/) for beautiful CLI interfaces
- [Qdrant](https://qdrant.tech/) for vector memory storage
- [PostgreSQL](https://postgresql.org/) for reliable data persistence

---

**NeuroDock**: Intelligent development orchestration for the AI era. Where human creativity meets AI capability.
