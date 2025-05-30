#!/bin/bash
"""
Check NeuroDock MCP Server Status
"""

cd /Users/barnent1/.neuro-dock

echo "🔍 Checking MCP Server Status..."
echo "================================"

if [ -f logs/mcp_server.pid ]; then
    PID=$(cat logs/mcp_server.pid)
    if ps -p $PID > /dev/null; then
        echo "✅ MCP Server is running (PID: $PID)"
        echo "📊 Process info:"
        ps -p $PID -o pid,ppid,etime,cmd
    else
        echo "❌ MCP Server not running (stale PID file)"
        rm logs/mcp_server.pid
    fi
else
    echo "❌ No PID file found"
    # Check for any running processes
    RUNNING=$(pgrep -f "server_minimal.py")
    if [ ! -z "$RUNNING" ]; then
        echo "⚠️  Found MCP server processes without PID file:"
        ps -p $RUNNING -o pid,ppid,etime,cmd
    fi
fi

echo ""
echo "📝 Recent log entries:"
echo "====================="
if [ -f logs/mcp_server.log ]; then
    tail -10 logs/mcp_server.log
else
    echo "No log file found"
fi
