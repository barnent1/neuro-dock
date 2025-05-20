import logging
from typing import List, Dict, Optional, Any, Union
from uuid import UUID, uuid4
from datetime import datetime

from neo4j import Record

from neurodock.models.task import (
    TaskNode, TaskCreate, TaskUpdate, TaskStatus, 
    TaskPriority, TaskEvent, TaskRelationship
)
from neurodock.neo4j.client import neo4j_client


class TaskRepository:
    logger = logging.getLogger("neurodock.task_repository")
    """
    Repository for task-related operations in Neo4j.
    """
    
    @staticmethod
    async def create_task(task: TaskCreate) -> TaskNode:
        """
        Create a new task node in the database.
        """
        task_id = uuid4()
        now = datetime.now()
        
        query = """
        CREATE (t:TaskNode {
            id: $id,
            title: $title,
            description: $description,
            status: $status,
            priority: $priority,
            weight: $weight,
            created_at: $created_at,
            updated_at: $updated_at,
            parent_id: $parent_id,
            metadata: $metadata,
            assigned_to: $assigned_to
        })
        RETURN t
        """
        
        params = {
            "id": str(task_id),
            "title": task.title,
            "description": task.description,
            "status": TaskStatus.PENDING.value,
            "priority": task.priority.value,
            "weight": task.weight,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "parent_id": str(task.parent_id) if task.parent_id else None,
            "metadata": task.metadata,
            "assigned_to": task.assigned_to
        }
        
        try:
            async with neo4j_client.get_session() as session:
                result = await session.run(query, params)
                record = await result.single()
                if not record:
                    TaskRepository.logger.error("Failed to create task: no record returned from Neo4j.")
                    raise Exception("Failed to create task node.")
                node_data = record["t"]
                # If there's a parent ID, create a relationship
                if task.parent_id:
                    rel_query = """
                    MATCH (parent:TaskNode {id: $parent_id})
                    MATCH (child:TaskNode {id: $child_id})
                    CREATE (parent)-[r:HAS_SUBTASK]->(child)
                    """
                    await session.run(rel_query, {
                        "parent_id": str(task.parent_id),
                        "child_id": str(task_id)
                    })
                # Create a task event for the creation
                event_query = """
                CREATE (e:TaskEvent {
                    id: $id,
                    task_id: $task_id,
                    event_type: $event_type,
                    timestamp: $timestamp,
                    data: $data,
                    user: $user
                })
                """
                await session.run(event_query, {
                    "id": str(uuid4()),
                    "task_id": str(task_id),
                    "event_type": "task_created",
                    "timestamp": now.isoformat(),
                    "data": {},
                    "user": task.assigned_to or "system"
                })
                return TaskNode(
                    id=UUID(node_data["id"]),
                    title=node_data["title"],
                    description=node_data["description"],
                    status=TaskStatus(node_data["status"]),
                    priority=TaskPriority(node_data["priority"]),
                    weight=node_data["weight"],
                    created_at=datetime.fromisoformat(node_data["created_at"]),
                    updated_at=datetime.fromisoformat(node_data["updated_at"]),
                    completed_at=None,
                    parent_id=UUID(node_data["parent_id"]) if node_data.get("parent_id") else None,
                    metadata=node_data["metadata"],
                    assigned_to=node_data.get("assigned_to")
                )
        except Exception as e:
            TaskRepository.logger.exception(f"Error creating task: {e}")
            raise
    
    @staticmethod
    async def get_task_by_id(task_id: UUID) -> Optional[TaskNode]:
        """
        Get a task node by its ID.
        """
        query = """
        MATCH (t:TaskNode {id: $id})
        RETURN t
        """
        
        params = {"id": str(task_id)}
        
        try:
            async with neo4j_client.get_session() as session:
                result = await session.run(query, params)
                record = await result.single()
                if not record:
                    TaskRepository.logger.warning(f"Task with id {task_id} not found.")
                    return None
                node_data = record["t"]
                return TaskNode(
                    id=UUID(node_data["id"]),
                    title=node_data["title"],
                    description=node_data["description"],
                    status=TaskStatus(node_data["status"]),
                    priority=TaskPriority(node_data["priority"]),
                    weight=node_data["weight"],
                    created_at=datetime.fromisoformat(node_data["created_at"]),
                    updated_at=datetime.fromisoformat(node_data["updated_at"]),
                    completed_at=datetime.fromisoformat(node_data["completed_at"]) if node_data.get("completed_at") else None,
                    parent_id=UUID(node_data["parent_id"]) if node_data.get("parent_id") else None,
                    metadata=node_data["metadata"],
                    assigned_to=node_data.get("assigned_to")
                )
        except Exception as e:
            TaskRepository.logger.exception(f"Error getting task by id {task_id}: {e}")
            raise
    
    @staticmethod
    async def update_task(task_id: UUID, task_update: TaskUpdate) -> Optional[TaskNode]:
        """
        Update a task node.
        """
        # First, get the current task to determine if status needs updating
        current_task = await TaskRepository.get_task_by_id(task_id)
        if not current_task:
            return None
        
        # Check if we need to update the status and potentially set completed_at
        update_completed_at = False
        if task_update.status == TaskStatus.COMPLETED and current_task.status != TaskStatus.COMPLETED:
            update_completed_at = True
        
        # Build dynamic update query based on provided fields
        set_clauses = []
        params = {"id": str(task_id), "updated_at": datetime.now().isoformat()}
        
        if task_update.title is not None:
            set_clauses.append("t.title = $title")
            params["title"] = task_update.title
        
        if task_update.description is not None:
            set_clauses.append("t.description = $description")
            params["description"] = task_update.description
        
        if task_update.status is not None:
            set_clauses.append("t.status = $status")
            params["status"] = task_update.status.value
        
        if task_update.priority is not None:
            set_clauses.append("t.priority = $priority")
            params["priority"] = task_update.priority.value
        
        if task_update.weight is not None:
            set_clauses.append("t.weight = $weight")
            params["weight"] = task_update.weight
        
        if task_update.metadata is not None:
            set_clauses.append("t.metadata = $metadata")
            params["metadata"] = task_update.metadata
        
        if task_update.assigned_to is not None:
            set_clauses.append("t.assigned_to = $assigned_to")
            params["assigned_to"] = task_update.assigned_to
        
        # Always update the updated_at field
        set_clauses.append("t.updated_at = $updated_at")
        
        # Handle completed_at if needed
        if update_completed_at:
            set_clauses.append("t.completed_at = $completed_at")
            params["completed_at"] = params["updated_at"]
        
        # Build and execute the query
        set_query = ", ".join(set_clauses)
        query = f"""
        MATCH (t:TaskNode {{id: $id}})
        SET {set_query}
        RETURN t
        """
        
        try:
            async with neo4j_client.get_session() as session:
                result = await session.run(query, params)
                record = await result.single()
                if not record:
                    TaskRepository.logger.warning(f"Task with id {task_id} not found for update.")
                    return None
                # Create a task event for the update
                event_query = """
                CREATE (e:TaskEvent {
                    id: $id,
                    task_id: $task_id,
                    event_type: $event_type,
                    timestamp: $timestamp,
                    data: $data,
                    user: $user
                })
                """
                event_data = {k: v for k, v in task_update.model_dump().items() if v is not None}
                await session.run(event_query, {
                    "id": str(uuid4()),
                    "task_id": str(task_id),
                    "event_type": "task_updated",
                    "timestamp": params["updated_at"],
                    "data": event_data,
                    "user": task_update.assigned_to or current_task.assigned_to or "system"
                })
                node_data = record["t"]
                return TaskNode(
                    id=UUID(node_data["id"]),
                    title=node_data["title"],
                    description=node_data["description"],
                    status=TaskStatus(node_data["status"]),
                    priority=TaskPriority(node_data["priority"]),
                    weight=node_data["weight"],
                    created_at=datetime.fromisoformat(node_data["created_at"]),
                    updated_at=datetime.fromisoformat(node_data["updated_at"]),
                    completed_at=datetime.fromisoformat(node_data["completed_at"]) if node_data.get("completed_at") else None,
                    parent_id=UUID(node_data["parent_id"]) if node_data.get("parent_id") else None,
                    metadata=node_data["metadata"],
                    assigned_to=node_data.get("assigned_to")
                )
        except Exception as e:
            TaskRepository.logger.exception(f"Error updating task {task_id}: {e}")
            raise
    
    @staticmethod
    async def create_task_relationship(relationship: TaskRelationship) -> TaskRelationship:
        """
        Create a relationship between two task nodes.
        """
        rel_id = uuid4() if not relationship.id else relationship.id
        
        # Define the relationship type mapping
        rel_types = {
            "subtask": "HAS_SUBTASK",
            "blocks": "BLOCKS",
            "depends_on": "DEPENDS_ON",
            "related": "RELATED_TO"
        }
        
        # Get the Neo4j relationship type
        neo4j_rel_type = rel_types.get(relationship.relationship_type, "RELATED_TO")
        
        query = f"""
        MATCH (from:TaskNode {{id: $from_id}})
        MATCH (to:TaskNode {{id: $to_id}})
        CREATE (from)-[r:{neo4j_rel_type} {{id: $id}}]->(to)
        RETURN r
        """
        
        params = {
            "id": str(rel_id),
            "from_id": str(relationship.from_task_id),
            "to_id": str(relationship.to_task_id)
        }
        
        try:
            async with neo4j_client.get_session() as session:
                result = await session.run(query, params)
                record = await result.single()
                if not record:
                    TaskRepository.logger.error(f"Failed to create task relationship: {relationship}")
                    raise ValueError("Failed to create task relationship")
                return TaskRelationship(
                    id=rel_id,
                    from_task_id=relationship.from_task_id,
                    to_task_id=relationship.to_task_id,
                    relationship_type=relationship.relationship_type
                )
        except Exception as e:
            TaskRepository.logger.exception(f"Error creating task relationship: {e}")
            raise
    
    @staticmethod
    async def get_task_events(task_id: UUID, limit: int = 100) -> List[TaskEvent]:
        """
        Get events for a specific task.
        """
        query = """
        MATCH (e:TaskEvent)
        WHERE e.task_id = $task_id
        RETURN e
        ORDER BY e.timestamp DESC
        LIMIT $limit
        """
        
        params = {
            "task_id": str(task_id),
            "limit": limit
        }
        
        try:
            async with neo4j_client.get_session() as session:
                result = await session.run(query, params)
                events = []
                async for record in result:
                    event_data = record["e"]
                    events.append(
                        TaskEvent(
                            id=UUID(event_data["id"]),
                            task_id=UUID(event_data["task_id"]),
                            event_type=event_data["event_type"],
                            timestamp=datetime.fromisoformat(event_data["timestamp"]),
                            data=event_data["data"],
                            user=event_data.get("user")
                        )
                    )
                return events
        except Exception as e:
            TaskRepository.logger.exception(f"Error getting task events for {task_id}: {e}")
            raise
    
    @staticmethod
    async def get_subtasks(task_id: UUID) -> List[TaskNode]:
        """
        Get all subtasks for a given task.
        """
        query = """
        MATCH (parent:TaskNode {id: $parent_id})-[:HAS_SUBTASK]->(child:TaskNode)
        RETURN child
        ORDER BY child.priority DESC, child.created_at ASC
        """
        
        params = {"parent_id": str(task_id)}
        
        try:
            async with neo4j_client.get_session() as session:
                result = await session.run(query, params)
                subtasks = []
                async for record in result:
                    node_data = record["child"]
                    subtasks.append(
                        TaskNode(
                            id=UUID(node_data["id"]),
                            title=node_data["title"],
                            description=node_data["description"],
                            status=TaskStatus(node_data["status"]),
                            priority=TaskPriority(node_data["priority"]),
                            weight=node_data["weight"],
                            created_at=datetime.fromisoformat(node_data["created_at"]),
                            updated_at=datetime.fromisoformat(node_data["updated_at"]),
                            completed_at=datetime.fromisoformat(node_data["completed_at"]) if node_data.get("completed_at") else None,
                            parent_id=UUID(task_id),
                            metadata=node_data["metadata"],
                            assigned_to=node_data.get("assigned_to")
                        )
                    )
                return subtasks
        except Exception as e:
            TaskRepository.logger.exception(f"Error getting subtasks for {task_id}: {e}")
            raise
    
    @staticmethod
    async def get_pending_tasks(limit: int = 10) -> List[TaskNode]:
        """
        Get pending tasks ordered by priority.
        """
        query = """
        MATCH (t:TaskNode)
        WHERE t.status = $status
        RETURN t
        ORDER BY t.priority DESC, t.created_at ASC
        LIMIT $limit
        """
        
        params = {
            "status": TaskStatus.PENDING.value,
            "limit": limit
        }
        
        try:
            async with neo4j_client.get_session() as session:
                result = await session.run(query, params)
                tasks = []
                async for record in result:
                    node_data = record["t"]
                    tasks.append(
                        TaskNode(
                            id=UUID(node_data["id"]),
                            title=node_data["title"],
                            description=node_data["description"],
                            status=TaskStatus(node_data["status"]),
                            priority=TaskPriority(node_data["priority"]),
                            weight=node_data["weight"],
                            created_at=datetime.fromisoformat(node_data["created_at"]),
                            updated_at=datetime.fromisoformat(node_data["updated_at"]),
                            completed_at=datetime.fromisoformat(node_data["completed_at"]) if node_data.get("completed_at") else None,
                            parent_id=UUID(node_data["parent_id"]) if node_data.get("parent_id") else None,
                            metadata=node_data["metadata"],
                            assigned_to=node_data.get("assigned_to")
                        )
                    )
                return tasks
        except Exception as e:
            TaskRepository.logger.exception(f"Error getting pending tasks: {e}")
            raise
    
    @staticmethod
    async def delete_project_tasks(project_id: str) -> bool:
        """
        Delete all tasks for a specific project.
        
        Args:
            project_id: The project ID to delete tasks for
            
        Returns:
            bool: True if tasks were deleted, False otherwise
        """
        query = """
        MATCH (t:TaskNode {project_id: $project_id})
        WITH t
        DETACH DELETE t
        RETURN count(t) as deleted_count
        """
        
        params = {"project_id": project_id}
        
        try:
            async with neo4j_client.get_session() as session:
                result = await session.run(query, params)
                record = await result.single()
                if not record:
                    TaskRepository.logger.warning(f"No tasks found to delete for project {project_id}.")
                    return False
                return record["deleted_count"] > 0
        except Exception as e:
            TaskRepository.logger.exception(f"Error deleting project tasks for {project_id}: {e}")
            raise
        
