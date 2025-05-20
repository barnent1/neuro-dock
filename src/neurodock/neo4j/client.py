import os
from typing import Optional, List, Dict, Any, Union
import logging
from contextlib import asynccontextmanager

from neo4j import GraphDatabase, Driver
from neo4j.exceptions import Neo4jError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)


class Neo4jClient:
    """
    Client for Neo4j database operations.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Neo4jClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Get connection details from environment variables
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "neurodock")
        
        # Initialize driver
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # Verify connection
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 AS test")
                test_value = result.single()["test"]
                if test_value != 1:
                    raise ConnectionError("Unable to verify Neo4j connection")
                
            logger.info(f"Connected to Neo4j at {uri}")
            
            # Set up database constraints and indexes
            self._initialize_database()
            
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
        
        self._initialized = True
    
    def _initialize_database(self):
        """
        Set up initial database constraints and indexes.
        """
        with self.driver.session() as session:
            # Create constraints for memory nodes
            session.run("""
                CREATE CONSTRAINT unique_memory_id IF NOT EXISTS
                FOR (m:MemoryNode) REQUIRE m.id IS UNIQUE
            """)
            
            # Create constraints for task nodes
            session.run("""
                CREATE CONSTRAINT unique_task_id IF NOT EXISTS
                FOR (t:TaskNode) REQUIRE t.id IS UNIQUE
            """)
            
            # Create indexes
            session.run("CREATE INDEX memory_source_idx IF NOT EXISTS FOR (m:MemoryNode) ON (m.source)")
            session.run("CREATE INDEX memory_type_idx IF NOT EXISTS FOR (m:MemoryNode) ON (m.type)")
            session.run("CREATE INDEX task_status_idx IF NOT EXISTS FOR (t:TaskNode) ON (t.status)")
            session.run("CREATE INDEX task_priority_idx IF NOT EXISTS FOR (t:TaskNode) ON (t.priority)")
    
    def close(self):
        """
        Close the Neo4j driver connection.
        """
        if hasattr(self, 'driver') and self.driver is not None:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    @asynccontextmanager
    async def get_session(self):
        """
        Async context manager for Neo4j sessions.
        """
        session = self.driver.session()
        try:
            yield session
        finally:
            session.close()
    
    def get_session_sync(self):
        """
        Get a synchronous Neo4j session.
        """
        return self.driver.session()


# Singleton instance for use across the application
neo4j_client = Neo4jClient()


# Make sure to close connection when the application shuts down
def close_neo4j_connection():
    neo4j_client.close()


# Register the shutdown handler at import time
import atexit
atexit.register(close_neo4j_connection)
