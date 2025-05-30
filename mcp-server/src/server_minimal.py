#!/usr/bin/env python3
"""
Minimal NeuroDock MCP Server - Fast startup version for debugging
"""

import sys
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Minimal server with just basic tools
mcp = FastMCP("neurodock-minimal")

@mcp.tool()
def test_connection() -> str:
    """Test tool to verify MCP server connection"""
    return "✅ NeuroDock MCP server is connected and working!"

@mcp.tool()
def list_workspace_files() -> str:
    """List files in the workspace"""
    try:
        workspace = Path.cwd()
        files = [f.name for f in workspace.iterdir() if f.is_file()]
        return f"Workspace files: {', '.join(files[:10])}"
    except Exception as e:
        return f"Error listing files: {e}"

if __name__ == "__main__":
    print("🚀 Starting minimal NeuroDock MCP server...", file=sys.stderr)
    mcp.run(transport='stdio')
