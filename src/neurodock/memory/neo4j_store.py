#!/usr/bin/env python3
"""
Neo4J Graph Database for NeuroDock Agent Memory System

This module provides graph-based memory storage and retrieval using Neo4J,
enabling both Agent 1 and Agent 2 to share contextual knowledge, relationships,
and project understanding.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

@dataclass
class MemoryNode:
    """Represents a memory node in the graph."""
    id: str
    type: str
    content: str
    metadata: Dict[str, Any]
    created_at: datetime
    project_path: str

@dataclass
class MemoryRelationship:
    """Represents a relationship between memory nodes."""
    from_node: str
    to_node: str
    relationship_type: str
    properties: Dict[str, Any]

class Neo4JMemoryStore:
    """
    Neo4J-based memory store for NeuroDock agent system.
    
    Provides graph-based memory storage that enables both Agent 1 (Project Agent)
    and Agent 2 (LLM Backend) to share contextual knowledge and understanding.
    """
    
    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password"):
        """Initialize Neo4J connection."""
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self.logger = logging.getLogger(__name__)
        
        if NEO4J_AVAILABLE:
            try:
                self.driver = GraphDatabase.driver(uri, auth=(user, password))
                self.driver.verify_connectivity()
                self._initialize_schema()
            except Exception as e:
                self.logger.warning(f"Neo4J connection failed: {e}")
                self.driver = None
        else:
            self.logger.warning("Neo4J dependencies not available. Install with: pip install neo4j")
    
    def _initialize_schema(self):
        """Initialize Neo4J schema and constraints."""
        if not self.driver:
            return
            
        with self.driver.session() as session:
            # Create constraints
            session.run("""
                CREATE CONSTRAINT memory_id IF NOT EXISTS
                FOR (m:Memory) REQUIRE m.id IS UNIQUE
            """)
            
            # Create indexes
            session.run("""
                CREATE INDEX memory_type IF NOT EXISTS
                FOR (m:Memory) ON (m.type)
            """)
            
            session.run("""
                CREATE INDEX memory_project IF NOT EXISTS
                FOR (m:Memory) ON (m.project_path)
            """)
            
            session.run("""
                CREATE INDEX memory_created IF NOT EXISTS
                FOR (m:Memory) ON (m.created_at)
            """)
    
    def add_memory(self, content: str, memory_type: str, metadata: Optional[Dict[str, Any]] = None, 
                   project_path: Optional[str] = None) -> Optional[str]:
        """
        Add a memory node to the graph.
        
        Args:
            content: The memory content
            memory_type: Type of memory (task, prompt, clarification, etc.)
            metadata: Additional metadata for the memory
            project_path: Project path for scoping
            
        Returns:
            Memory node ID if successful, None otherwise
        """
        if not self.driver:
            return None
            
        if not project_path:
            project_path = str(Path.cwd())
            
        memory_id = f"mem_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(content) % 10000}"
        metadata = metadata or {}
        
        with self.driver.session() as session:
            try:
                result = session.run("""
                    CREATE (m:Memory {
                        id: $memory_id,
                        type: $memory_type,
                        content: $content,
                        metadata: $metadata,
                        created_at: datetime(),
                        project_path: $project_path
                    })
                    RETURN m.id as id
                """, {
                    "memory_id": memory_id,
                    "memory_type": memory_type,
                    "content": content,
                    "metadata": json.dumps(metadata),
                    "project_path": project_path
                })
                
                record = result.single()
                if record:
                    self.logger.info(f"Added memory node: {memory_id}")
                    return record["id"]
                    
            except Exception as e:
                self.logger.error(f"Failed to add memory: {e}")
                
        return None
    
    def add_relationship(self, from_memory_id: str, to_memory_id: str, 
                        relationship_type: str, properties: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a relationship between two memory nodes.
        
        Args:
            from_memory_id: Source memory node ID
            to_memory_id: Target memory node ID
            relationship_type: Type of relationship (LEADS_TO, DEPENDS_ON, etc.)
            properties: Additional properties for the relationship
            
        Returns:
            True if successful, False otherwise
        """
        if not self.driver:
            return False
            
        properties = properties or {}
        
        with self.driver.session() as session:
            try:
                session.run(f"""
                    MATCH (from:Memory {{id: $from_id}})
                    MATCH (to:Memory {{id: $to_id}})
                    CREATE (from)-[r:{relationship_type} $properties]->(to)
                """, {
                    "from_id": from_memory_id,
                    "to_id": to_memory_id,
                    "properties": properties
                })
                
                self.logger.info(f"Added relationship: {from_memory_id} -{relationship_type}-> {to_memory_id}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to add relationship: {e}")
                return False
    
    def search_memories(self, query: str, memory_types: Optional[List[str]] = None,
                       project_path: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for memories using text content and graph relationships.
        
        Args:
            query: Search query
            memory_types: Filter by memory types
            project_path: Filter by project path
            limit: Maximum number of results
            
        Returns:
            List of memory dictionaries
        """
        if not self.driver:
            return []
            
        if not project_path:
            project_path = str(Path.cwd())
            
        # Build the query
        where_clauses = ["m.project_path = $project_path"]
        params = {"project_path": project_path, "limit": limit}
        
        if memory_types:
            where_clauses.append("m.type IN $memory_types")
            params["memory_types"] = memory_types
            
        if query:
            where_clauses.append("toLower(m.content) CONTAINS toLower($query)")
            params["query"] = query
            
        where_clause = " AND ".join(where_clauses)
        
        cypher_query = f"""
            MATCH (m:Memory)
            WHERE {where_clause}
            RETURN m.id as id, m.type as type, m.content as content, 
                   m.metadata as metadata, m.created_at as created_at
            ORDER BY m.created_at DESC
            LIMIT $limit
        """
        
        with self.driver.session() as session:
            try:
                result = session.run(cypher_query, params)
                memories = []
                
                for record in result:
                    memory = {
                        "id": record["id"],
                        "type": record["type"],
                        "content": record["content"],
                        "metadata": json.loads(record["metadata"]) if record["metadata"] else {},
                        "created_at": record["created_at"]
                    }
                    memories.append(memory)
                    
                return memories
                
            except Exception as e:
                self.logger.error(f"Failed to search memories: {e}")
                return []
    
    def get_related_memories(self, memory_id: str, relationship_types: Optional[List[str]] = None,
                           depth: int = 2) -> List[Dict[str, Any]]:
        """
        Get memories related to a given memory through graph relationships.
        
        Args:
            memory_id: Starting memory node ID
            relationship_types: Filter by relationship types
            depth: Maximum relationship depth to traverse
            
        Returns:
            List of related memory dictionaries
        """
        if not self.driver:
            return []
            
        # Build relationship pattern
        if relationship_types:
            rel_pattern = f"[r:{':'.join(relationship_types)}]"
        else:
            rel_pattern = "[r]"
            
        cypher_query = f"""
            MATCH (start:Memory {{id: $memory_id}})
            MATCH (start)-{rel_pattern}*1..{depth}-(related:Memory)
            WHERE start <> related
            RETURN DISTINCT related.id as id, related.type as type, 
                   related.content as content, related.metadata as metadata,
                   related.created_at as created_at
            ORDER BY related.created_at DESC
        """
        
        with self.driver.session() as session:
            try:
                result = session.run(cypher_query, {"memory_id": memory_id})
                memories = []
                
                for record in result:
                    memory = {
                        "id": record["id"],
                        "type": record["type"],
                        "content": record["content"],
                        "metadata": json.loads(record["metadata"]) if record["metadata"] else {},
                        "created_at": record["created_at"]
                    }
                    memories.append(memory)
                    
                return memories
                
            except Exception as e:
                self.logger.error(f"Failed to get related memories: {e}")
                return []
    
    def get_project_context(self, project_path: Optional[str] = None, 
                           hours_back: int = 24) -> Dict[str, Any]:
        """
        Get comprehensive project context from the memory graph.
        
        Args:
            project_path: Project path to filter by
            hours_back: How many hours back to look for recent context
            
        Returns:
            Dictionary with project context summary
        """
        if not self.driver:
            return {}
            
        if not project_path:
            project_path = str(Path.cwd())
            
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        with self.driver.session() as session:
            try:
                # Get memory counts by type
                type_counts = session.run("""
                    MATCH (m:Memory {project_path: $project_path})
                    WHERE m.created_at >= datetime($cutoff_time)
                    RETURN m.type as type, count(m) as count
                    ORDER BY count DESC
                """, {
                    "project_path": project_path,
                    "cutoff_time": cutoff_time.isoformat()
                }).data()
                
                # Get recent memories
                recent_memories = session.run("""
                    MATCH (m:Memory {project_path: $project_path})
                    WHERE m.created_at >= datetime($cutoff_time)
                    RETURN m.type as type, m.content as content
                    ORDER BY m.created_at DESC
                    LIMIT 10
                """, {
                    "project_path": project_path,
                    "cutoff_time": cutoff_time.isoformat()
                }).data()
                
                # Get relationship summary
                relationships = session.run("""
                    MATCH (m1:Memory {project_path: $project_path})-[r]->(m2:Memory {project_path: $project_path})
                    WHERE m1.created_at >= datetime($cutoff_time) OR m2.created_at >= datetime($cutoff_time)
                    RETURN type(r) as relationship_type, count(r) as count
                    ORDER BY count DESC
                """, {
                    "project_path": project_path,
                    "cutoff_time": cutoff_time.isoformat()
                }).data()
                
                return {
                    "project_path": project_path,
                    "memory_types": {item["type"]: item["count"] for item in type_counts},
                    "recent_memories": recent_memories,
                    "relationships": {item["relationship_type"]: item["count"] for item in relationships},
                    "total_memories": sum(item["count"] for item in type_counts),
                    "context_window_hours": hours_back
                }
                
            except Exception as e:
                self.logger.error(f"Failed to get project context: {e}")
                return {}
    
    def get_agent_reminders(self, agent_name: str, project_path: Optional[str] = None) -> List[str]:
        """
        Get contextual reminders for an agent based on recent project activity.
        
        Args:
            agent_name: Name of the agent (agent1, agent2)
            project_path: Project path to filter by
            
        Returns:
            List of reminder strings
        """
        if not self.driver:
            return []
            
        if not project_path:
            project_path = str(Path.cwd())
            
        context = self.get_project_context(project_path)
        reminders = []
        
        # Generate reminders based on context
        if context.get("total_memories", 0) > 0:
            memory_types = context.get("memory_types", {})
            
            # Task-related reminders
            if "task_execution" in memory_types:
                reminders.append(f"🔄 {memory_types['task_execution']} tasks have been executed recently")
                
            if "task_completion" in memory_types:
                reminders.append(f"✅ {memory_types['task_completion']} tasks have been completed")
                
            # Planning reminders
            if "project_plan" in memory_types:
                reminders.append("📋 Project plan has been updated - consider reviewing task dependencies")
                
            # Discussion reminders
            if "clarified_prompt" in memory_types:
                reminders.append("💬 Recent requirements clarification available - ensure alignment")
                
            # Recent activity summary
            recent_count = len(context.get("recent_memories", []))
            if recent_count > 5:
                reminders.append(f"🧠 High activity: {recent_count} memory entries in last 24h - stay focused on priorities")
                
            # Relationship insights
            relationships = context.get("relationships", {})
            if "DEPENDS_ON" in relationships:
                reminders.append("⚠️ Task dependencies exist - check completion order")
                
        return reminders
    
    def test_connection(self) -> bool:
        """Test Neo4J connection and basic functionality."""
        if not self.driver:
            return False
            
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 'Connection successful' as message")
                record = result.single()
                return record is not None
                
        except Exception as e:
            self.logger.error(f"Neo4J connection test failed: {e}")
            return False
    
    def close(self):
        """Close the Neo4J driver connection."""
        if self.driver:
            self.driver.close()

# Global instance
_neo4j_store = None

def get_neo4j_store() -> Optional[Neo4JMemoryStore]:
    """Get the global Neo4J memory store instance."""
    global _neo4j_store
    
    if _neo4j_store is None and NEO4J_AVAILABLE:
        # Try to get connection info from environment or config
        import os
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")
        
        _neo4j_store = Neo4JMemoryStore(uri, user, password)
        
    return _neo4j_store

def add_graph_memory(content: str, memory_type: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Add memory to Neo4J graph store."""
    store = get_neo4j_store()
    if store:
        return store.add_memory(content, memory_type, metadata)
    return None

def search_graph_memory(query: str, memory_types: Optional[List[str]] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Search Neo4J graph memory."""
    store = get_neo4j_store()
    if store:
        return store.search_memories(query, memory_types, limit=limit)
    return []

def get_agent_reminders(agent_name: str) -> List[str]:
    """Get contextual reminders for an agent."""
    store = get_neo4j_store()
    if store:
        return store.get_agent_reminders(agent_name)
    return []

def test_neo4j_system() -> bool:
    """Test the Neo4J memory system."""
    if not NEO4J_AVAILABLE:
        print("❌ Neo4J dependencies not available. Install with: pip install neo4j")
        return False
        
    store = get_neo4j_store()
    if not store:
        print("❌ Failed to initialize Neo4J store")
        return False
        
    print("🔍 Testing Neo4J memory system...")
    
    # Test connection
    if not store.test_connection():
        print("❌ Neo4J connection failed")
        print("💡 Make sure Neo4J is running: docker run -p 7474:7474 -p 7687:7687 neo4j")
        return False
        
    print("✅ Neo4J connection successful")
    
    # Test adding memories
    print("📝 Adding test memories...")
    mem1_id = store.add_memory("Create Flask authentication system", "task", {"priority": "high"})
    mem2_id = store.add_memory("Implement user login functionality", "subtask", {"parent": "auth_system"})
    mem3_id = store.add_memory("Set up database models for users", "task", {"complexity": 5})
    
    if mem1_id and mem2_id and mem3_id:
        print(f"✅ Added memories: {mem1_id}, {mem2_id}, {mem3_id}")
        
        # Test relationships
        print("🔗 Adding test relationships...")
        store.add_relationship(mem1_id, mem2_id, "CONTAINS")
        store.add_relationship(mem1_id, mem3_id, "DEPENDS_ON")
        
        # Test searching
        print("🔍 Testing memory search...")
        results = store.search_memories("Flask authentication")
        print(f"✅ Found {len(results)} memories matching 'Flask authentication'")
        
        # Test context
        print("📊 Testing project context...")
        context = store.get_project_context()
        print(f"✅ Project context: {context.get('total_memories', 0)} memories")
        
        # Test reminders
        print("💭 Testing agent reminders...")
        reminders = store.get_agent_reminders("agent1")
        print(f"✅ Generated {len(reminders)} reminders for agent1")
        for i, reminder in enumerate(reminders[:3], 1):
            print(f"   {i}. {reminder}")
            
        print("\n🎉 Neo4J memory system test completed successfully!")
        return True
    else:
        print("❌ Failed to add test memories")
        return False
