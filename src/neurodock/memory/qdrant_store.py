#!/usr/bin/env python3
"""
Qdrant-based vector memory system for neuro-dock.

This module provides functionality to store and retrieve meaningful content
using vector embeddings for improved long-term context handling.
"""

import os
import warnings
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import uuid4

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    from sentence_transformers import SentenceTransformer
    QDRANT_AVAILABLE = True
except ImportError:
    QdrantClient = None
    SentenceTransformer = None
    QDRANT_AVAILABLE = False

# Global variables for lazy loading
_client: Optional[QdrantClient] = None
_model: Optional[SentenceTransformer] = None

def _get_client() -> Optional[QdrantClient]:
    """Get or create Qdrant client with lazy loading."""
    global _client
    if _client is None and QDRANT_AVAILABLE:
        try:
            _client = QdrantClient(host="localhost", port=6333)
            # Test connection
            _client.get_collections()
        except Exception as e:
            # Silent fallback - Qdrant connection failed
            return None
    return _client

def _get_model() -> Optional[SentenceTransformer]:
    """Get or create sentence transformer model with lazy loading."""
    global _model
    if _model is None and QDRANT_AVAILABLE:
        try:
            _model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        except Exception as e:
            # Silent fallback - sentence transformer unavailable
            return None
    return _model

def _ensure_collection() -> bool:
    """Ensure the neurodock_memory collection exists."""
    client = _get_client()
    if not client:
        return False
    
    try:
        # Check if collection exists
        collections = client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if "neurodock_memory" not in collection_names:
            # Create collection with 384-dimensional vectors (all-MiniLM-L6-v2 output size)
            client.create_collection(
                collection_name="neurodock_memory",
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
        return True
    except Exception as e:
        # Silent fallback - failed to ensure collection
        return False

def add_to_memory(text: str, metadata: Dict[str, Any]) -> None:
    """
    Add text content to vector memory.
    
    Args:
        text: The text content to store
        metadata: Dictionary containing project_path, task_id, type, etc.
        
    Example:
        >>> add_to_memory(
        ...     "Create a Flask web application with user authentication",
        ...     {"project_path": "/path/to/project", "task_id": "task_1", "type": "prompt"}
        ... )
    """
    if not QDRANT_AVAILABLE:
        # Silent fallback - memory storage unavailable
        return
    
    model = _get_model()
    if not model or not _ensure_collection():
        return
    
    try:
        # Generate embedding
        embedding = model.encode(text).tolist()
        
        # Add current working directory as project_path if not provided
        if "project_path" not in metadata:
            metadata["project_path"] = str(Path.cwd())
        
        # Create point with unique ID
        point = PointStruct(
            id=str(uuid4()),
            vector=embedding,
            payload={
                "text": text,
                **metadata
            }
        )
        
        # Store in Qdrant
        client = _get_client()
        if client:
            client.upsert(collection_name="neurodock_memory", points=[point])
            
    except Exception as e:
        # Silent fallback - failed to add to memory
        pass

def search_memory(query: str, limit: int = 5, project_path: Optional[str] = None) -> List[str]:
    """
    Search for relevant memory entries using vector similarity.
    
    Args:
        query: The search query text
        limit: Maximum number of results to return
        project_path: Filter by specific project path (uses current directory if None)
        
    Returns:
        List of relevant text entries from memory
        
    Example:
        >>> results = search_memory("Flask authentication", limit=3)
        >>> for result in results:
        ...     print(f"- {result}")
    """
    if not QDRANT_AVAILABLE:
        # Silent fallback - context recall unavailable
        return []
    
    model = _get_model()
    client = _get_client()
    if not model or not client or not _ensure_collection():
        return []
    
    try:
        # Use current directory if no project_path specified
        if project_path is None:
            project_path = str(Path.cwd())
        
        # Generate query embedding
        query_embedding = model.encode(query).tolist()
        
        # Search with project_path filter
        search_result = client.search(
            collection_name="neurodock_memory",
            query_vector=query_embedding,
            query_filter={
                "must": [
                    {"key": "project_path", "match": {"value": project_path}}
                ]
            },
            limit=limit
        )
        
        # Extract text from results
        results = []
        for point in search_result:
            if point.payload and "text" in point.payload:
                results.append(point.payload["text"])
        
        return results
        
    except Exception as e:
        # Silent fallback - memory search failed
        return []

def test_memory_system() -> bool:
    """
    Test the memory system by adding sample entries and searching.
    
    Returns:
        True if all tests pass, False otherwise
        
    Example usage:
        >>> if test_memory_system():
        ...     print("✅ Memory system is working!")
        ... else:
        ...     print("❌ Memory system failed")
    """
    if not QDRANT_AVAILABLE:
        print("❌ Qdrant dependencies not available. Install with: pip install qdrant-client sentence-transformers")
        return False
    
    print("🧠 Testing Qdrant memory system...")
    
    # Test data
    test_entries = [
        {
            "text": "Create a Flask web application with user authentication and database integration",
            "metadata": {"task_id": "test_1", "type": "prompt", "project_path": str(Path.cwd())}
        },
        {
            "text": "Implement REST API endpoints for user management and session handling",
            "metadata": {"task_id": "test_2", "type": "task", "project_path": str(Path.cwd())}
        },
        {
            "text": "Set up database models for User, Session, and authentication using SQLAlchemy",
            "metadata": {"task_id": "test_3", "type": "clarification", "project_path": str(Path.cwd())}
        }
    ]
    
    try:
        # Add test entries
        print("📝 Adding test memory entries...")
        for i, entry in enumerate(test_entries, 1):
            add_to_memory(entry["text"], entry["metadata"])
            print(f"  {i}. Added: {entry['text'][:50]}...")
        
        # Test search
        print("\n🔍 Testing memory search...")
        test_query = "Flask authentication database"
        results = search_memory(test_query, limit=3)
        
        if not results:
            print("❌ No search results returned")
            return False
        
        print(f"\nQuery: '{test_query}'")
        print("📋 Top 3 relevant memories:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result}")
        
        print(f"\n✅ Memory system is working! Found {len(results)} relevant entries.")
        return True
        
    except Exception as e:
        print(f"❌ Memory system test failed: {e}")
        return False
