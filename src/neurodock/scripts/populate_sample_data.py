"""
Sample data generator for NeuroDock's memory system.
This script populates the database with sample memories for demonstration purposes.
"""

import asyncio
import os
import random
from datetime import datetime, timedelta
from uuid import uuid4

from neurodock.models.memory import MemoryCreate, MemoryType
from neurodock.neo4j.memory_repository import MemoryRepository
from neurodock.neo4j.client import neo4j_client

# Sample memory data
SAMPLE_MEMORIES = [
    {
        "content": "Felt really energised after switching to morning workouts.",
        "type": MemoryType.IMPORTANT,
        "source": "Manual"
    },
    {
        "content": "I can still picture that first sunrise yoga session; it felt like my spirit was being rejuvenated with every pose.",
        "type": MemoryType.NORMAL,
        "source": "Claude"
    },
    {
        "content": "The moment I ran along the beach at dawn, I truly felt a deep connection to the earth and my own vitality.",
        "type": MemoryType.NORMAL,
        "source": "ChatGPT"
    },
    {
        "content": "The exhilaration I experienced after my inaugural outdoor cycling ride in the brisk morning air is something I'll never forget.",
        "type": MemoryType.IMPORTANT,
        "source": "Manual"
    },
    {
        "content": "Switching to evening hikes opened up a serene world I never knew existed, and that moment was unforgettable.",
        "type": MemoryType.NORMAL,
        "source": "ChatGPT"
    },
    {
        "content": "Joining that morning dance class was a thrilling experience that completely uplifted my week!",
        "type": MemoryType.NORMAL,
        "source": "Manual"
    },
    {
        "content": "Discovered a bug in the memory repository where it wasn't properly handling project filtering.",
        "type": MemoryType.CODE,
        "source": "Manual"
    },
    {
        "content": "The Neo4j graph database provides powerful relationship management capabilities that are perfect for our memory system.",
        "type": MemoryType.DOCUMENTATION,
        "source": "Manual"
    },
    {
        "content": "Team meeting notes: We decided to implement fulltext search for better memory retrieval with fuzzy matching.",
        "type": MemoryType.IMPORTANT,
        "source": "Manual"
    },
    {
        "content": "User feedback suggests we need a more intuitive UI for browsing memories by category.",
        "type": MemoryType.COMMENT,
        "source": "Manual"
    }
]

PROJECT_IDS = [None, "project-1", "project-2"]
SOURCES = ["Manual", "ChatGPT", "Claude"]

async def create_sample_memories(num_memories=10):
    """Create some sample memories in the database"""
    print(f"Creating {num_memories} sample memories...")
    
    # Create memories from the sample list first
    for i, sample in enumerate(SAMPLE_MEMORIES):
        if i >= num_memories:
            break
            
        # Add a random timestamp within the last week
        days_ago = random.randint(0, 7)
        hours_ago = random.randint(0, 23)
        
        memory = MemoryCreate(
            content=sample["content"],
            type=sample["type"],
            source=sample["source"],
            project_id=random.choice(PROJECT_IDS)
        )
        
        await MemoryRepository.create_memory(memory)
    
    # If we need more memories, generate random ones
    if num_memories > len(SAMPLE_MEMORIES):
        for i in range(len(SAMPLE_MEMORIES), num_memories):
            memory_type = random.choice(list(MemoryType))
            source = random.choice(SOURCES)
            
            content = f"Sample memory #{i} of type {memory_type} from {source}"
            
            memory = MemoryCreate(
                content=content,
                type=memory_type,
                source=source,
                project_id=random.choice(PROJECT_IDS)
            )
            
            await MemoryRepository.create_memory(memory)
    
    print("Sample memories created successfully!")

if __name__ == "__main__":
    import sys
    num_memories = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    
    try:
        asyncio.run(create_sample_memories(num_memories))
    except Exception as e:
        print(f"Error creating sample memories: {e}")
    finally:
        # Close the Neo4j connection
        neo4j_client.close()
