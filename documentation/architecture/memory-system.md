# Memory System Architecture

## Overview

NeuroDock's memory system is the central nervous system that enables seamless communication and context sharing between Navigator (conversation) and NeuroDock (implementation). It provides persistent storage, real-time synchronization, and intelligent context management.

## Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Memory System Core                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ PostgreSQL  │  │   Qdrant    │  │   Neo4J     │         │
│  │ (Relational)│  │ (Vector DB) │  │ (Graph DB)  │         │
│  │             │  │             │  │             │         │
│  │ • Sessions  │  │ • Embeddings│  │ • Relations │         │
│  │ • Messages  │  │ • Similarity│  │ • Workflows │         │
│  │ • Results   │  │ • Context   │  │ • Dependencies│       │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
    ┌─────────────────────────┼─────────────────────────┐
    │                         │                         │
┌───▼───┐              ┌─────▼──────┐           ┌──────▼──────┐
│Navigator│              │ Memory API │           │   NeuroDock   │
│       │◄────────────►│            │◄─────────►│             │
│ Chat  │              │ • Store    │           │ Implement   │
│ Plan  │              │ • Retrieve │           │ Test        │
│ Guide │              │ • Search   │           │ Validate    │
└───────┘              │ • Sync     │           └─────────────┘
                       └────────────┘
```

## Database Layer Architecture

### 1. PostgreSQL - Structured Data

**Purpose**: Primary relational database for structured conversation and session data

**Schema Design**:
```sql
-- Conversation Sessions
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    project_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB
);

-- Conversation Messages
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    agent_type VARCHAR(20) NOT NULL, -- 'navigator' or 'neurodock'
    role VARCHAR(20) NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB,
    embedding_id VARCHAR(255) -- Reference to Qdrant vector
);

-- Implementation Results
CREATE TABLE implementation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    neurodock_task_id VARCHAR(255) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    result_data JSONB,
    files_changed TEXT[],
    tests_run JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Context Snapshots
CREATE TABLE context_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    snapshot_type VARCHAR(50) NOT NULL,
    context_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Indexes for Performance**:
```sql
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_created_at ON sessions(created_at);
CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp);
CREATE INDEX idx_implementation_results_session_id ON implementation_results(session_id);
CREATE INDEX idx_context_snapshots_session_id ON context_snapshots(session_id);
```

### 2. Qdrant - Vector Database

**Purpose**: Semantic search and context similarity matching

**Collection Structure**:
```python
from qdrant_client.http import models

# Conversation Context Collection
conversation_collection = {
    "collection_name": "conversation_context",
    "vectors_config": models.VectorParams(
        size=1536,  # OpenAI ada-002 embedding size
        distance=models.Distance.COSINE
    ),
    "payload_schema": {
        "session_id": "keyword",
        "message_id": "keyword", 
        "agent_type": "keyword",
        "content_type": "keyword",  # 'message', 'requirement', 'result'
        "timestamp": "datetime",
        "content_preview": "text"
    }
}

# Implementation Knowledge Collection
implementation_collection = {
    "collection_name": "implementation_knowledge",
    "vectors_config": models.VectorParams(
        size=1536,
        distance=models.Distance.COSINE
    ),
    "payload_schema": {
        "result_id": "keyword",
        "task_type": "keyword",
        "technologies": ["keyword"],
        "files_involved": ["keyword"],
        "success_patterns": "text",
        "error_patterns": "text"
    }
}
```

**Vector Operations**:
```python
# Store conversation embedding
def store_conversation_vector(content, metadata):
    embedding = openai_client.embeddings.create(
        input=content,
        model="text-embedding-ada-002"
    ).data[0].embedding
    
    qdrant_client.upsert(
        collection_name="conversation_context",
        points=[models.PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload=metadata
        )]
    )

# Search similar context
def find_similar_context(query, limit=5):
    query_embedding = openai_client.embeddings.create(
        input=query,
        model="text-embedding-ada-002"
    ).data[0].embedding
    
    results = qdrant_client.search(
        collection_name="conversation_context",
        query_vector=query_embedding,
        limit=limit,
        score_threshold=0.7
    )
    return results
```

### 3. Neo4J - Graph Database

**Purpose**: Relationship mapping and workflow dependencies

**Node Types**:
```cypher
// Session Nodes
CREATE (s:Session {
    id: "session_uuid",
    user_id: "user_identifier",
    project_name: "project_name",
    created_at: datetime(),
    status: "active"
})

// Message Nodes
CREATE (m:Message {
    id: "message_uuid",
    content: "message_content",
    role: "user|assistant|system",
    agent_type: "agent1|agent2",
    timestamp: datetime()
})

// Requirement Nodes
CREATE (r:Requirement {
    id: "requirement_uuid",
    description: "requirement_text",
    priority: "high|medium|low",
    status: "pending|in_progress|completed",
    category: "feature|bug|enhancement"
})

// Implementation Nodes
CREATE (i:Implementation {
    id: "implementation_uuid",
    task_type: "code|test|integration",
    status: "success|failed|pending",
    files_changed: ["file1.py", "file2.js"],
    completion_time: duration()
})

// Dependency Nodes
CREATE (d:Dependency {
    id: "dependency_uuid",
    type: "technical|business|user",
    description: "dependency_description",
    blocking: true
})
```

**Relationship Types**:
```cypher
// Session contains messages
(s:Session)-[:CONTAINS]->(m:Message)

// Messages derive requirements
(m:Message)-[:DERIVES]->(r:Requirement)

// Requirements have dependencies
(r:Requirement)-[:DEPENDS_ON]->(d:Dependency)

// Requirements lead to implementations
(r:Requirement)-[:IMPLEMENTED_BY]->(i:Implementation)

// Implementations have prerequisites
(i:Implementation)-[:REQUIRES]->(i2:Implementation)

// Messages reference previous context
(m:Message)-[:REFERENCES]->(m2:Message)

// Sessions evolve from previous sessions
(s:Session)-[:CONTINUES]->(s2:Session)
```

## Memory API Layer

### Core Memory Manager

```python
# src/memory/core_manager.py
class MemoryManager:
    def __init__(self):
        self.postgres = PostgreSQLManager()
        self.qdrant = QdrantManager()
        self.neo4j = Neo4JManager()
        self.sync_manager = SynchronizationManager()
    
    async def store_conversation_turn(self, session_id, messages):
        """Store a complete conversation turn across all databases"""
        async with self.transaction_manager():
            # 1. Store in PostgreSQL
            pg_message_ids = await self.postgres.store_messages(session_id, messages)
            
            # 2. Generate and store embeddings in Qdrant
            for msg_id, message in zip(pg_message_ids, messages):
                embedding = await self.generate_embedding(message.content)
                await self.qdrant.store_vector(msg_id, embedding, {
                    "session_id": session_id,
                    "content_type": "message",
                    "agent_type": message.agent_type
                })
            
            # 3. Create relationships in Neo4J
            await self.neo4j.create_message_nodes(session_id, messages)
            
            # 4. Update context synchronization
            await self.sync_manager.sync_context(session_id)
    
    async def retrieve_context(self, session_id, query=None, limit=10):
        """Retrieve relevant context for a session"""
        context = {
            "recent_messages": [],
            "similar_context": [],
            "related_implementations": [],
            "dependency_graph": {}
        }
        
        # Recent conversation history
        context["recent_messages"] = await self.postgres.get_recent_messages(
            session_id, limit
        )
        
        # Semantic similarity search
        if query:
            similar_vectors = await self.qdrant.search_similar(query, limit=5)
            context["similar_context"] = similar_vectors
        
        # Related implementations
        context["related_implementations"] = await self.postgres.get_implementations(
            session_id
        )
        
        # Dependency and relationship graph
        context["dependency_graph"] = await self.neo4j.get_session_graph(session_id)
        
        return context
```

### Agent Integration Interfaces

#### Navigator Integration

```python
# src/memory/navigator_interface.py
class NavigatorMemoryInterface:
    def __init__(self, memory_manager):
        self.memory = memory_manager
    
    async def store_user_message(self, session_id, content, context=None):
        """Store user input and context"""
        message = Message(
            role="user",
            content=content,
            agent_type="navigator",
            metadata={"context": context}
        )
        await self.memory.store_conversation_turn(session_id, [message])
    
    async def store_agent_response(self, session_id, response, analysis=None):
        """Store Agent 1's response and analysis"""
        message = Message(
            role="assistant",
            content=response,
            agent_type="navigator",
            metadata={"analysis": analysis}
        )
        await self.memory.store_conversation_turn(session_id, [message])
    
    async def get_conversation_context(self, session_id, depth=10):
        """Get conversation context for Agent 1"""
        return await self.memory.retrieve_context(
            session_id, 
            limit=depth
        )
    
    async def search_similar_conversations(self, query, exclude_session=None):
        """Find similar past conversations"""
        results = await self.memory.qdrant.search_similar(
            query, 
            filters={"session_id": {"$ne": exclude_session}} if exclude_session else None
        )
        return results
```

#### NeuroDock Integration

```python
# src/memory/neurodock_interface.py
class NeuroDockMemoryInterface:
    def __init__(self, memory_manager):
        self.memory = memory_manager
    
    async def get_implementation_requirements(self, session_id):
        """Extract implementation requirements from conversation"""
        context = await self.memory.retrieve_context(session_id)
        
        # Use Neo4J to find requirement nodes
        requirements = await self.memory.neo4j.query("""
            MATCH (s:Session {id: $session_id})-[:CONTAINS]->(m:Message)
                  -[:DERIVES]->(r:Requirement)
            WHERE r.status IN ['pending', 'in_progress']
            RETURN r
        """, session_id=session_id)
        
        return requirements
    
    async def store_implementation_result(self, session_id, task_id, result):
        """Store implementation results"""
        # Store in PostgreSQL
        result_id = await self.memory.postgres.store_implementation_result(
            session_id, task_id, result
        )
        
        # Store knowledge embedding in Qdrant
        knowledge_text = f"Task: {result.task_type}, Files: {result.files_changed}, Outcome: {result.status}"
        embedding = await self.memory.generate_embedding(knowledge_text)
        await self.memory.qdrant.store_vector(result_id, embedding, {
            "result_id": result_id,
            "task_type": result.task_type,
            "technologies": result.technologies_used,
            "success_patterns": result.success_patterns
        })
        
        # Update Neo4J relationships
        await self.memory.neo4j.create_implementation_node(session_id, result)
    
    async def get_similar_implementations(self, task_description):
        """Find similar past implementations"""
        return await self.memory.qdrant.search_similar(
            task_description,
            collection_name="implementation_knowledge"
        )
```

## Synchronization and Consistency

### Transaction Management

```python
# src/memory/transaction_manager.py
class TransactionManager:
    def __init__(self, postgres, qdrant, neo4j):
        self.postgres = postgres
        self.qdrant = qdrant
        self.neo4j = neo4j
    
    async def __aenter__(self):
        """Start distributed transaction"""
        self.pg_tx = await self.postgres.begin_transaction()
        self.neo4j_tx = await self.neo4j.begin_transaction()
        # Note: Qdrant doesn't support transactions, so we handle rollback manually
        self.qdrant_operations = []
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Commit or rollback distributed transaction"""
        if exc_type is None:
            # Commit all
            await self.pg_tx.commit()
            await self.neo4j_tx.commit()
            # Qdrant operations are already applied
        else:
            # Rollback all
            await self.pg_tx.rollback()
            await self.neo4j_tx.rollback()
            
            # Manual rollback for Qdrant
            for operation in reversed(self.qdrant_operations):
                await self.rollback_qdrant_operation(operation)
```

### Event-Driven Synchronization

```python
# src/memory/sync_manager.py
class SynchronizationManager:
    def __init__(self):
        self.event_queue = asyncio.Queue()
        self.subscribers = {
            "message_stored": [],
            "implementation_completed": [],
            "context_updated": []
        }
    
    async def sync_context(self, session_id):
        """Synchronize context across all databases"""
        # Trigger context update event
        await self.publish_event("context_updated", {
            "session_id": session_id,
            "timestamp": datetime.utcnow()
        })
    
    async def publish_event(self, event_type, data):
        """Publish synchronization event"""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow()
        }
        await self.event_queue.put(event)
        
        # Notify subscribers
        for subscriber in self.subscribers.get(event_type, []):
            await subscriber(event)
    
    def subscribe(self, event_type, callback):
        """Subscribe to synchronization events"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
```

## Performance Optimization

### Caching Strategy

```python
# src/memory/cache_manager.py
class CacheManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.cache_ttl = {
            "conversation_context": 3600,  # 1 hour
            "similar_context": 1800,       # 30 minutes
            "implementation_results": 7200  # 2 hours
        }
    
    async def get_cached_context(self, session_id):
        """Get cached conversation context"""
        cache_key = f"context:{session_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        return None
    
    async def cache_context(self, session_id, context):
        """Cache conversation context"""
        cache_key = f"context:{session_id}"
        await self.redis.setex(
            cache_key,
            self.cache_ttl["conversation_context"],
            json.dumps(context, default=str)
        )
```

### Connection Pooling

```python
# src/memory/connection_manager.py
class ConnectionManager:
    def __init__(self):
        self.postgres_pool = None
        self.qdrant_client = None
        self.neo4j_driver = None
    
    async def initialize(self):
        """Initialize connection pools"""
        # PostgreSQL connection pool
        self.postgres_pool = await asyncpg.create_pool(
            dsn=os.getenv("DATABASE_URL"),
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        
        # Qdrant client with connection pooling
        self.qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
            timeout=30
        )
        
        # Neo4J driver with connection pool
        self.neo4j_driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD")),
            max_connection_lifetime=3600,
            max_connection_pool_size=50,
            connection_acquisition_timeout=60
        )
```

## Monitoring and Health Checks

### System Health Monitoring

```python
# src/memory/health_monitor.py
class HealthMonitor:
    def __init__(self, memory_manager):
        self.memory = memory_manager
    
    async def check_system_health(self):
        """Comprehensive system health check"""
        health_status = {
            "postgres": await self.check_postgres_health(),
            "qdrant": await self.check_qdrant_health(),
            "neo4j": await self.check_neo4j_health(),
            "synchronization": await self.check_sync_health(),
            "overall": "healthy"
        }
        
        # Determine overall health
        if any(status != "healthy" for status in health_status.values() if status != "overall"):
            health_status["overall"] = "degraded"
        
        return health_status
    
    async def check_postgres_health(self):
        """Check PostgreSQL connectivity and performance"""
        try:
            async with self.memory.postgres.pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                latency = await self.measure_query_latency(conn)
                
                if latency > 1000:  # > 1 second
                    return "slow"
                return "healthy"
        except Exception:
            return "unhealthy"
    
    async def check_qdrant_health(self):
        """Check Qdrant connectivity and collection status"""
        try:
            collections = await self.memory.qdrant.client.get_collections()
            if len(collections.collections) == 0:
                return "no_collections"
            return "healthy"
        except Exception:
            return "unhealthy"
    
    async def check_neo4j_health(self):
        """Check Neo4J connectivity and constraint status"""
        try:
            with self.memory.neo4j.driver.session() as session:
                result = session.run("RETURN 1 as test")
                if result.single()["test"] == 1:
                    return "healthy"
        except Exception:
            return "unhealthy"
```

## Error Handling and Recovery

### Automatic Recovery Mechanisms

```python
# src/memory/recovery_manager.py
class RecoveryManager:
    def __init__(self, memory_manager):
        self.memory = memory_manager
        self.max_retries = 3
        self.retry_delay = 1.0
    
    async def recover_from_sync_failure(self, session_id, operation_type):
        """Recover from synchronization failures"""
        for attempt in range(self.max_retries):
            try:
                if operation_type == "message_store":
                    await self.recover_message_storage(session_id)
                elif operation_type == "context_sync":
                    await self.recover_context_sync(session_id)
                elif operation_type == "implementation_store":
                    await self.recover_implementation_storage(session_id)
                
                break  # Success
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise  # Final attempt failed
                
                await asyncio.sleep(self.retry_delay * (2 ** attempt))
    
    async def recover_message_storage(self, session_id):
        """Recover incomplete message storage operations"""
        # Check for orphaned records across databases
        pg_messages = await self.memory.postgres.get_session_messages(session_id)
        qdrant_vectors = await self.memory.qdrant.get_session_vectors(session_id)
        neo4j_nodes = await self.memory.neo4j.get_session_nodes(session_id)
        
        # Identify and fix inconsistencies
        await self.reconcile_message_data(pg_messages, qdrant_vectors, neo4j_nodes)
```

## Configuration and Deployment

### Environment Configuration

```bash
# Memory System Configuration
MEMORY_POSTGRES_URL=postgresql://user:pass@localhost:5432/neurodock
MEMORY_QDRANT_URL=http://localhost:6333
MEMORY_QDRANT_API_KEY=your_qdrant_api_key
MEMORY_NEO4J_URI=bolt://localhost:7687
MEMORY_NEO4J_USER=neo4j
MEMORY_NEO4J_PASSWORD=your_neo4j_password

# Performance Settings
MEMORY_POSTGRES_POOL_SIZE=20
MEMORY_QDRANT_TIMEOUT=30
MEMORY_NEO4J_POOL_SIZE=50
MEMORY_CACHE_TTL=3600

# Monitoring Settings
MEMORY_HEALTH_CHECK_INTERVAL=60
MEMORY_LOG_LEVEL=INFO
MEMORY_METRICS_ENABLED=true
```

### Docker Deployment

```yaml
# docker-compose.memory.yml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: neurodock
      POSTGRES_USER: neurodock
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql/init_schema.sql:/docker-entrypoint-initdb.d/init_schema.sql
    ports:
      - "5432:5432"
  
  qdrant:
    image: qdrant/qdrant:v1.7.0
    environment:
      QDRANT__SERVICE__HTTP_PORT: 6333
      QDRANT__SERVICE__GRPC_PORT: 6334
    volumes:
      - qdrant_data:/qdrant/storage
    ports:
      - "6333:6333"
      - "6334:6334"
  
  neo4j:
    image: neo4j:5.15
    environment:
      NEO4J_AUTH: neo4j/secure_password
      NEO4J_PLUGINS: '["apoc"]'
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    ports:
      - "7474:7474"
      - "7687:7687"

volumes:
  postgres_data:
  qdrant_data:
  neo4j_data:
  neo4j_logs:
```

## Usage Examples

### Basic Memory Operations

```python
# Initialize memory system
memory = MemoryManager()
await memory.initialize()

# Store conversation
session_id = "user_session_123"
await memory.store_conversation_turn(session_id, [
    Message(role="user", content="Create a user authentication system", agent_type="agent1"),
    Message(role="assistant", content="I'll help you create a user authentication system...", agent_type="agent1")
])

# Retrieve context
context = await memory.retrieve_context(session_id)
print(f"Recent messages: {len(context['recent_messages'])}")
print(f"Similar context found: {len(context['similar_context'])}")

# Search for similar implementations
similar = await memory.search_similar_implementations("user authentication")
for result in similar:
    print(f"Similar task: {result.payload['task_type']} (score: {result.score})")
```

### Agent Integration Example

```python
# Agent 1 storing user input
agent1_interface = Agent1MemoryInterface(memory)
await agent1_interface.store_user_message(
    session_id, 
    "Add OAuth integration with Google and GitHub",
    context={"project_type": "web_app", "tech_stack": ["FastAPI", "React"]}
)

# Agent 2 retrieving requirements
agent2_interface = Agent2MemoryInterface(memory)
requirements = await agent2_interface.get_implementation_requirements(session_id)

# Agent 2 storing implementation results
result = ImplementationResult(
    task_type="oauth_integration",
    status="success",
    files_changed=["auth.py", "oauth_providers.py", "frontend/login.js"],
    technologies_used=["FastAPI", "OAuth2", "React"],
    tests_run={"unit": 15, "integration": 5, "passed": 20, "failed": 0}
)
await agent2_interface.store_implementation_result(session_id, "task_001", result)
```

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   ```bash
   # Check database connectivity
   python -m src.memory.diagnostics --check-connections
   
   # Test individual databases
   python -m src.memory.diagnostics --test-postgres
   python -m src.memory.diagnostics --test-qdrant
   python -m src.memory.diagnostics --test-neo4j
   ```

2. **Synchronization Problems**
   ```bash
   # Check synchronization status
   python -m src.memory.diagnostics --check-sync --session SESSION_ID
   
   # Force resynchronization
   python -m src.memory.recovery --resync-session SESSION_ID
   ```

3. **Performance Issues**
   ```bash
   # Monitor memory system performance
   python -m src.memory.monitor --performance
   
   # Analyze slow queries
   python -m src.memory.diagnostics --slow-queries --limit 10
   ```

The memory system forms the backbone of NeuroDock's dual-agent architecture, enabling seamless collaboration between conversation and implementation agents while maintaining data consistency and providing intelligent context retrieval.
