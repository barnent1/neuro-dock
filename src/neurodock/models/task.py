from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from uuid import UUID, uuid4
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskPriority(int, Enum):
    LOW = 1
    MEDIUM = 3
    HIGH = 5
    CRITICAL = 8


class TaskComplexity(str, Enum):
    TRIVIAL = "trivial"      # < 50 lines
    SIMPLE = "simple"        # 50-200 lines
    MODERATE = "moderate"    # 200-500 lines
    COMPLEX = "complex"      # > 500 lines, needs breakdown
    
class TaskType(str, Enum):
    FEATURE = "feature"
    BUG = "bug"
    REFACTOR = "refactor"
    DOCUMENTATION = "documentation"
    TEST = "test"
    INFRASTRUCTURE = "infrastructure"

class TaskNode(BaseModel):
    """
    Represents a task node in the graph database.
    Tasks are automatically broken down if they exceed 500 lines of code
    or if their estimated time exceeds 4 hours.
    """
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    weight: int = Field(default=3, ge=1, le=10)  # Complexity/effort weight (1-10)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    parent_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    assigned_to: Optional[str] = None
    
    # New fields for enhanced task management
    estimated_hours: float = Field(default=1.0, ge=0.0)  # Estimated time in hours
    actual_hours: Optional[float] = None  # Actual time spent
    complexity: TaskComplexity = TaskComplexity.MODERATE
    task_type: TaskType = TaskType.FEATURE
    estimated_loc: Optional[int] = None  # Estimated Lines of Code
    requires_breakdown: bool = Field(default=False)  # Auto-set based on complexity
    subtasks: List[UUID] = Field(default_factory=list)  # IDs of subtasks
    dependencies: List[UUID] = Field(default_factory=list)  # Tasks that must be completed first
    skills_required: List[str] = Field(default_factory=list)  # Required skills for the task
    
    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    """
    Schema for creating a new task.
    Tasks will be automatically analyzed and broken down if they exceed complexity thresholds.
    """
    title: str
    description: str
    priority: TaskPriority = TaskPriority.MEDIUM
    task_type: TaskType = TaskType.FEATURE
    estimated_hours: Optional[float] = None  # If not provided, will be estimated
    estimated_loc: Optional[int] = None  # If not provided, will be estimated
    skills_required: List[str] = Field(default_factory=list)
    dependencies: List[UUID] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    assigned_to: Optional[str] = None
    parent_id: Optional[UUID] = None  # For manually creating subtasks

    @field_validator("weight")
    def validate_weight(cls, v: int) -> int:
        if v < 1 or v > 10:
            raise ValueError("Weight must be between 1 and 10")
        return v


class TaskUpdate(BaseModel):
    """
    Schema for updating an existing task.
    """
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    weight: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    assigned_to: Optional[str] = None
    
    @field_validator("weight")
    def validate_weight(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1 or v > 10):
            raise ValueError("Weight must be between 1 and 10")
        return v


class TaskEvent(BaseModel):
    """
    Represents an event in the task's lifecycle.
    """
    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    event_type: str  # e.g. "status_changed", "priority_changed", "comment_added"
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Any] = Field(default_factory=dict)
    user: Optional[str] = None  # Who initiated the event (could be agent or user)
    
    class Config:
        from_attributes = True


class AgentAction(BaseModel):
    """
    Represents an action taken by an agent.
    """
    id: UUID = Field(default_factory=uuid4)
    task_id: Optional[UUID] = None
    action_type: str  # e.g. "subtask_creation", "status_update", "research"
    timestamp: datetime = Field(default_factory=datetime.now)
    description: str
    reasoning: str
    result: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


class TaskRelationship(BaseModel):
    """
    Represents a relationship between tasks.
    """
    id: UUID = Field(default_factory=uuid4)
    from_task_id: UUID
    to_task_id: UUID
    relationship_type: str  # e.g., "subtask", "blocks", "depends_on"
    
    class Config:
        from_attributes = True
