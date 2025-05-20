from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class MemoryType(str, Enum):
    IMPORTANT = "important"
    NORMAL = "normal"
    TRIVIAL = "trivial"
    CODE = "code"
    COMMENT = "comment"
    DOCUMENTATION = "documentation"


class MemoryNode(BaseModel):
    """
    Represents a memory node in the graph database.
    Each memory node contains content, a type, and a source.
    """
    id: UUID = Field(default_factory=uuid4)
    content: str
    type: MemoryType
    timestamp: datetime = Field(default_factory=datetime.now)
    source: str
    project_id: Optional[str] = None  # Project identifier to isolate memories
    
    class Config:
        from_attributes = True


class MemoryEdge(BaseModel):
    """
    Represents an edge between two memory nodes.
    """
    id: UUID = Field(default_factory=uuid4)
    label: str
    from_id: UUID
    to_id: UUID
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    
    class Config:
        from_attributes = True


class MemoryCreate(BaseModel):
    """
    Schema for creating a new memory node.
    """
    content: str
    type: MemoryType
    source: str
    project_id: Optional[str] = None  # Project identifier


class MemoryEdgeCreate(BaseModel):
    """
    Schema for creating a new edge between memory nodes.
    """
    label: str
    from_id: UUID
    to_id: UUID
    confidence: float = 1.0
    
    @field_validator("confidence")
    def validate_confidence(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return v
