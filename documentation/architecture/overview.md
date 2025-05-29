# NeuroDock Architecture Overview

## Enhanced System Architecture *(Updated)*

NeuroDock implements a sophisticated dual-agent architecture with advanced memory systems and enhanced iterative discussion capabilities for intelligent, conversation-driven development.

### Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    Enhanced NeuroDock System                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │  Developer  │◄──►│  Navigator  │◄──►│  NeuroDock  │         │
│  │ (Provides   │    │(Facilitates │    │ (Enhanced   │         │
│  │  Answers)   │    │ Iteration)  │    │Discussion)  │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                            │                   │                │
│                            ▼                   ▼                │
│                  ┌─────────────────────────────────┐            │
│                  │      Enhanced Memory System     │            │
│                  │ • Discussion State Management   │            │
│                  │ • Conversation History         │            │
│                  │ • Vector Memory (Qdrant)      │            │
│                  │ • Relational Storage          │            │
│                  └─────────────────────────────────┘            │
│                            │                                    │
│                            ▼                                    │
│                  ┌─────────────────┐                           │
│                  │   PostgreSQL    │                           │
│                  │ • State Storage │                           │
│                  │ • Audit Trail   │                           │
│                  │ • Persistence   │                           │
│                  └─────────────────┘                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Enhanced Discussion System *(New Feature)*

### Iterative Conversation Engine

**Purpose**: Enables complex, multi-round requirement gathering through intelligent iteration

**Key Features**:
- **Unlimited Iterations**: Support for complex enterprise-level requirement gathering
- **State Persistence**: Complete conversation history preserved across sessions
- **Completeness Analysis**: AI-powered analysis determines when more questions are needed
- **Context-Aware Questions**: Follow-up questions generated based on previous answers
- **Navigator Integration**: Seamless handoff between human and AI components

**Implementation**: `src/neurodock/discussion.py`

### Discussion State Flow

```
┌─────────────┐   ┌─────────────────┐   ┌─────────────────┐
│    new      │──▶│ questions_pending│──▶│ awaiting_answers│
└─────────────┘   └─────────────────┘   └─────────────────┘
                                                  │
                                                  ▼
┌─────────────────┐                    ┌─────────────────┐
│ ready_for_planning│◄──────────────────│ (iteration loop)│
└─────────────────┘                    └─────────────────┘
```

## Agent Architecture

### Navigator (Enhanced Conversation Facilitator) *(Updated)*

**Purpose**: Guides developers through structured iterative conversations with enhanced discussion capabilities

**Key Responsibilities**:
- Facilitate multi-round requirement gathering conversations
- Monitor discussion state and completion progress
- Collect developer answers and provide them to the system
- Interpret system analysis and continue iteration as needed
- Store all conversation context in enhanced memory systems
- Provide clear guidance on next actions required

**Enhanced Capabilities**:
- **State Monitoring**: Track discussion progress and completion percentage
- **Answer Collection**: Gather comprehensive developer responses
- **Iteration Management**: Facilitate unlimited Q&A rounds until complete
- **Context Preservation**: Maintain full conversation history across sessions

**Implementation**: `src/neurodock/conversational_agent.py`

**Navigator Commands**:
```bash
nd discuss-status     # Check current discussion state and next action
nd discuss-answer     # Provide developer answers to continue iteration
nd memory --search="discussion"  # Review conversation history
```
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

### NeuroDock (Enhanced Task Executor) *(Updated)*

**Purpose**: Execute technical development tasks with enhanced iterative discussion capabilities

**Key Characteristics**:
- Can be any LLM (Claude, OpenAI, Ollama, local models)
- Enhanced discussion engine with multi-round conversation support
- Receives comprehensive context from iterative requirement gathering
- Provides intelligent completeness analysis and follow-up questions
- Works through enhanced CLI commands with state management

**Enhanced Capabilities**:
- **Iterative Question Generation**: Context-aware clarifying questions
- **Completeness Analysis**: AI-powered analysis of requirement gathering progress
- **Follow-up Intelligence**: Generate targeted questions based on previous answers
- **State Management**: Track and persist conversation state across sessions

**Context Sources**:
- Complete iterative conversation history
- Discussion state and completion analysis
- Project requirements gathered through multiple iterations
- Technical decisions and constraints clarified through Q&A
- Enhanced memory system with conversation metadata

## Enhanced Memory System Architecture *(Updated)*

### Triple Storage Strategy *(Enhanced)*

**Qdrant (Vector Storage)**:
- Semantic search capabilities across all conversation iterations
- Discussion content indexing with temporal context
- Contextual similarity matching for follow-up questions
- Cross-conversation correlation and learning

**PostgreSQL (Enhanced Relational Storage)**:
- **Discussion State Management**: Persistent conversation states across sessions
- **Iteration Tracking**: Complete audit trail of all Q&A rounds
- **Conversation History**: Structured storage of questions, answers, and metadata
- **Completeness Metrics**: Progress tracking and analysis results
- Task management with enhanced context
- Project metadata with conversation insights

**Memory Integration Features**:
- **Temporal Context**: Track conversation progression over time
- **State Persistence**: Resume interrupted discussions exactly where left off
- **Audit Trail**: Complete record of all conversation iterations for compliance
- **Context Search**: Intelligent search across all discussion history

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
