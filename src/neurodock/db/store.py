#!/usr/bin/env python3

"""
Database store operations for NeuroDock PostgreSQL backend.
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import warnings
from .schema import get_db_connection, initialize_schema

class DatabaseStore:
    """Database operations for NeuroDock."""
    
    def __init__(self, project_path: Optional[str] = None):
        """Initialize with project path for namespacing."""
        self.project_path = project_path or str(Path.cwd())
        
        # Ensure schema is initialized - this will raise if database not available
        initialize_schema()
    
    # Task operations
    def add_task(self, title: str, description: str, complexity: str = None, 
                 dependencies: List[str] = None, parent_id: str = None) -> str:
        """Add a new task and return its ID."""
        conn = get_db_connection()  # This will raise if no connection
        
        try:
            with conn.cursor() as cur:
                task_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO tasks (id, title, description, complexity, dependencies, parent_id, project_path)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (task_id, title, description, complexity, dependencies or [], parent_id, self.project_path))
                
                result = cur.fetchone()
                conn.commit()
                return str(result['id']) if result else task_id
                
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to add task: {str(e)}")
        finally:
            conn.close()
    
    def get_tasks(self, status: str = None) -> List[Dict[str, Any]]:
        """Get tasks, optionally filtered by status."""
        conn = get_db_connection()  # This will raise if no connection
        
        try:
            with conn.cursor() as cur:
                if status:
                    cur.execute("""
                        SELECT * FROM tasks 
                        WHERE project_path = %s AND status = %s
                        ORDER BY created_at;
                    """, (self.project_path, status))
                else:
                    cur.execute("""
                        SELECT * FROM tasks 
                        WHERE project_path = %s
                        ORDER BY created_at;
                    """, (self.project_path,))
                
                return [dict(row) for row in cur.fetchall()]
                
        except Exception as e:
            # Graceful degradation - failed to get tasks
            return []
        finally:
            conn.close()
    
    def mark_task_done(self, task_id: str) -> bool:
        """Mark a task as completed."""
        conn = get_db_connection()  # This will raise if no connection  # This will raise if no connection
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE tasks 
                    SET status = 'completed', completed_at = now()
                    WHERE id = %s AND project_path = %s;
                """, (task_id, self.project_path))
                
                conn.commit()
                return cur.rowcount > 0
                
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to mark task done: {str(e)}")
        finally:
            conn.close()
    
    def update_task_status(self, task_id: str, status: str) -> bool:
        """Update task status."""
        conn = get_db_connection()  # This will raise if no connection  # This will raise if no connection
        
        try:
            with conn.cursor() as cur:
                if status == 'completed':
                    cur.execute("""
                        UPDATE tasks 
                        SET status = %s, completed_at = now()
                        WHERE id = %s AND project_path = %s;
                    """, (status, task_id, self.project_path))
                else:
                    cur.execute("""
                        UPDATE tasks 
                        SET status = %s
                        WHERE id = %s AND project_path = %s;
                    """, (status, task_id, self.project_path))
                
                conn.commit()
                return cur.rowcount > 0
                
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to update task status: {str(e)}")
        finally:
            conn.close()
    
    def update_task_status_by_name(self, task_name: str, status: str) -> bool:
        """Update task status by task name (for YAML task plan compatibility)."""
        conn = get_db_connection()  # This will raise if no connection
        if not conn:
            return False
        
        try:
            with conn.cursor() as cur:
                if status == 'completed':
                    cur.execute("""
                        UPDATE tasks 
                        SET status = %s, completed_at = now()
                        WHERE title = %s AND project_path = %s;
                    """, (status, task_name, self.project_path))
                else:
                    cur.execute("""
                        UPDATE tasks 
                        SET status = %s
                        WHERE title = %s AND project_path = %s;
                    """, (status, task_name, self.project_path))
                
                conn.commit()
                return cur.rowcount > 0
                
        except Exception as e:
            # Graceful degradation - failed to update task status by name
            conn.rollback()
            return False
        finally:
            conn.close()

    # Memory operations
    def add_memory(self, text: str, memory_type: str) -> Optional[str]:
        """Add memory entry and return its ID."""
        conn = get_db_connection()  # This will raise if no connection
        if not conn:
            return None
        
        try:
            with conn.cursor() as cur:
                memory_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO memory (id, type, text, project_path)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id;
                """, (memory_id, memory_type, text, self.project_path))
                
                result = cur.fetchone()
                conn.commit()
                return str(result['id']) if result else memory_id
                
        except Exception as e:
            # Graceful degradation - failed to add memory
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def get_memory_by_type(self, memory_type: str) -> List[Dict[str, Any]]:
        """Get memory entries by type."""
        conn = get_db_connection()  # This will raise if no connection
        if not conn:
            return []
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM memory 
                    WHERE project_path = %s AND type = %s
                    ORDER BY created_at DESC;
                """, (self.project_path, memory_type))
                
                return [dict(row) for row in cur.fetchall()]
                
        except Exception as e:
            # Graceful degradation - failed to get memory
            return []
        finally:
            conn.close()
    
    def get_latest_memory(self, memory_type: str) -> Optional[Dict[str, Any]]:
        """Get the most recent memory entry of a specific type."""
        memories = self.get_memory_by_type(memory_type)
        return memories[0] if memories else None
    
    def get_all_memories(self) -> List[Dict[str, Any]]:
        """Get all memory entries for this project."""
        conn = get_db_connection()
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM memory 
                    WHERE project_path = %s
                    ORDER BY created_at DESC;
                """, (self.project_path,))
                
                return [dict(row) for row in cur.fetchall()]
        except Exception:
            # Graceful degradation - failed to get memories
            return []
        finally:
            conn.close()
    
    # Discussion operations
    def add_discussion_turn(self, role: str, message: str, turn_index: int) -> Optional[str]:
        """Add a discussion turn and return its ID."""
        conn = get_db_connection()  # This will raise if no connection
        if not conn:
            return None
        
        try:
            with conn.cursor() as cur:
                discussion_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO discussion (id, role, message, turn_index, project_path)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id;
                """, (discussion_id, role, message, turn_index, self.project_path))
                
                result = cur.fetchone()
                conn.commit()
                return str(result['id']) if result else discussion_id
                
        except Exception as e:
            # Graceful degradation - failed to add discussion turn
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def get_discussion_history(self) -> List[Dict[str, Any]]:
        """Get full discussion history for the project."""
        conn = get_db_connection()  # This will raise if no connection
        if not conn:
            return []
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM discussion 
                    WHERE project_path = %s
                    ORDER BY turn_index;
                """, (self.project_path,))
                
                return [dict(row) for row in cur.fetchall()]
                
        except Exception as e:
            # Graceful degradation - failed to get discussion history
            return []
        finally:
            conn.close()
    
    def save_discussion_history(self, discussion_history: List[Dict]) -> bool:
        """Save discussion history to database."""
        if not discussion_history:
            return True
            
        conn = get_db_connection()  # This will raise if no connection
        if not conn:
            return False
        
        try:
            with conn.cursor() as cur:
                # Clear existing discussion history for this project
                cur.execute("DELETE FROM discussion WHERE project_path = %s;", (self.project_path,))
                
                # Save new discussion history
                for i, turn in enumerate(discussion_history):
                    discussion_id = str(uuid.uuid4())
                    role = turn.get('role', 'unknown')
                    message = turn.get('message', '')
                    
                    cur.execute("""
                        INSERT INTO discussion (id, role, message, turn_index, project_path)
                        VALUES (%s, %s, %s, %s, %s);
                    """, (discussion_id, role, message, i, self.project_path))
                
                conn.commit()
                return True
                
        except Exception as e:
            # Graceful degradation - failed to save discussion history
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def log_task_execution(self, task_name: str, description: str, files_created: List[str], status: str = 'completed') -> bool:
        """Log task execution details."""
        conn = get_db_connection()  # This will raise if no connection
        if not conn:
            return False
        
        try:
            with conn.cursor() as cur:
                # Create a task execution record in memory table
                memory_id = str(uuid.uuid4())
                log_content = f"Task '{task_name}' executed successfully.\nDescription: {description}\nFiles created: {len(files_created)}\n"
                log_content += "\n".join(f"- {file}" for file in files_created)
                
                cur.execute("""
                    INSERT INTO memory (id, text, memory_type, metadata, project_path)
                    VALUES (%s, %s, %s, %s, %s);
                """, (
                    memory_id, 
                    log_content, 
                    'task_execution',
                    {'task_name': task_name, 'status': status, 'files_count': len(files_created)},
                    self.project_path
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            # Graceful degradation - failed to log task execution
            conn.rollback()
            return False
        finally:
            conn.close()
    
    # Task plan operations
    def save_task_plan(self, task_plan) -> bool:
        """Save task plan to database."""
        conn = get_db_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cur:
                # Clear existing task plan for this project
                cur.execute("DELETE FROM memory WHERE project_path = %s AND type = 'task_plan';", (self.project_path,))
                
                # Save new task plan
                memory_id = str(uuid.uuid4())
                
                # Handle both dict and string inputs
                if isinstance(task_plan, dict):
                    import json
                    task_plan_text = json.dumps(task_plan)
                else:
                    task_plan_text = str(task_plan)
                
                cur.execute("""
                    INSERT INTO memory (id, type, text, project_path)
                    VALUES (%s, %s, %s, %s);
                """, (memory_id, 'task_plan', task_plan_text, self.project_path))
                
                conn.commit()
                return True
                
        except Exception as e:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_task_plan(self) -> Optional[Dict[str, Any]]:
        """Get task plan from database."""
        conn = get_db_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT text FROM memory 
                    WHERE project_path = %s AND type = 'task_plan'
                    ORDER BY created_at DESC
                    LIMIT 1;
                """, (self.project_path,))
                
                result = cur.fetchone()
                if result:
                    import json
                    import yaml
                    text = result['text']
                    
                    # Try JSON first, then YAML
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        try:
                            return yaml.safe_load(text)
                        except yaml.YAMLError:
                            return None
                return None
                
        except Exception as e:
            return None
        finally:
            conn.close()

    # Utility methods
    def clear_project_data(self) -> bool:
        """Clear all data for the current project (useful for testing)."""
        conn = get_db_connection()  # This will raise if no connection
        if not conn:
            return False
        
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM tasks WHERE project_path = %s;", (self.project_path,))
                cur.execute("DELETE FROM memory WHERE project_path = %s;", (self.project_path,))
                cur.execute("DELETE FROM discussion WHERE project_path = %s;", (self.project_path,))
                
                conn.commit()
                return True
                
        except Exception as e:
            # Graceful degradation - failed to clear project data
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_project_stats(self) -> Dict[str, int]:
        """Get project statistics."""
        conn = get_db_connection()  # This will raise if no connection
        if not conn:
            return {"tasks": 0, "memories": 0, "discussions": 0}
        
        try:
            with conn.cursor() as cur:
                # Count tasks
                cur.execute("SELECT COUNT(*) as count FROM tasks WHERE project_path = %s;", (self.project_path,))
                task_count = cur.fetchone()['count']
                
                # Count memories
                cur.execute("SELECT COUNT(*) as count FROM memory WHERE project_path = %s;", (self.project_path,))
                memory_count = cur.fetchone()['count']
                
                # Count discussions
                cur.execute("SELECT COUNT(*) as count FROM discussion WHERE project_path = %s;", (self.project_path,))
                discussion_count = cur.fetchone()['count']
                
                return {
                    "tasks": task_count,
                    "memories": memory_count,
                    "discussions": discussion_count
                }
                
        except Exception as e:
            # Graceful degradation - failed to get project stats
            return {"tasks": 0, "memories": 0, "discussions": 0}
        finally:
            conn.close()

# Convenience functions for global use
def get_store(project_path: Optional[str] = None) -> DatabaseStore:
    """Get a database store instance."""
    return DatabaseStore(project_path)

def test_database():
    """Test database functionality."""
    from .schema import test_database_connection
    
    if not test_database_connection():
        print("❌ Database connection test failed")
        return False
    
    # Test basic operations
    store = get_store("/tmp/test_project")
    
    try:
        # Test task operations
        task_id = store.add_task("Test Task", "Test Description", "simple")
        if not task_id:
            print("❌ Failed to add task")
            return False
        
        tasks = store.get_tasks()
        if not tasks:
            print("❌ Failed to retrieve tasks")
            return False
        
        success = store.mark_task_done(task_id)
        if not success:
            print("❌ Failed to mark task done")
            return False
        
        # Test memory operations
        memory_id = store.add_memory("Test memory content", "test_type")
        if not memory_id:
            print("❌ Failed to add memory")
            return False
        
        memories = store.get_memory_by_type("test_type")
        if not memories:
            print("❌ Failed to retrieve memories")
            return False
        
        # Test discussion operations
        discussion_id = store.add_discussion_turn("user", "Test message", 1)
        if not discussion_id:
            print("❌ Failed to add discussion turn")
            return False
        
        history = store.get_discussion_history()
        if not history:
            print("❌ Failed to retrieve discussion history")
            return False
        
        # Test task plan operations
        task_plan = {"version": 1, "tasks": [{"id": "1", "title": "Test Task 1", "description": "Test Description 1"}]}
        success = store.save_task_plan(task_plan)
        if not success:
            print("❌ Failed to save task plan")
            return False
        
        retrieved_plan = store.get_task_plan()
        if not retrieved_plan or retrieved_plan != task_plan:
            print("❌ Failed to retrieve correct task plan")
            return False
        
        # Clean up test data
        store.clear_project_data()
        
        print("✅ Database functionality test passed")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
