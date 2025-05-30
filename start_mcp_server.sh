#!/bin/bash
"""
NeuroDock MCP Server Startup Script
This script starts the MCP server in the background
"""

# Set the working directory
cd /Users/barnent1/.neuro-dock

# Set environment variables
export PYTHONPATH="/Users/barnent1/.neuro-dock:/Users/barnent1/.neuro-dock/mcp-server/src"

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the MCP server in the background
nohup python3 /Users/barnent1/.neuro-dock/mcp-server/src/server_background.py > logs/mcp_server.log 2>&1 &

# Get the process ID
PID=$!
echo $PID > logs/mcp_server.pid

echo "🚀 MCP Server started with PID: $PID"
echo "📝 Logs available at: logs/mcp_server.log"
echo "🔍 To check status: ps -p $PID"
echo "🛑 To stop: kill $PID"
