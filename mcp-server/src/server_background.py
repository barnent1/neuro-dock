#!/usr/bin/env python3
"""
NeuroDock MCP Server - Background Service Version
This version runs as a background service on a specific port
"""

import sys
import asyncio
import logging
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/barnent1/.neuro-dock/logs/mcp_server.log'),
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger(__name__)

# Create MCP server
mcp = FastMCP("neurodock-minimal")

@mcp.tool()
def test_connection() -> str:
    """Test tool to verify MCP server connection"""
    logger.info("Test connection called")
    return "✅ NeuroDock MCP server is connected and working!"

@mcp.tool()
def list_workspace_files() -> str:
    """List files in the workspace"""
    try:
        workspace = Path("/Users/barnent1/.neuro-dock")
        files = [f.name for f in workspace.iterdir() if f.is_file()]
        result = f"Workspace files: {', '.join(files[:10])}"
        logger.info(f"Listed workspace files: {len(files)} files found")
        return result
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return f"Error listing files: {e}"

@mcp.tool()
def get_project_structure() -> str:
    """Get the structure of the NeuroDock project"""
    try:
        workspace = Path("/Users/barnent1/.neuro-dock")
        structure = []
        
        def scan_directory(path, level=0):
            indent = "  " * level
            for item in sorted(path.iterdir()):
                if item.name.startswith('.'):
                    continue
                if item.is_dir():
                    structure.append(f"{indent}{item.name}/")
                    if level < 2:  # Limit depth
                        scan_directory(item, level + 1)
                else:
                    structure.append(f"{indent}{item.name}")
        
        scan_directory(workspace)
        result = "NeuroDock Project Structure:\n" + "\n".join(structure[:50])
        logger.info("Project structure requested")
        return result
    except Exception as e:
        logger.error(f"Error getting project structure: {e}")
        return f"Error getting project structure: {e}"

async def main():
    """Main function to run the MCP server"""
    logger.info("🚀 Starting NeuroDock MCP Server as background service...")
    
    try:
        # For background service, we'll use stdio transport but with proper async handling
        logger.info("MCP Server ready and listening...")
        await mcp.run_async(transport='stdio')
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
