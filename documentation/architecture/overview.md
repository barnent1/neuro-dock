# NeuroDock Architecture Overview

## System Architecture

NeuroDock implements a sophisticated dual-agent architecture with advanced memory systems for intelligent, conversation-driven development.

### Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         NeuroDock System                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │  Developer  │◄──►│  Navigator  │◄──►│  NeuroDock  │         │
│  │    (Chat)   │    │(Conversation│    │  (Any LLM)  │         │
│  │             │    │Facilitator) │    │             │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                            │                                    │
│                            ▼                                    │
│                  ┌─────────────────┐                           │
│                  │  Memory System  │                           │
│                  │ (Qdrant+Neo4J)  │                           │
│                  └─────────────────┘                           │
│                            │                                    │
│                            ▼                                    │
│                  ┌─────────────────┐                           │
│                  │   PostgreSQL    │                           │
│                  │    Database     │                           │
│                  └─────────────────┘                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Agent Architecture

### Navigator (Conversational Facilitator)

**Purpose**: Guides developers through structured Agile conversations

**Key Responsibilities**:
- Read and understand system capabilities via `.neuro-dock.md`
- Facilitate structured conversations following Agile methodology
- Parse developer inputs and maintain conversation state
- Execute keyword-triggered commands to engage NeuroDock
- Relay NeuroDock results back to developer
- Store all conversation context in memory systems

**Implementation**: `src/neurodock/conversational_agent.py`

**Conversation Flow**:
1. **Initiation**: Introduce system and gather project vision
2. **Requirements**: Facilitate detailed requirements gathering
3. **Planning**: Guide sprint planning and task breakdown
4. **Design**: Discuss technical architecture
5. **Development**: Oversee iterative development cycles
6. **Testing**: Coordinate testing and quality assurance
7. **Review**: Facilitate code review processes
8. **Deployment**: Guide deployment procedures
9. **Retrospective**: Conduct project retrospectives

**Keyword Triggers**:
- `"proceed to requirements"` → Execute `nd discuss`
- `"proceed to planning"` → Execute `nd sprint-plan`
- `"proceed to design"` → Execute `nd design`
- `"proceed to development"` → Execute `nd develop`
- `"proceed to testing"` → Execute `nd test`
- `"proceed to review"` → Execute `nd review`
- `"proceed to deployment"` → Execute `nd deploy`
- `"proceed to retrospective"` → Execute `nd retrospective`

### NeuroDock (Task Executor)

**Purpose**: Execute technical development tasks with rich context

**Key Characteristics**:
- Can be any LLM (Claude, OpenAI, Ollama, local models)
- Receives rich context from Navigator conversations
- Works through CLI commands with contextual reminders
- Provides feedback through the reminder system

**Context Sources**:
- Full conversation history from Navigator
- Project requirements and constraints
- Previous task completion history
- Technical decisions and preferences
- Memory system insights

## Memory System Architecture

### Dual Storage Strategy

**Qdrant (Vector Storage)**:
- Semantic search capabilities
- Conversation content indexing
- Contextual similarity matching
- Cross-conversation correlation

**Neo4J (Graph Storage)**:
- Relationship mapping
- Decision dependency tracking
- Project structure representation
- Agent interaction patterns

**PostgreSQL (Relational Storage)**:
- Task management
- Project metadata
- Command history
- Structured data relationships

### Memory Integration Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Conversation│───►│   Memory    │───►│  Agent 2    │
│   Context   │    │ Processing  │    │ Reminders   │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Qdrant    │    │   Neo4J     │    │ PostgreSQL  │
│  (Vector)   │    │  (Graph)    │    │(Relational) │
└─────────────┘    └─────────────┘    └─────────────┘
```

## CLI Architecture

### Command Categories

**Conversational Commands** (Navigator):
- `nd begin` - Start Navigator conversation
- `nd continue` - Resume conversation
- `nd conversation-status` - View conversation state
- `nd explain` - System explanations
- `nd guide-me` - Process guidance

**Development Commands** (NeuroDock):
- `nd init` - Project initialization
- `nd discuss` - Requirements gathering
- `nd sprint-plan` - Task breakdown
- `nd design` - Architecture design
- `nd develop` - Code implementation
- `nd test` - Testing execution
- `nd review` - Code review
- `nd deploy` - Deployment
- `nd retrospective` - Project retrospective

**Utility Commands**:
- `nd status` - Project overview
- `nd memory` - Memory management
- `nd context` - Context viewing
- `nd reminders` - Agent 2 reminders

### Command Flow Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│     CLI     │───►│   Memory    │───►│  Agent 2    │
│  Commands   │    │ Integration │    │  Context    │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Database   │    │ Reminders   │    │   LLM API   │
│ Operations  │    │   System    │    │Integration  │
└─────────────┘    └─────────────┘    └─────────────┘
```

## Data Flow

### Conversation to Execution Flow

1. **Developer Input** → Agent 1 conversation interface
2. **Agent 1 Processing** → Structured conversation management
3. **Context Storage** → Memory systems (Qdrant + Neo4J + PostgreSQL)
4. **Keyword Detection** → Trigger analysis and command preparation
5. **Command Execution** → Agent 2 engagement via CLI
6. **Context Injection** → Rich context provided to Agent 2
7. **Task Execution** → Agent 2 performs technical work
8. **Result Integration** → Outcomes stored in memory systems
9. **Feedback Loop** → Results relayed back through Agent 1

### Memory Correlation Flow

```
Conversation ──┐
               ├─► Memory Processing ──┐
Requirements ──┘                        ├─► Context Generation ──► Agent 2
               ┌─► Relationship         │
Decisions ────┘     Analysis ──────────┘
```

## Integration Points

### LLM Provider Integration

NeuroDock supports multiple LLM providers through a unified interface:

- **OpenAI**: GPT-3.5, GPT-4, GPT-4-turbo
- **Anthropic**: Claude-3 (Haiku, Sonnet, Opus)
- **Local Models**: Ollama, LLaMA, Mistral
- **Custom Endpoints**: Any OpenAI-compatible API

### Database Integration

**PostgreSQL Backend**:
- Primary data storage
- ACID compliance
- Complex query support
- Production scalability

**Vector Database (Qdrant)**:
- Semantic search
- Embedding storage
- Similarity matching
- Fast retrieval

**Graph Database (Neo4J)**:
- Relationship modeling
- Path analysis
- Complex associations
- Decision tracking

## Scalability Considerations

### Horizontal Scaling

- **Database Sharding**: Project-based data partitioning
- **Memory Replication**: Multi-node vector/graph storage
- **Load Balancing**: Distributed CLI processing
- **Cache Layers**: Intelligent context caching

### Performance Optimization

- **Lazy Loading**: On-demand memory retrieval
- **Context Compression**: Intelligent summarization
- **Query Optimization**: Efficient database operations
- **Parallel Processing**: Concurrent task execution

## Security Architecture

### Data Protection

- **Encryption at Rest**: Database encryption
- **Secure Communication**: TLS for all API calls
- **Access Control**: Role-based permissions
- **Audit Logging**: Comprehensive activity tracking

### Privacy Considerations

- **Local Processing**: Option for fully local deployment
- **Data Anonymization**: Sensitive information protection
- **Secure Storage**: Encrypted memory systems
- **Configurable Retention**: Flexible data lifecycle management

This architecture enables NeuroDock to provide intelligent, context-aware development assistance while maintaining scalability, security, and flexibility for various deployment scenarios.
