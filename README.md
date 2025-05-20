# NeuroDock

NeuroDock is a powerful memory and task execution system for AI agents using Neo4j and the Model Context Protocol (MCP). It provides a foundation for building intelligent, contextually-aware applications that can store memories, manage tasks, and make autonomous decisions.

## Features

- **Memory Storage and Retrieval**: Store and query memories with different types and confidence levels
- **Task Management System**: Create tasks, subtasks, and track their progress
- **Context Selection**: Retrieve relevant context for queries
- **Model Context Protocol (MCP)**: Full MCP implementation for integration with VSCode and other applications
- **Autonomous Agent**: Built-in agent powered by OpenAI's GPT-4o for task execution
- **Docker Support**: Easy deployment with Docker and docker-compose
- **Web Interface**: Memory dashboard for browsing, searching, and managing memories

## Architecture

NeuroDock consists of the following components:

- **FastAPI Backend**: High-performance API server
- **Neo4j Graph Database**: Stores memory nodes and their relationships
- **OpenAI Integration**: Uses GPT-4o for intelligent decisions
- **MCP Server**: Implements the Model Context Protocol
- **Docker Support**: Easy deployment with Docker and docker-compose
- **Web Dashboard**: User-friendly interface for memory management

## Getting Started

### Prerequisites

- Docker and docker-compose
- OpenAI API Key (optional, for autonomous agent functionality)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-organization/neuro-dock.git
cd neuro-dock

# Create a .env file with your configuration
cp .env.example .env
# Edit .env with your settings

# Start the services
docker-compose up -d
```

The application will be available at http://localhost:4000
