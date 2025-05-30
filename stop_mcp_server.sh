#!/bin/bash
"""
Stop NeuroDock MCP Server Script
"""

cd /Users/barnent1/.neuro-dock

if [ -f logs/mcp_server.pid ]; then
    PID=$(cat logs/mcp_server.pid)
    if ps -p $PID > /dev/null; then
        kill $PID
        echo "🛑 MCP Server (PID: $PID) stopped"
        rm logs/mcp_server.pid
    else
        echo "❌ MCP Server process not found"
        rm logs/mcp_server.pid
    fi
else
    echo "❌ No PID file found. Server may not be running."
    # Try to find and kill any running server processes
    pkill -f "server_minimal.py" && echo "🛑 Found and stopped MCP server process"
fi
