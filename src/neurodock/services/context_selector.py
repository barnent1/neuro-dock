from typing import List, Dict, Any, Optional
from uuid import UUID
import logging
import re

from neurodock.models.memory import MemoryNode, MemoryType
from neurodock.neo4j.memory_repository import MemoryRepository

logger = logging.getLogger(__name__)


class ContextSelector:
    """
    Service for selecting relevant context for a given query.
    This is a key component for building effective memory-augmented LLM interactions.
    """
    
    @staticmethod
    async def select_context(
        query: str,
        max_memories: int = 10,
        memory_types: Optional[List[MemoryType]] = None,
        project_id: Optional[str] = None
    ) -> List[MemoryNode]:
        """
        Select relevant memories for a given query.
        
        Args:
            query: The query to select context for
            max_memories: Maximum number of memories to return
            memory_types: Optional list of memory types to filter by
            project_id: Optional project ID to filter memories by
            
        Returns:
            List of relevant memory nodes
        """
        # For now, we'll use a simple keyword search
        # In the future, this could be replaced with a vector search or more sophisticated retrieval
        
        # Split query into keywords
        keywords = query.lower().split()
        results = []
        
        # For each keyword, find relevant memories
        for keyword in keywords:
            if len(keyword) < 3:
                continue  # Skip short keywords
                
            # Search for memories containing this keyword
            if memory_types:
                for memory_type in memory_types:
                    memories = await MemoryRepository.search_memories(
                        query_text=keyword,
                        memory_type=memory_type,
                        project_id=project_id,  # Filter by project
                        limit=max_memories // len(keywords) or 1  # Distribute the limit among keywords
                    )
                    results.extend(memories)
            else:
                memories = await MemoryRepository.search_memories(
                    query_text=keyword,
                    project_id=project_id,  # Filter by project
                    limit=max_memories // len(keywords) or 1
                )
                results.extend(memories)
        
        # Deduplicate results based on memory ID
        deduplicated = {}
        for memory in results:
            deduplicated[memory.id] = memory
            
        # Return at most max_memories memories
        return list(deduplicated.values())[:max_memories]
    
    @staticmethod
    async def get_related_context(memory_id: UUID, max_memories: int = 5) -> List[MemoryNode]:
        """
        Get related context for a given memory node.
        
        Args:
            memory_id: ID of the memory to find related contexts for
            max_memories: Maximum number of related memories to return
            
        Returns:
            List of related memory nodes
        """
        return await MemoryRepository.get_related_memories(
            memory_id=memory_id,
            limit=max_memories,
            min_confidence=0.6  # Only return reasonably confident connections
        )
    
    @staticmethod
    async def select_context_for_editor(
        code_snippet: str,
        file_path: Optional[str] = None,
        project_id: Optional[str] = None,
        max_memories: int = 10
    ) -> List[MemoryNode]:
        """
        Select relevant memories specifically for code editing context.
        This method is optimized for VSCode integration.
        
        Args:
            code_snippet: The code snippet from the editor
            file_path: Optional path of the current file
            project_id: Optional project ID to filter memories by
            max_memories: Maximum number of memories to return
            
        Returns:
            List of relevant memory nodes
        """
        # Extract potential identifiers from the code
        identifiers = ContextSelector._extract_identifiers(code_snippet)
        
        # Try to determine project from file path if not provided
        if not project_id and file_path:
            from neurodock.services.project_settings import ProjectSettings
            from neurodock.routes.mcp import ModelContextProtocolService
            
            project_path = ModelContextProtocolService._infer_project_path(file_path)
            if project_path:
                settings = ProjectSettings.load_settings(project_path)
                project_id = settings.get("project_id")
                
                # If isolation level is set to none, don't filter by project
                if settings.get("memory_isolation_level") == "none":
                    project_id = None
        
        # Get file type if available
        file_type = None
        if file_path:
            if file_path.endswith('.py'):
                file_type = 'python'
            elif file_path.endswith('.js') or file_path.endswith('.ts'):
                file_type = 'javascript'
            elif file_path.endswith('.java'):
                file_type = 'java'
            # Add more file types as needed
        
        results = []
        
        # Search for each identifier
        for identifier in identifiers[:5]:  # Limit to top 5 identifiers
            if len(identifier) < 3:
                continue
                
            # Search for memories containing this identifier
            memories = await MemoryRepository.search_memories(
                query_text=identifier,
                memory_type=MemoryType.CODE,  # Focus on code memories first
                project_id=project_id,  # Filter by project
                limit=3
            )
            results.extend(memories)
            
            # Also search for documentation if available
            doc_memories = await MemoryRepository.search_memories(
                query_text=identifier,
                memory_type=MemoryType.DOCUMENTATION,
                project_id=project_id,  # Filter by project
                limit=2
            )
            results.extend(doc_memories)
        
        # If file type is available, add memories related to the language
        if file_type:
            lang_memories = await MemoryRepository.search_memories(
                query_text=file_type,
                project_id=project_id,  # Filter by project
                limit=3
            )
            results.extend(lang_memories)
        
        # Deduplicate results
        deduplicated = {}
        for memory in results:
            deduplicated[memory.id] = memory
            
        return list(deduplicated.values())[:max_memories]
    
    @staticmethod
    def _extract_identifiers(code: str) -> List[str]:
        """
        Extract potential identifiers from code.
        """
        # Simple regex to extract variable names, function names, class names, etc.
        pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]{2,}\b'
        identifiers = re.findall(pattern, code)
        
        # Count frequency of each identifier
        frequency = {}
        for ident in identifiers:
            if ident in frequency:
                frequency[ident] += 1
            else:
                frequency[ident] = 1
        
        # Sort by frequency
        sorted_identifiers = sorted(frequency.items(), key=lambda x: x[1], reverse=True)
        
        # Return just the identifiers
        return [item[0] for item in sorted_identifiers]
