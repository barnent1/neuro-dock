import pytest
from unittest.mock import AsyncMock, patch
import uuid
from datetime import datetime

from neurodock.models.memory import MemoryNode, MemoryCreate, MemoryType, MemoryEdge
from neurodock.neo4j.memory_repository import MemoryRepository

# Mock the Neo4j client module before importing
with patch("neurodock.neo4j.client.Neo4jClient") as mock_client:
    mock_client.return_value = AsyncMock()
    mock_client.return_value.get_session = AsyncMock()


@pytest.fixture
def mock_neo4j_session():
    """Mock Neo4j session for testing"""
    session = AsyncMock()
    
    # Set up the record return values
    mock_record = AsyncMock()
    mock_record.__getitem__.return_value = {
        "id": str(uuid.uuid4()),
        "content": "Test memory content",
        "type": MemoryType.NORMAL.value,
        "timestamp": datetime.now().isoformat(),
        "source": "test"
    }
    
    # Configure the session's run method to return a result with single method
    mock_result = AsyncMock()
    mock_result.single.return_value = mock_record
    session.run.return_value = mock_result
    
    return session


@pytest.mark.asyncio
async def test_create_memory(mock_neo4j_session):
    """Test creating a memory node"""
    # Create a memory object
    memory = MemoryCreate(
        content="Test memory content",
        type=MemoryType.NORMAL,
        source="test"
    )
    
    # Mock get_session
    with patch("neurodock.neo4j.client.neo4j_client.get_session") as mock_get_session:
        # Mock the context manager to return our mock session
        mock_get_session.return_value.__aenter__.return_value = mock_neo4j_session
        
        # Call the function being tested
        result = await MemoryRepository.create_memory(memory)
        
        # Assert that the result is a MemoryNode
        assert isinstance(result, MemoryNode)
        assert result.content == "Test memory content"
        assert result.type == MemoryType.NORMAL
        assert result.source == "test"
        
        # Verify that run was called with the correct parameters
        mock_neo4j_session.run.assert_called_once()
        args, kwargs = mock_neo4j_session.run.call_args
        
        # Assert the query contains the expected CREATE statement
        assert "CREATE (m:MemoryNode" in args[0]
        
        # Assert the parameters contain the expected values
        assert kwargs["content"] == "Test memory content"
        assert kwargs["type"] == MemoryType.NORMAL.value
        assert kwargs["source"] == "test"


@pytest.mark.asyncio
async def test_get_memory_by_id(mock_neo4j_session):
    """Test retrieving a memory by ID"""
    memory_id = uuid.uuid4()
    
    # Mock get_session
    with patch("neurodock.neo4j.client.neo4j_client.get_session") as mock_get_session:
        # Mock the context manager to return our mock session
        mock_get_session.return_value.__aenter__.return_value = mock_neo4j_session
        
        # Call the function being tested
        result = await MemoryRepository.get_memory_by_id(memory_id)
        
        # Assert that the result is a MemoryNode
        assert isinstance(result, MemoryNode)
        
        # Verify that run was called with the correct parameters
        mock_neo4j_session.run.assert_called_once()
        args, kwargs = mock_neo4j_session.run.call_args
        
        # Assert the query contains the expected MATCH statement
        assert "MATCH (m:MemoryNode {id: $id})" in args[0]
        
        # Assert the parameters contain the expected values
        assert kwargs["id"] == str(memory_id)


@pytest.mark.asyncio
async def test_create_memory_relationship(mock_neo4j_session):
    """Test creating a relationship between memory nodes"""
    # Create a memory edge
    edge = MemoryEdge(
        label="RELATED",
        from_id=uuid.uuid4(),
        to_id=uuid.uuid4(),
        confidence=0.85
    )
    
    # Mock get_session
    with patch("neurodock.neo4j.client.neo4j_client.get_session") as mock_get_session:
        # Mock the context manager to return our mock session
        mock_get_session.return_value.__aenter__.return_value = mock_neo4j_session
        
        # Configure mock_record to return relationship data
        mock_record = mock_neo4j_session.run.return_value.single.return_value
        mock_record.__getitem__.return_value = {
            "id": str(uuid.uuid4()),
            "label": "RELATED",
            "confidence": 0.85
        }
        
        # Call the function being tested
        result = await MemoryRepository.create_memory_relationship(edge)
        
        # Assert that the result is a MemoryEdge
        assert isinstance(result, MemoryEdge)
        assert result.label == "RELATED"
        assert result.confidence == 0.85
        
        # Verify that run was called with the correct parameters
        mock_neo4j_session.run.assert_called_once()
        args, kwargs = mock_neo4j_session.run.call_args
        
        # Assert the query contains the expected CREATE statement for relationship
        assert "CREATE (from)-[r:RELATED" in args[0]
        
        # Assert the parameters contain the expected values
        assert kwargs["from_id"] == str(edge.from_id)
        assert kwargs["to_id"] == str(edge.to_id)
        assert kwargs["confidence"] == 0.85
