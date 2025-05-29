# NeuroDock 🧠⚓

> **AI-Orchestrated Agile Development System**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

NeuroDock is an innovative AI-orchestrated development system that transforms how software projects are built. It combines the power of Large Language Models with structured Agile methodology to create an intelligent development assistant that can take projects from concept to completion.

## 🌟 Key Features

### 🤖 Dual Agent Architecture
- **Navigator (Conversational)**: Intelligent conversation facilitator that guides developers through structured Agile processes
- **NeuroDock (Execution)**: Any LLM backend that executes technical tasks with rich context

### 🧠 Advanced Memory System
- **Dual Storage**: Qdrant (vector) + Neo4J (graph) for comprehensive context preservation
- **Cross-Session Memory**: Conversations and decisions persist across development sessions
- **Contextual Reminders**: NeuroDock receives intelligent reminders based on conversation history

### 📋 Structured Agile Workflow
- **9 Comprehensive Phases**: From project initiation to retrospective
- **Conversation-Driven**: Detailed discussions before any code execution
- **Keyword Triggers**: Natural language progression controls (e.g., "proceed to requirements")
- **Human-Controlled**: Developers maintain complete control over when execution happens

### 🔧 Technical Excellence
- **Enterprise-Grade Database**: PostgreSQL backend with intelligent schema management
- **Flexible LLM Integration**: Works with Claude, OpenAI, Ollama, and custom endpoints
- **Production-Ready**: Comprehensive error handling and graceful fallbacks
- **Extensible Architecture**: Modular design for easy customization and extension

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/neurodock.git
cd neurodock

# Install dependencies
pip install -r requirements.txt

# Set up the system
python -m neurodock.cli setup

# Initialize your first project
python -m neurodock.cli init
```

### Your First AI-Guided Project

```bash
# Start a conversation with Navigator
python -m neurodock.cli begin

# Navigator will guide you through:
# 1. Project vision discussion
# 2. Requirements gathering with NeuroDock
# 3. Sprint planning and task breakdown
# 4. Technical design and architecture
# 5. Iterative development cycles
# 6. Testing and quality assurance
# 7. Code review and optimization
# 8. Deployment and release
# 9. Project retrospective
```

## 🏗️ How It Works

### The Conversation-First Approach

1. **Deep Discussions**: Navigator facilitates thorough conversations about each project phase
2. **Memory Storage**: Important insights and decisions are stored in the dual memory system
3. **Keyword Triggers**: When ready, you say phrases like "proceed to requirements" to advance
4. **NeuroDock Execution**: Commands are issued to NeuroDock with full conversation context
5. **Result Integration**: Navigator interprets results and continues the conversation

### Example Workflow

```
You: "I want to build a task management app for small teams"

Navigator: "Excellent! Let's explore this vision together..."
[Detailed conversation about goals, users, features]

You: "proceed to requirements"

Navigator: "Perfect! Engaging NeuroDock for detailed requirements gathering..."
[NeuroDock works with full context from conversation]

Navigator: "Based on NeuroDock's analysis, here are some clarifying questions..."
[Continues facilitating until you're ready for next phase]
```

## 📚 Documentation

- **[System Overview](docs/README.md)** - Complete system documentation
- **[Setup Guide](docs/setup/)** - Installation and configuration
- **[Architecture](docs/architecture/)** - Technical architecture details
- **[Development](docs/development/)** - Development workflow and contribution guide

## 🛠️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Developer     │────│    Navigator     │────│   NeuroDock     │
│  (Chat Window)  │    │ (Conversation    │    │  (Any LLM via   │
│                 │    │  Facilitator)    │    │   CLI/Terminal) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌──────────────────┐
                    │   Dual Memory    │
                    │   Qdrant + Neo4J │
                    │   PostgreSQL     │
                    └──────────────────┘
```

### Core Components

- **CLI Interface**: Comprehensive command-line interface with conversational commands
- **Conversational Agent**: Structured Agile script following with intelligent progression
- **Memory Systems**: Vector similarity search + graph relationships + relational storage
- **LLM Integration**: Flexible backends supporting multiple AI providers
- **Database Layer**: PostgreSQL with intelligent schema management

## 🎯 Use Cases

### For Solo Developers
- **Rapid Prototyping**: From idea to working prototype with AI guidance
- **Learning**: Understand best practices through AI mentorship
- **Code Quality**: Automated review and optimization suggestions

### For Development Teams
- **Project Planning**: AI-assisted sprint planning and task breakdown
- **Knowledge Sharing**: Persistent memory across team sessions
- **Consistency**: Standardized development workflows

### For Organizations
- **Development Acceleration**: Reduce time-to-market for new features
- **Quality Assurance**: Built-in testing and review processes
- **Documentation**: Automated documentation generation and maintenance

## 🔐 Enterprise Features

- **Security**: Secure handling of sensitive project data
- **Scalability**: Designed for projects of any size
- **Integration**: Works with existing development workflows
- **Customization**: Extensible architecture for specific organizational needs

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone and setup development environment
git clone https://github.com/yourusername/neurodock.git
cd neurodock

# Install in development mode
pip install -e .

# Run tests
pytest tests/

# Run linting
black src/
flake8 src/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Typer](https://typer.tiangolo.com/) for beautiful CLI interfaces
- Powered by [Qdrant](https://qdrant.tech/) for vector similarity search
- Enhanced with [Neo4J](https://neo4j.com/) for graph relationships
- Inspired by modern Agile development methodologies

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/neurodock/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/neurodock/discussions)
- **Documentation**: [Full Documentation](docs/)

---

**NeuroDock**: Where AI meets Agile development. Build better software, faster, with intelligent guidance every step of the way.
