#!/usr/bin/env python3

"""
Database schema initialization for NeuroDock PostgreSQL backend.
"""

import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
from ..config import get_config
import warnings

# Get centralized configuration
config = get_config()

def get_db_connection():
    """Get PostgreSQL database connection. Raises exception on failure."""
    postgres_url = config.postgres_url
    
    try:
        conn = psycopg2.connect(postgres_url, cursor_factory=RealDictCursor)
        return conn
    except psycopg2.OperationalError as e:
        # NeuroDock requires a database connection to function
        error_msg = f"""
❌ NeuroDock Database Connection Failed

NeuroDock requires a PostgreSQL database to store tasks, memory, and discussions.

Connection error: {str(e)}

📋 Quick Setup Options:

🌐 Cloud Databases (Recommended):
  • Supabase: https://supabase.com (free tier available)
  • Neon: https://neon.tech (generous free tier)
  • Aiven: https://aiven.io (free trial)

🏠 Local Setup:
  • Install PostgreSQL locally
  • Or use Docker: docker run --name neurodock-postgres -e POSTGRES_PASSWORD=password -d -p 5432:5432 postgres

⚙️  Configuration:
  Set POSTGRES_URL environment variable or run 'nd setup' for guidance.

💡 Need help? Check the setup guide: 'nd setup'
"""
        raise ConnectionError(error_msg)

def check_database_status():
    """Check database connection and return user-friendly status info."""
    try:
        conn = get_db_connection()
        conn.close()
        return {
            "connected": True,
            "message": "✅ Database connected successfully"
        }
    except Exception as e:
        return {
            "connected": False,
            "message": "❌ Database connection failed",
            "help": f"Error: {str(e)}"
        }

def initialize_schema():
    """Initialize the PostgreSQL schema with required tables."""
    conn = get_db_connection()  # This will raise if no connection
    
    try:
        with conn.cursor() as cur:
            # Create tasks table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    title TEXT,
                    description TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMPTZ DEFAULT now(),
                    completed_at TIMESTAMPTZ,
                    parent_id UUID,
                    complexity TEXT,
                    dependencies TEXT[],
                    project_path TEXT NOT NULL
                );
            """)
            
            # Create memory table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS memory (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    type TEXT,
                    text TEXT,
                    created_at TIMESTAMPTZ DEFAULT now(),
                    project_path TEXT NOT NULL
                );
            """)
            
            # Create discussion table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS discussion (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    role TEXT,
                    message TEXT,
                    turn_index INT,
                    created_at TIMESTAMPTZ DEFAULT now(),
                    project_path TEXT NOT NULL
                );
            """)
            
            # Create indexes for better performance
            cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_project_path ON tasks(project_path);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_project_path ON memory(project_path);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_type ON memory(type);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_discussion_project_path ON discussion(project_path);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_discussion_turn_index ON discussion(turn_index);")
            
            conn.commit()
            return True
            
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Failed to initialize database schema: {str(e)}")
    finally:
        conn.close()

def test_database_connection():
    """Test the database connection and schema."""
    conn = get_db_connection()  # This will raise if no connection
    
    try:
        with conn.cursor() as cur:
            # Test basic connectivity
            cur.execute("SELECT 1;")
            
            # Test tables exist
            cur.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('tasks', 'memory', 'discussion');
            """)
            
            tables = [row['table_name'] for row in cur.fetchall()]
            required_tables = {'tasks', 'memory', 'discussion'}
            
            if not required_tables.issubset(set(tables)):
                missing_tables = required_tables - set(tables)
                raise RuntimeError(f"Missing required database tables: {missing_tables}")
            
            return True
            
    except Exception as e:
        raise RuntimeError(f"Database test failed: {str(e)}")
    finally:
        conn.close()
