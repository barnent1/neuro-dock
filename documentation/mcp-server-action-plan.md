# NeuroDock MCP Server - Current State & Action Plan

## Current State Analysis

### What's Already Built ✅
- **Working MCP server** in `/mcp-server/src/server.py` using FastMCP
- **7 core tools** implemented:
  - `neurodock_get_project_status`
  - `neurodock_list_tasks` 
  - `neurodock_update_task`
  - `neurodock_create_task`
  - `neurodock_add_memory`
  - `neurodock_search_memory`
  - `neurodock_get_project_context`
- **SQLite fallback database** for basic functionality
- **NPM package structure** ready for distribution
- **Claude Desktop integration** configuration ready

### What Needs to be Fixed 🔧

#### 1. Database Integration Issue
**Current Problem**: Server uses SQLite fallback instead of NeuroDock's PostgreSQL + Qdrant + Neo4J system
**Solution**: Integrate with actual NeuroDock core database layer

#### 2. Missing Agile Workflow Tools
**Current Gap**: No discussion flow or agile process tools
**Need to Add**:
- `neurodock_start_discussion` - Begin iterative requirements gathering
- `neurodock_continue_discussion` - Provide answers and continue iteration  
- `neurodock_get_discussion_status` - Check discussion state
- Sprint planning and retrospective tools

#### 3. Missing Resources & Prompts
**Current Gap**: Only tools implemented, no Resources or Prompts
**Need to Add**:
- Resources for project context access
- Prompts for agile workflow templates

#### 4. No Integration with NeuroDock Core
**Current Problem**: Server bypasses NeuroDock core system entirely
**Solution**: Import and use actual NeuroDock modules

## Action Plan

### Phase 1: Fix Core Integration 🎯
**Goal**: Connect MCP server to actual NeuroDock system

1. **Import NeuroDock modules** into MCP server
   ```python
   import sys
   sys.path.append('../src')  # Add NeuroDock core to path
   
   from neurodock.db import get_store
   from neurodock.discussion import run_interactive_discussion
   from neurodock.memory.qdrant_store import search_memory, add_to_memory
   from neurodock.agent import ProjectAgent
   ```

2. **Replace SQLite with NeuroDock database layer**
   - Remove SQLite queries
   - Use `get_store()` for database operations
   - Connect to PostgreSQL/Qdrant system

3. **Update tool implementations** to call NeuroDock core functions
   ```python
   @mcp.tool()
   async def neurodock_get_project_status() -> str:
       # Use actual NeuroDock ProjectAgent
       agent = ProjectAgent(os.getcwd())
       context = agent.load_project_context()
       return json.dumps(context, indent=2)
   ```

### Phase 2: Add Discussion Flow Tools 🗣️
**Goal**: Support iterative agile conversations

1. **Add discussion state management tools**
   - `neurodock_start_discussion`
   - `neurodock_continue_discussion` 
   - `neurodock_get_discussion_status`

2. **Connect to NeuroDock discussion system**
   - Use `run_interactive_discussion()` function
   - Leverage existing discussion state management
   - Support multi-iteration conversations

### Phase 3: Add Resources & Prompts 📚
**Goal**: Complete MCP feature set

1. **Implement Resources**
   - `neurodock://project/config` - Project configuration
   - `neurodock://project/plan` - Task plan
   - `neurodock://project/discussions` - Conversation history
   - `neurodock://project/memory` - Project memory/decisions

2. **Implement Prompts**
   - `neurodock-start-project` - Begin project planning
   - `neurodock-sprint-planning` - Plan development sprint
   - `neurodock-retrospective` - Analyze completed work
   - `neurodock-clarify-requirements` - Deep dive requirements

### Phase 4: Polish & Package 🚀
**Goal**: Production-ready distribution

1. **Error handling improvements**
2. **Documentation updates** 
3. **Testing with Claude Desktop**
4. **NPM package publishing**

## Key Changes Needed

### 1. Server Initialization
```python
# Current approach (SQLite)
def get_db_path():
    # ... SQLite logic

# New approach (NeuroDock core)
def get_neurodock_store():
    try:
        return get_store(str(Path.cwd()))
    except Exception as e:
        print(f"Failed to connect to NeuroDock database: {e}")
        return None
```

### 2. Tool Implementation Pattern
```python
# Current approach (direct SQL)
@mcp.tool()
async def neurodock_list_tasks(status: str = "all") -> str:
    tasks = query_database("SELECT * FROM tasks...")
    return json.dumps(tasks)

# New approach (NeuroDock core)
@mcp.tool()
async def neurodock_list_tasks(status: str = "all") -> str:
    store = get_neurodock_store()
    if not store:
        return "NeuroDock database not available"
    
    # Use actual NeuroDock task management
    plan_data = store.get_task_plan()
    tasks = plan_data.get('tasks', []) if plan_data else []
    
    if status != "all":
        tasks = [t for t in tasks if t.get('status') == status]
    
    return json.dumps(tasks, indent=2)
```

### 3. Discussion Integration
```python
# New tools needed
@mcp.tool()
async def neurodock_start_discussion(initial_prompt: str) -> str:
    """Begin iterative requirements gathering discussion."""
    try:
        nd_path = Path.cwd() / ".neuro-dock"
        success = run_interactive_discussion(nd_path, initial_prompt)
        return "Discussion started successfully" if success else "Failed to start discussion"
    except Exception as e:
        return f"Error starting discussion: {str(e)}"
```

## Clear Division of Responsibilities

### NeuroDock MCP Server Does:
- ✅ Project planning and task breakdown
- ✅ Memory storage and retrieval  
- ✅ Discussion facilitation and requirements gathering
- ✅ Progress tracking and status reporting
- ✅ Agile workflow orchestration

### AI Agent (Claude/Copilot) Does:
- ✅ All code generation and implementation
- ✅ File system operations
- ✅ Running tests and builds
- ✅ Git operations and version control  
- ✅ Technical decision-making during implementation

## Success Criteria

1. **MCP server connects to actual NeuroDock database** instead of SQLite
2. **All tools work with real project data** from NeuroDock system
3. **Discussion flow supported** through MCP tools
4. **Claude Desktop integration works** seamlessly
5. **Agent can plan entire projects** using NeuroDock via MCP
6. **Memory persistence works** across sessions

## Next Steps

1. **Read the implementation guide** we created: `/documentation/mcp-implementation-guide.md`
2. **Fix the database integration** in `mcp-server/src/server.py`
3. **Test with actual NeuroDock project** to verify integration
4. **Add missing discussion flow tools**
5. **Test end-to-end with Claude Desktop**

The foundation is solid - we just need to connect it properly to the NeuroDock core system!
