# Agent 2 Integration Guide

## Overview

Agent 2 is NeuroDock's specialized integration and automation agent that works alongside Agent 1 to handle technical implementation, testing, and system integration tasks.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐
│     Agent 1     │    │     Agent 2     │
│  (Conversation) │◄──►│ (Implementation)│
│                 │    │                 │
│ • User Dialogue │    │ • Code Execution│
│ • Requirements  │    │ • Testing       │
│ • Planning      │    │ • Integration   │
│ • Coordination  │    │ • Validation    │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────────────────┘
                    │
         ┌─────────────────┐
         │  Shared Memory  │
         │    System       │
         │                 │
         │ • Conversation  │
         │ • Context       │
         │ • Results       │
         └─────────────────┘
```

## Key Features

### 1. **Automated Implementation**
- Executes code changes based on Agent 1's requirements
- Handles file creation, modification, and deletion
- Manages dependency installation and configuration

### 2. **Testing Integration**
- Runs automated tests after implementations
- Validates system functionality
- Reports results back to shared memory

### 3. **System Integration**
- Coordinates with external systems
- Manages database connections and migrations
- Handles API integrations

### 4. **Quality Assurance**
- Code validation and linting
- Performance monitoring
- Error handling and recovery

## Setup and Configuration

### Prerequisites

Before setting up Agent 2, ensure:

1. **Agent 1 is configured** and functional
2. **Shared memory system** is operational
3. **Required dependencies** are installed:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

Agent 2 shares the same environment configuration as Agent 1:

```bash
# Copy environment template
cp .env.example .env

# Configure required variables
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
DATABASE_URL=your_database_connection
QDRANT_URL=your_qdrant_instance
NEO4J_URI=your_neo4j_connection
```

### Integration Points

Agent 2 integrates through several mechanisms:

1. **Shared Memory Access**
   - Reads conversation context from Agent 1
   - Writes implementation results back to memory
   - Maintains synchronization between agents

2. **CLI Interface**
   ```bash
   # Agent 2 can be invoked directly
   python -m src.agent2.main --task implementation --context-id 12345
   
   # Or through Agent 1 coordination
   # Agent 1 automatically delegates to Agent 2 when needed
   ```

3. **File System Integration**
   - Monitors project directory for changes
   - Executes file operations as directed
   - Maintains project structure integrity

## Usage Patterns

### 1. **Automatic Delegation**

Agent 1 automatically delegates to Agent 2 for:
- Code implementation tasks
- Testing and validation
- System configuration changes
- Database operations

Example conversation flow:
```
User: "Implement the user authentication system"
Agent 1: "I'll analyze the requirements and coordinate implementation"
         → Delegates to Agent 2
Agent 2: "Implementing authentication system..."
         → Executes code changes
         → Runs tests
         → Reports back to Agent 1
Agent 1: "Authentication system implemented successfully. Here's what was done..."
```

### 2. **Direct Invocation**

For advanced users, Agent 2 can be invoked directly:

```bash
# Execute specific implementation
python -m src.agent2.main --implement feature_spec.json

# Run validation suite
python -m src.agent2.main --validate --target user_auth

# Integrate external system
python -m src.agent2.main --integrate --system payment_gateway
```

### 3. **Batch Processing**

Agent 2 can handle multiple tasks in sequence:

```bash
python -m src.agent2.main --batch tasks.json
```

Where `tasks.json` contains:
```json
{
  "tasks": [
    {
      "type": "implement",
      "spec": "feature_requirements.json",
      "priority": "high"
    },
    {
      "type": "test",
      "target": "implemented_features",
      "coverage": "full"
    },
    {
      "type": "integrate",
      "systems": ["database", "cache"],
      "validate": true
    }
  ]
}
```

## Memory Integration

### Shared Context

Agent 2 accesses and updates shared memory:

```python
# Read context from Agent 1
conversation_context = memory_system.get_conversation_context(session_id)

# Execute implementation
result = implement_feature(conversation_context.requirements)

# Update shared memory
memory_system.store_implementation_result(session_id, result)
```

### Synchronization

The agents maintain synchronization through:

1. **Event-based messaging**
2. **Shared state management**
3. **Result validation**
4. **Error propagation**

## Testing and Validation

### Automated Testing

Agent 2 includes comprehensive testing capabilities:

```bash
# Run Agent 2 test suite
python -m pytest tests/agent2/

# Integration tests
python -m pytest tests/integration/

# End-to-end workflow tests
python test_dual_agent_workflow.py
```

### Validation Workflows

1. **Pre-implementation validation**
   - Requirements analysis
   - Dependency checks
   - Resource availability

2. **Implementation validation**
   - Code syntax and style
   - Functional testing
   - Integration testing

3. **Post-implementation validation**
   - System health checks
   - Performance validation
   - User acceptance criteria

## Troubleshooting

### Common Issues

1. **Agent 2 not responding**
   ```bash
   # Check Agent 2 status
   python -m src.agent2.main --status
   
   # Restart Agent 2
   python -m src.agent2.main --restart
   ```

2. **Memory synchronization errors**
   ```bash
   # Validate memory system
   python test_dual_memory_integration.py
   
   # Reset shared state if needed
   python -m src.memory.reset --confirm
   ```

3. **Implementation failures**
   ```bash
   # Check implementation logs
   tail -f logs/agent2_implementation.log
   
   # Rollback failed implementation
   python -m src.agent2.main --rollback --session SESSION_ID
   ```

### Debugging

Enable detailed logging:

```bash
export NEURODOCK_LOG_LEVEL=DEBUG
export AGENT2_VERBOSE=true
```

Monitor Agent 2 activity:

```bash
# Real-time monitoring
python -m src.agent2.monitor --follow

# Implementation trace
python -m src.agent2.main --trace --task TASK_ID
```

## Advanced Configuration

### Custom Implementation Handlers

Agent 2 supports custom implementation handlers:

```python
# src/agent2/handlers/custom_handler.py
from src.agent2.base_handler import BaseImplementationHandler

class CustomFeatureHandler(BaseImplementationHandler):
    def can_handle(self, requirement):
        return requirement.type == "custom_feature"
    
    def implement(self, requirement, context):
        # Custom implementation logic
        pass
```

### Integration Extensions

Extend Agent 2 with custom integrations:

```python
# src/agent2/integrations/custom_integration.py
from src.agent2.base_integration import BaseIntegration

class CustomSystemIntegration(BaseIntegration):
    def connect(self):
        # Custom connection logic
        pass
    
    def sync_data(self):
        # Custom synchronization
        pass
```

## Performance Optimization

### Resource Management

Agent 2 includes resource management features:

```python
# Configure resource limits
AGENT2_MAX_MEMORY=2GB
AGENT2_MAX_CPU_PERCENT=80
AGENT2_TIMEOUT_SECONDS=300
```

### Parallel Processing

Enable parallel processing for multiple tasks:

```python
# Enable parallel implementation
AGENT2_PARALLEL_TASKS=true
AGENT2_MAX_WORKERS=4
```

## Security Considerations

### Sandboxing

Agent 2 operations can be sandboxed:

```bash
# Enable sandboxed execution
export AGENT2_SANDBOX=true
export AGENT2_ALLOWED_PATHS="/project,/tmp"
```

### Access Control

Configure access permissions:

```python
# Restrict Agent 2 capabilities
AGENT2_ALLOWED_OPERATIONS=["file_write", "database_read", "test_execute"]
AGENT2_FORBIDDEN_PATHS=["/system", "/etc"]
```

## Integration Examples

### Example 1: Database Schema Update

```python
# Agent 1 conversation
user_input = "Add user profile table with social media links"

# Agent 2 implementation
schema_update = {
    "table": "user_profiles",
    "columns": [
        {"name": "user_id", "type": "UUID", "references": "users.id"},
        {"name": "twitter_handle", "type": "VARCHAR(50)"},
        {"name": "linkedin_url", "type": "TEXT"},
        {"name": "github_username", "type": "VARCHAR(100)"}
    ]
}

# Execution result
result = agent2.implement_database_schema(schema_update)
```

### Example 2: API Integration

```python
# Agent 1 requirement
requirement = "Integrate with Stripe payment processing"

# Agent 2 implementation
integration_spec = {
    "service": "stripe",
    "endpoints": ["payment_intents", "customers", "subscriptions"],
    "webhook_handlers": ["payment.succeeded", "customer.created"]
}

result = agent2.implement_api_integration(integration_spec)
```

## Support and Documentation

For additional support:

1. **Check the logs**: `logs/agent2_*.log`
2. **Run diagnostics**: `python -m src.agent2.diagnostics`
3. **Review memory state**: `python -m src.memory.inspect`
4. **Validate configuration**: `python test_agent2_config.py`

## Next Steps

After setting up Agent 2:

1. **Test the dual-agent workflow**
2. **Configure custom handlers** for your use case
3. **Set up monitoring and alerting**
4. **Review security settings**
5. **Optimize performance parameters**

See the [Development Guide](../development/getting-started.md) for advanced usage patterns and the [API Reference](../api/commands.md) for detailed command documentation.
