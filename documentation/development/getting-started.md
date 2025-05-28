
# Development Guide

## Overview

This guide covers development workflows, contribution guidelines, and advanced usage patterns for NeuroDock. Whether you're contributing to the core system or building integrations, this guide will help you get started.

## Development Environment Setup

### Prerequisites

Before you begin development on NeuroDock, ensure you have:

1. **Python 3.9+** with pip
2. **Node.js 16+** (if working on frontend components)
3. **Docker & Docker Compose** (for local infrastructure)
4. **Git** with SSH keys configured
5. **Code editor** with Python support (VSCode recommended)

### Local Development Setup

#### 1. Clone and Install

```bash
# Clone the repository
git clone https://github.com/your-org/neurodock.git
cd neurodock

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows

# Install development dependencies
pip install -e ".[dev]"
pip install -r requirements-dev.txt
```

#### 2. Database Setup for Development

```bash
# Start development databases using Docker Compose
docker-compose -f docker-compose.dev.yml up -d

# Run database migrations
python -m src.db.migrate

# Seed development data (optional)
python -m src.db.seed --dev-data
```

#### 3. Configuration

```bash
# Copy development environment template
cp .env.example .env.dev

# Edit development configuration
nano .env.dev
```

**Development Environment Variables:**
```bash
# Development settings
NEURODOCK_ENV=development
NEURODOCK_DEBUG=true
NEURODOCK_LOG_LEVEL=DEBUG

# Development databases
DATABASE_URL=postgresql://dev:dev@localhost:5432/neurodock_dev
QDRANT_URL=http://localhost:6333
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=dev_password

# Development API keys (use test keys)
OPENAI_API_KEY=sk-test-your-development-key
ANTHROPIC_API_KEY=test-your-anthropic-key

# Development-specific settings
NEURODOCK_RATE_LIMIT=1000
NEURODOCK_MAX_WORKERS=2
NEURODOCK_TIMEOUT=60
```

#### 4. Verify Installation

```bash
# Run health check
python -m src.diagnostics.health_check

# Run development tests
pytest tests/ -v

# Start development server
python -m src.cli.main --profile development
```

## Project Structure

### Core Architecture

```
src/
├── neurodock/                 # Main package
│   ├── __init__.py
│   ├── agent.py              # Base agent classes
│   ├── cli.py                # Command-line interface
│   ├── config.py             # Configuration management
│   └── conversational_agent.py # Agent 1 implementation
│
├── agents/                   # Agent implementations
│   ├── agent1/              # Conversational agent
│   │   ├── conversation.py
│   │   ├── planning.py
│   │   └── coordination.py
│   └── agent2/              # Implementation agent
│       ├── implementation.py
│       ├── testing.py
│       └── validation.py
│
├── memory/                  # Memory system
│   ├── __init__.py
│   ├── core_manager.py     # Central memory manager
│   ├── postgres_store.py   # PostgreSQL operations
│   ├── qdrant_store.py     # Vector database
│   ├── neo4j_store.py      # Graph database
│   └── sync_manager.py     # Synchronization
│
├── api/                    # REST API
│   ├── routes/            # API route definitions
│   ├── middleware/        # Custom middleware
│   └── client.py          # Python client library
│
├── utils/                 # Utility modules
│   ├── animation.py      # CLI animations
│   ├── models.py         # Data models
│   └── logging.py        # Logging configuration
│
└── tests/                # Test suites
    ├── unit/             # Unit tests
    ├── integration/      # Integration tests
    └── e2e/              # End-to-end tests
```

### Configuration Files

```
├── .env.example          # Environment template
├── .env.dev             # Development environment
├── .env.test            # Test environment
├── .neuro-dock.md       # Agent 1 configuration
├── pyproject.toml       # Python project configuration
├── requirements.txt     # Production dependencies
├── requirements-dev.txt # Development dependencies
└── docker-compose.dev.yml # Development infrastructure
```

## Development Workflows

### 1. Feature Development

#### Standard Feature Workflow

```bash
# 1. Create feature branch
git checkout -b feature/user-authentication

# 2. Implement feature with tests
# - Write failing tests first (TDD)
# - Implement feature code
# - Update documentation

# 3. Run test suite
pytest tests/ -v --cov=src/

# 4. Run integration tests
python test_dual_agent_workflow.py

# 5. Validate with Agent 1
python -m src.cli.main chat "Test the new authentication feature"

# 6. Create pull request
git add .
git commit -m "feat: implement user authentication system"
git push origin feature/user-authentication
```

#### Agent Development Workflow

```bash
# For Agent 1 development
python -m src.agents.agent1.test_conversation
python test_agent1_system.py

# For Agent 2 development  
python -m src.agents.agent2.test_implementation
python test_enhanced_agent.py

# For memory system development
python test_dual_memory_integration.py
python -m src.memory.test_sync
```

### 2. Testing Strategy

#### Unit Tests

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_conversation.py -v

# Run with coverage
pytest tests/unit/ --cov=src/agents/agent1/ --cov-report=html
```

#### Integration Tests

```bash
# Run integration test suite
pytest tests/integration/ -v

# Test dual-agent integration
python test_dual_memory_integration.py

# Test full conversation workflow
python test_discussion.py
```

#### End-to-End Tests

```bash
# Run complete E2E test suite
pytest tests/e2e/ -v --slow

# Test CLI interface
python test_cli_integration.py

# Test memory system integration
python test_centralized_config.py
```

### 3. Debugging and Development Tools

#### Debug Mode

```bash
# Enable debug logging
export NEURODOCK_DEBUG=true
export NEURODOCK_LOG_LEVEL=DEBUG

# Run with debug mode
python -m src.cli.main --debug chat "Debug conversation"
```

#### Memory System Debugging

```bash
# Inspect memory state
python -m src.memory.inspect --session session_id

# Monitor memory operations
python -m src.memory.monitor --follow

# Debug synchronization issues
python -m src.memory.debug_sync --session session_id
```

#### Agent Debugging

```bash
# Debug Agent 1 conversations
python -m src.agents.agent1.debug --conversation-id conv_id

# Debug Agent 2 implementations
python -m src.agents.agent2.debug --task-id task_id

# Monitor agent communication
python -m src.agents.monitor --dual-mode
```

## Contributing Guidelines

### Code Style and Standards

#### Python Code Standards

We follow PEP 8 with some modifications:

```python
# Use type hints
def process_conversation(message: str, context: Optional[Dict]) -> ConversationResult:
    """Process a conversation message with context."""
    pass

# Use dataclasses for models
@dataclass
class ConversationTurn:
    user_message: str
    agent_response: str
    timestamp: datetime
    metadata: Optional[Dict] = None

# Use async/await for I/O operations
async def store_conversation(session_id: str, turn: ConversationTurn) -> None:
    """Store conversation turn in memory system."""
    async with memory_manager.transaction():
        await memory_manager.store_turn(session_id, turn)
```

#### Code Quality Tools

```bash
# Format code with black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Type checking with mypy
mypy src/

# Linting with flake8
flake8 src/ tests/

# Security analysis with bandit
bandit -r src/
```

#### Pre-commit Hooks

Install pre-commit hooks to ensure code quality:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### Documentation Standards

#### Code Documentation

```python
class ConversationAgent:
    """Agent 1: Conversational interface for NeuroDock.
    
    This agent handles user interactions, requirements gathering,
    and coordination with Agent 2 for implementation tasks.
    
    Attributes:
        memory_manager: Interface to the memory system
        llm_client: LLM client for conversation processing
        config: Agent configuration settings
        
    Example:
        >>> agent = ConversationAgent(memory_manager, llm_client, config)
        >>> response = await agent.process_message("Create user auth")
        >>> print(response.content)
    """
    
    def process_message(self, message: str, context: Optional[Dict] = None) -> ConversationResponse:
        """Process a user message and generate response.
        
        Args:
            message: User input message
            context: Optional conversation context
            
        Returns:
            ConversationResponse with agent reply and metadata
            
        Raises:
            ConversationError: If message processing fails
            MemoryError: If context retrieval fails
        """
        pass
```

#### API Documentation

Use OpenAPI/Swagger for REST API documentation:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict] = None

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Start or continue a conversation with Agent 1.
    
    - **message**: User input message
    - **session_id**: Optional session to continue
    - **context**: Optional additional context
    
    Returns conversation response with agent reply.
    """
    pass
```

### Testing Guidelines

#### Test Structure

```python
# tests/unit/test_conversation.py
import pytest
from unittest.mock import AsyncMock, Mock

from src.agents.agent1.conversation import ConversationAgent
from src.memory.core_manager import MemoryManager

class TestConversationAgent:
    """Test suite for ConversationAgent."""
    
    @pytest.fixture
    async def agent(self):
        """Create test agent instance."""
        memory_manager = AsyncMock(spec=MemoryManager)
        llm_client = Mock()
        config = {"model": "gpt-4", "temperature": 0.1}
        return ConversationAgent(memory_manager, llm_client, config)
    
    async def test_process_simple_message(self, agent):
        """Test processing a simple user message."""
        # Arrange
        message = "Hello, create a user authentication system"
        
        # Act
        response = await agent.process_message(message)
        
        # Assert
        assert response.content is not None
        assert "authentication" in response.content.lower()
        assert response.session_id is not None
    
    async def test_process_message_with_context(self, agent):
        """Test processing message with conversation context."""
        # Arrange
        message = "Add OAuth support"
        context = {
            "previous_requirements": ["basic auth", "user registration"],
            "tech_stack": ["Python", "FastAPI"]
        }
        
        # Act  
        response = await agent.process_message(message, context)
        
        # Assert
        assert "oauth" in response.content.lower()
        assert response.agent2_tasks is not None
```

#### Integration Test Patterns

```python
# tests/integration/test_dual_agent.py
import pytest
from src.agents.agent1.conversation import ConversationAgent
from src.agents.agent2.implementation import ImplementationAgent
from src.memory.core_manager import MemoryManager

@pytest.mark.integration
class TestDualAgentWorkflow:
    """Integration tests for dual-agent workflows."""
    
    @pytest.fixture
    async def system(self):
        """Set up complete system for testing."""
        memory_manager = await MemoryManager.create()
        agent1 = ConversationAgent(memory_manager)
        agent2 = ImplementationAgent(memory_manager)
        return {"memory": memory_manager, "agent1": agent1, "agent2": agent2}
    
    async def test_complete_feature_workflow(self, system):
        """Test complete feature development workflow."""
        # User conversation with Agent 1
        response1 = await system["agent1"].process_message(
            "Create a user registration endpoint with email validation"
        )
        
        # Agent 1 should delegate to Agent 2
        assert len(response1.agent2_tasks) > 0
        
        # Agent 2 executes implementation
        task = response1.agent2_tasks[0]
        result = await system["agent2"].execute_task(task)
        
        # Verify implementation result
        assert result.status == "completed"
        assert len(result.files_changed) > 0
        assert result.tests_passed > 0
        
        # Verify memory synchronization
        context = await system["memory"].get_context(response1.session_id)
        assert len(context["implementations"]) > 0
```

### Pull Request Process

#### 1. Before Creating PR

```bash
# Ensure all tests pass
pytest tests/ -v

# Run full integration test
python test_dual_memory_integration.py

# Check code quality
pre-commit run --all-files

# Update documentation if needed
# Add entry to CHANGELOG.md
```

#### 2. PR Template

```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Agent 1 conversation testing
- [ ] Agent 2 implementation testing

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
```

#### 3. Review Process

- **Code Review**: At least one maintainer review required
- **Testing**: All automated tests must pass
- **Documentation**: Documentation must be updated for new features
- **Integration**: Manual integration testing with both agents

## Advanced Development

### Custom Agent Development

#### Creating Custom Agent Extensions

```python
# src/agents/custom/custom_agent.py
from src.agents.base import BaseAgent
from src.memory.interfaces import MemoryInterface

class CustomAgent(BaseAgent):
    """Custom agent for specialized tasks."""
    
    def __init__(self, memory_interface: MemoryInterface, config: Dict):
        super().__init__(memory_interface, config)
        self.specialty = config.get("specialty", "general")
    
    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """Process custom agent request."""
        # Custom logic here
        result = await self.execute_custom_logic(request)
        
        # Store result in memory
        await self.memory.store_result(request.session_id, result)
        
        return AgentResponse(content=result.content, metadata=result.metadata)
    
    async def execute_custom_logic(self, request: AgentRequest) -> CustomResult:
        """Implement custom agent logic."""
        # Your custom implementation
        pass
```

#### Registering Custom Agents

```python
# src/agents/registry.py
from src.agents.custom.custom_agent import CustomAgent

# Register agent
agent_registry.register("custom", CustomAgent)

# Use in configuration
config = {
    "agents": {
        "agent1": "conversational",
        "agent2": "implementation", 
        "agent3": "custom"
    }
}
```

### Memory System Extensions

#### Custom Memory Stores

```python
# src/memory/stores/custom_store.py
from src.memory.base_store import BaseMemoryStore

class CustomMemoryStore(BaseMemoryStore):
    """Custom memory store implementation."""
    
    async def store(self, key: str, data: Any, metadata: Dict) -> str:
        """Store data with custom logic."""
        # Custom storage implementation
        pass
    
    async def retrieve(self, key: str, filters: Optional[Dict] = None) -> List[Any]:
        """Retrieve data with custom logic."""
        # Custom retrieval implementation
        pass
    
    async def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search with custom algorithm."""
        # Custom search implementation
        pass
```

### Performance Optimization

#### Profiling and Monitoring

```python
# Development profiling
import cProfile
import pstats

def profile_conversation():
    """Profile conversation processing."""
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run conversation
    agent = ConversationAgent(memory_manager, llm_client, config)
    asyncio.run(agent.process_message("Complex message"))
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative').print_stats(20)

# Memory usage monitoring
import tracemalloc

tracemalloc.start()

# Run code to monitor
# ...

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")
tracemalloc.stop()
```

#### Performance Testing

```python
# tests/performance/test_conversation_performance.py
import pytest
import time
from concurrent.futures import ThreadPoolExecutor

class TestPerformance:
    """Performance tests for NeuroDock."""
    
    @pytest.mark.performance
    async def test_conversation_latency(self, agent):
        """Test conversation response latency."""
        start_time = time.time()
        
        response = await agent.process_message("Create a simple API endpoint")
        
        end_time = time.time()
        latency = end_time - start_time
        
        # Assert reasonable response time
        assert latency < 5.0, f"Conversation latency too high: {latency}s"
    
    @pytest.mark.performance  
    async def test_concurrent_conversations(self, agent):
        """Test handling multiple concurrent conversations."""
        def run_conversation(message_id):
            return asyncio.run(agent.process_message(f"Task {message_id}"))
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(run_conversation, i) 
                for i in range(10)
            ]
            
            results = [future.result() for future in futures]
            
        # All conversations should complete successfully
        assert all(result.content for result in results)
```

## Deployment for Development

### Local Development Infrastructure

```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: neurodock_dev
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
  
  qdrant:
    image: qdrant/qdrant:v1.7.0
    ports:
      - "6333:6333"
    volumes:
      - qdrant_dev_data:/qdrant/storage
  
  neo4j:
    image: neo4j:5.15
    environment:
      NEO4J_AUTH: neo4j/dev_password
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_dev_data:/data
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_dev_data:/data

volumes:
  postgres_dev_data:
  qdrant_dev_data:
  neo4j_dev_data:
  redis_dev_data:
```

### Development Scripts

```bash
# scripts/dev-setup.sh
#!/bin/bash
set -e

echo "Setting up NeuroDock development environment..."

# Start development infrastructure
docker-compose -f docker-compose.dev.yml up -d

# Wait for databases to be ready
echo "Waiting for databases to be ready..."
sleep 10

# Run migrations
python -m src.db.migrate

# Install pre-commit hooks
pre-commit install

# Run initial tests
pytest tests/unit/ -v

echo "Development environment ready!"
```

```bash
# scripts/dev-test.sh
#!/bin/bash
set -e

echo "Running development test suite..."

# Unit tests
pytest tests/unit/ -v --cov=src/

# Integration tests  
pytest tests/integration/ -v

# Agent-specific tests
python test_agent1_system.py
python test_enhanced_agent.py
python test_dual_memory_integration.py

echo "All tests completed!"
```

## Troubleshooting Development Issues

### Common Development Problems

#### 1. Database Connection Issues

```bash
# Check database status
docker-compose -f docker-compose.dev.yml ps

# View database logs
docker-compose -f docker-compose.dev.yml logs postgres

# Reset database
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d
```

#### 2. Memory System Synchronization

```bash
# Check memory system health
python -m src.memory.diagnostics --health

# Debug synchronization
python -m src.memory.debug_sync --verbose

# Reset memory state
python -m src.memory.reset --dev-mode --confirm
```

#### 3. Agent Communication Issues

```bash
# Test Agent 1 functionality
python test_agent1_system.py --debug

# Test Agent 2 functionality  
python test_enhanced_agent.py --debug

# Test dual-agent communication
python test_discussion.py --verbose
```

### Development Tools and Utilities

#### Debugging Tools

```python
# src/dev_tools/debug_conversation.py
"""Development tool for debugging conversations."""

async def debug_conversation_flow(session_id: str):
    """Debug a specific conversation flow."""
    memory = MemoryManager()
    
    # Get conversation history
    history = await memory.get_conversation_history(session_id)
    
    # Analyze conversation flow
    for turn in history:
        print(f"Turn {turn.id}:")
        print(f"  User: {turn.user_message}")
        print(f"  Agent: {turn.agent_response}")
        print(f"  Agent 2 Tasks: {len(turn.agent2_tasks)}")
        print(f"  Context: {turn.context}")
        print()

if __name__ == "__main__":
    import sys
    session_id = sys.argv[1] if len(sys.argv) > 1 else None
    if session_id:
        asyncio.run(debug_conversation_flow(session_id))
```

#### Development CLI Extensions

```python
# src/dev_tools/dev_cli.py
"""Development CLI extensions."""

import click
from src.cli.main import cli

@cli.group()
def dev():
    """Development tools and utilities."""
    pass

@dev.command()
@click.argument('session_id')
def debug_session(session_id):
    """Debug a conversation session."""
    from src.dev_tools.debug_conversation import debug_conversation_flow
    asyncio.run(debug_conversation_flow(session_id))

@dev.command()  
def reset_dev_data():
    """Reset development data."""
    click.confirm('This will delete all development data. Continue?', abort=True)
    # Reset logic here
    click.echo('Development data reset complete.')
```

This comprehensive development guide provides everything needed to contribute to NeuroDock, from initial setup through advanced development patterns. The focus is on maintaining code quality, comprehensive testing, and smooth collaboration between the dual-agent system components.
