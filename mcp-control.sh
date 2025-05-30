#!/bin/bash
# NeuroDock MCP Server Control Script (NPX Version)

case "$1" in
    start)
        echo "🚀 Starting NeuroDock MCP Server with NPX..."
        cd /Users/barnent1/.neuro-dock
        
        # Check if already running
        if pgrep -f "neurodock-mcp" > /dev/null; then
            echo "⚠️  MCP Server is already running"
            exit 1
        fi
        
        # Start the server
        nohup npx neurodock-mcp > logs/mcp_server_npx.log 2>&1 &
        PID=$!
        echo $PID > logs/mcp_server_npx.pid
        
        echo "✅ MCP Server started with PID: $PID"
        echo "📝 Logs: logs/mcp_server_npx.log"
        ;;
        
    stop)
        echo "🛑 Stopping NeuroDock MCP Server..."
        
        if [ -f /Users/barnent1/.neuro-dock/logs/mcp_server_npx.pid ]; then
            PID=$(cat /Users/barnent1/.neuro-dock/logs/mcp_server_npx.pid)
            if ps -p $PID > /dev/null; then
                kill $PID
                echo "✅ Stopped MCP Server (PID: $PID)"
            fi
            rm /Users/barnent1/.neuro-dock/logs/mcp_server_npx.pid
        fi
        
        # Also kill any remaining processes
        pkill -f "neurodock-mcp" && echo "🧹 Cleaned up any remaining processes"
        ;;
        
    status)
        echo "🔍 MCP Server Status:"
        
        if pgrep -f "neurodock-mcp" > /dev/null; then
            echo "✅ MCP Server is running"
            echo "📊 Processes:"
            pgrep -f "neurodock-mcp" | xargs ps -p
        else
            echo "❌ MCP Server is not running"
        fi
        
        echo ""
        echo "📝 Recent logs:"
        if [ -f /Users/barnent1/.neuro-dock/logs/mcp_server_npx.log ]; then
            tail -5 /Users/barnent1/.neuro-dock/logs/mcp_server_npx.log
        else
            echo "No log file found"
        fi
        ;;
        
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
        
    *)
        echo "Usage: $0 {start|stop|status|restart}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the MCP server using NPX"
        echo "  stop    - Stop the MCP server"
        echo "  status  - Check server status and show logs"
        echo "  restart - Restart the server"
        ;;
esac
