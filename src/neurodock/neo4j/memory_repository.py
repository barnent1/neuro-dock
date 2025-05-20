from typing import List, Dict, Optional, Any, Union
from uuid import UUID, uuid4
from datetime import datetime

from neo4j import Record

from neurodock.models.memory import MemoryNode, MemoryEdge, MemoryCreate, MemoryType
from neurodock.neo4j.client import neo4j_client


class MemoryRepository:
    """
    Repository for memory-related operations in Neo4j.
    """
    
    @staticmethod
    async def create_memory(memory: MemoryCreate) -> MemoryNode:
        """
        Create a new memory node in the database.
        """
        memory_id = uuid4()
        timestamp = datetime.now()
        
        query = """
        CREATE (m:MemoryNode {
            id: $id,
            content: $content,
            type: $type,
            timestamp: $timestamp,
            source: $source,
            project_id: $project_id
        })
        RETURN m
        """
        
        params = {
            "id": str(memory_id),
            "content": memory.content,
            "type": memory.type,
            "timestamp": timestamp.isoformat(),
            "source": memory.source,
            "project_id": memory.project_id
        }
        
        async with neo4j_client.get_session() as session:
            result = await session.run(query, params)
            record = await result.single()
            node_data = record["m"]
            
            return MemoryNode(
                id=UUID(node_data["id"]),
                content=node_data["content"],
                type=node_data["type"],
                timestamp=datetime.fromisoformat(node_data["timestamp"]),
                source=node_data["source"],
                project_id=node_data["project_id"]
            )
    
    @staticmethod
    async def get_memory_by_id(memory_id: UUID) -> Optional[MemoryNode]:
        """
        Get a memory node by its ID.
        """
        query = """
        MATCH (m:MemoryNode {id: $id})
        RETURN m
        """
        
        params = {"id": str(memory_id)}
        
        async with neo4j_client.get_session() as session:
            result = await session.run(query, params)
            record = await result.single()
            
            if not record:
                return None
                
            node_data = record["m"]
            return MemoryNode(
                id=UUID(node_data["id"]),
                content=node_data["content"],
                type=node_data["type"],
                timestamp=datetime.fromisoformat(node_data["timestamp"]),
                source=node_data["source"],
                project_id=node_data["project_id"]
            )
    
    @staticmethod
    async def create_memory_relationship(edge: MemoryEdge) -> MemoryEdge:
        """
        Create a relationship between two memory nodes.
        """
        edge_id = uuid4() if not edge.id else edge.id
        
        query = """
        MATCH (from:MemoryNode {id: $from_id})
        MATCH (to:MemoryNode {id: $to_id})
        CREATE (from)-[r:RELATED {
            id: $id,
            label: $label,
            confidence: $confidence
        }]->(to)
        RETURN r
        """
        
        params = {
            "id": str(edge_id),
            "from_id": str(edge.from_id),
            "to_id": str(edge.to_id),
            "label": edge.label,
            "confidence": edge.confidence
        }
        
        async with neo4j_client.get_session() as session:
            result = await session.run(query, params)
            record = await result.single()
            
            if not record:
                raise ValueError("Failed to create relationship")
                
            rel_data = record["r"]
            return MemoryEdge(
                id=UUID(rel_data["id"]),
                from_id=edge.from_id,
                to_id=edge.to_id,
                label=rel_data["label"],
                confidence=rel_data["confidence"]
            )
    
    @staticmethod
    async def get_related_memories(
        memory_id: UUID, 
        limit: int = 10, 
        min_confidence: float = 0.5,
        project_id: Optional[str] = None
    ) -> List[MemoryNode]:
        """
        Get memories related to the given memory ID.
        
        Args:
            memory_id: ID of the memory to find related memories for
            limit: Maximum number of memories to return
            min_confidence: Minimum confidence score for relationships
            project_id: Optional project ID to filter memories by
        """
        # Base query without project filtering
        base_query = """
        MATCH (m:MemoryNode {id: $id})-[r:RELATED]->(related:MemoryNode)
        WHERE r.confidence >= $min_confidence
        """
        
        # Add project filter if specified
        if project_id:
            query = base_query + """
            AND related.project_id = $project_id
            RETURN related
            ORDER BY r.confidence DESC
            LIMIT $limit
            """
        else:
            query = base_query + """
            RETURN related
            ORDER BY r.confidence DESC
            LIMIT $limit
            """
        
        params = {
            "id": str(memory_id),
            "limit": limit,
            "min_confidence": min_confidence
        }
        
        if project_id:
            params["project_id"] = project_id
        
        async with neo4j_client.get_session() as session:
            result = await session.run(query, params)
            memories = []
            async for record in result:
                node_data = record["related"]
                memories.append(
                    MemoryNode(
                        id=UUID(node_data["id"]),
                        content=node_data["content"],
                        type=node_data["type"],
                        timestamp=datetime.fromisoformat(node_data["timestamp"]),
                        source=node_data["source"],
                        project_id=node_data.get("project_id")
                    )
                )
            return memories
    
    @staticmethod
    async def search_memories(
        query_text: str,
        memory_type: Optional[MemoryType] = None,
        project_id: Optional[str] = None,
        limit: int = 10,
        use_fulltext: bool = False
    ) -> List[MemoryNode]:
        """
        Search memories by content, optionally filtered by project.
        
        Args:
            query_text: Text to search for in memory content
            memory_type: Optional memory type filter
            project_id: Optional project ID filter
            limit: Maximum number of results to return
            use_fulltext: Whether to use full-text search instead of CONTAINS
            
        Returns:
            List of memory nodes matching the search criteria
        """
        # Build the query conditions based on parameters
        params = {
            "query_text": query_text,
            "limit": limit
        }
        
        # Use different search method based on use_fulltext flag
        if use_fulltext:
            # Use full-text search index if available
            search_condition = "apoc.text.fuzzyMatch(m.content, $query_text) > 0.7"
        else:
            # Use standard CONTAINS operator
            search_condition = "m.content CONTAINS $query_text"
            
        conditions = [search_condition]
        
        # Add type filter if specified
        if memory_type:
            conditions.append("m.type = $type")
            params["type"] = memory_type
        
        # Add project filter if specified
        if project_id:
            conditions.append("m.project_id = $project_id")
            params["project_id"] = project_id
        
        # Build the where clause
        where_clause = " AND ".join(conditions)
        
        # Construct the full query
        query = f"""
        MATCH (m:MemoryNode)
        WHERE {where_clause}
        RETURN m
        ORDER BY m.timestamp DESC
        LIMIT $limit
        """
        
        async with neo4j_client.get_session() as session:
            try:
                result = await session.run(query, params)
                memories = []
                async for record in result:
                    node_data = record["m"]
                    memories.append(
                        MemoryNode(
                            id=UUID(node_data["id"]),
                            content=node_data["content"],
                            type=node_data["type"],
                            timestamp=datetime.fromisoformat(node_data["timestamp"]),
                            source=node_data["source"],
                            project_id=node_data.get("project_id")
                        )
                    )
                return memories
            except Exception as e:
                # If APOC procedures are not available, fall back to standard search
                if use_fulltext and "apoc.text.fuzzyMatch" in str(e):
                    return await MemoryRepository.search_memories(
                        query_text=query_text,
                        memory_type=memory_type,
                        project_id=project_id,
                        limit=limit,
                        use_fulltext=False
                    )
                raise
    
    @staticmethod
    async def delete_memory(memory_id: UUID) -> bool:
        """
        Delete a memory node from the database.
        
        Args:
            memory_id: The ID of the memory to delete
            
        Returns:
            bool: True if the memory was successfully deleted, False otherwise
        """
        query = """
        MATCH (m:MemoryNode {id: $id})
        DETACH DELETE m
        RETURN count(m) as deleted_count
        """
        
        params = {"id": str(memory_id)}
        
        async with neo4j_client.get_session() as session:
            result = await session.run(query, params)
            record = await result.single()
            
            if not record:
                return False
                
            return record["deleted_count"] > 0
    
    @staticmethod
    async def delete_project_memories(project_id: str) -> bool:
        """
        Delete all memories for a specific project.
        
        Args:
            project_id: The project ID to delete memories for
            
        Returns:
            bool: True if memories were deleted, False otherwise
        """
        query = """
        MATCH (m:MemoryNode {project_id: $project_id})
        WITH m
        DETACH DELETE m
        RETURN count(m) as deleted_count
        """
        
        params = {"project_id": project_id}
        
        async with neo4j_client.get_session() as session:
            result = await session.run(query, params)
            record = await result.single()
            
            return record["deleted_count"] > 0

    @staticmethod
    async def get_memories_batch(memory_ids: List[UUID]) -> List[MemoryNode]:
        """
        Get multiple memory nodes by their IDs in a single batch query.
        
        Args:
            memory_ids: List of memory IDs to retrieve
            
        Returns:
            List of memory nodes matching the provided IDs
        """
        if not memory_ids:
            return []
            
        # Convert UUIDs to strings
        id_strings = [str(id) for id in memory_ids]
        
        query = """
        MATCH (m:MemoryNode)
        WHERE m.id IN $ids
        RETURN m
        """
        
        params = {"ids": id_strings}
        
        async with neo4j_client.get_session() as session:
            result = await session.run(query, params)
            memories = []
            async for record in result:
                node_data = record["m"]
                memories.append(
                    MemoryNode(
                        id=UUID(node_data["id"]),
                        content=node_data["content"],
                        type=node_data["type"],
                        timestamp=datetime.fromisoformat(node_data["timestamp"]),
                        source=node_data["source"],
                        project_id=node_data.get("project_id")
                    )
                )
            return memories
            
            return memories
            
