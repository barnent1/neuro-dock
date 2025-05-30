#!/usr/bin/env python3
"""
NeuroDock MCP Server - Debug Version
Logs startup process for debugging VS Code integration
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Setup logging
log_file = Path(__file__).parent.parent / "logs" / "mcp_debug.log"
log_file.parent.mkdir(exist_ok=True)

def debug_log(message):
    """Log debug message to file and stderr"""
    timestamp = datetime.now().isoformat()
    log_message = f"[{timestamp}] {message}\n"
    
    # Write to log file
    with open(log_file, "a") as f:
        f.write(log_message)
    
    # Also write to stderr for VS Code to see
    print(f"DEBUG: {message}", file=sys.stderr)

debug_log("🚀 NeuroDock MCP Server Debug - Starting up")
debug_log(f"Python executable: {sys.executable}")
debug_log(f"Python version: {sys.version}")
debug_log(f"Working directory: {os.getcwd()}")
debug_log(f"Script path: {__file__}")
debug_log(f"Arguments: {sys.argv}")

try:
    debug_log("Adding NeuroDock to Python path...")
    neurodock_src = Path(__file__).parent.parent / "src"
    if neurodock_src.exists():
        sys.path.insert(0, str(neurodock_src))
        debug_log(f"Added to path: {neurodock_src}")
    else:
        debug_log(f"⚠️  NeuroDock source not found at: {neurodock_src}")

    debug_log("Importing FastMCP...")
    from mcp.server.fastmcp import FastMCP
    debug_log("✅ FastMCP imported successfully")

    debug_log("Importing NeuroDock modules...")
    from neurodock.db import get_store
    debug_log("✅ NeuroDock imports successful")

    debug_log("Creating FastMCP server instance...")
    mcp = FastMCP("neurodock-mcp")
    debug_log("✅ FastMCP server created")

    debug_log("Adding a simple test tool...")
    
    @mcp.tool()
    def test_tool(message: str = "Hello from NeuroDock!") -> str:
        """Test tool to verify MCP server is working"""
        debug_log(f"Test tool called with message: {message}")
        return f"✅ NeuroDock MCP Server is working! Message: {message}"

    debug_log("✅ Test tool registered")

    debug_log("Starting MCP server with stdio transport...")
    mcp.run(transport='stdio')

except Exception as e:
    debug_log(f"❌ Error during startup: {str(e)}")
    debug_log(f"Error type: {type(e).__name__}")
    import traceback
    debug_log(f"Traceback: {traceback.format_exc()}")
    sys.exit(1)
