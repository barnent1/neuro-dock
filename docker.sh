#!/usr/bin/env bash

# NeuroDock Docker Manager Script
# A unified script to manage NeuroDock Docker operations

set -e  # Exit on error

# Determine the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Parse command line arguments
ACTION="start"  # Default action
POPULATE=false
DASHBOARD=true
DETACHED=true
SAMPLE_COUNT=10

# Parse options
while [[ $# -gt 0 ]]; do
    case $1 in
        start|up)
            ACTION="start"
            shift
            ;;
        stop|down)
            ACTION="stop"
            shift
            ;;
        restart)
            ACTION="restart"
            shift
            ;;
        logs)
            ACTION="logs"
            shift
            ;;
        populate)
            POPULATE=true
            shift
            if [[ $1 =~ ^[0-9]+$ ]]; then
                SAMPLE_COUNT=$1
                shift
            fi
            ;;
        --foreground|-f)
            DETACHED=false
            shift
            ;;
        --help|-h)
            ACTION="help"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            ACTION="help"
            shift
            ;;
    esac
done

# Display help message
if [ "$ACTION" == "help" ]; then
    echo "NeuroDock Docker Manager"
    echo "========================"
    echo ""
    echo "Usage: ./docker.sh [action] [options]"
    echo ""
    echo "Actions:"
    echo "  start, up        Start the NeuroDock containers (default)"
    echo "  stop, down       Stop the NeuroDock containers"
    echo "  restart          Restart the NeuroDock containers"
    echo "  logs             Show container logs"
    echo "  populate [n]     Populate with sample data (n = number of samples, default 10)"
    echo ""
    echo "Options:"
    echo "  --foreground, -f Run in foreground (not detached)"
    echo "  --help, -h       Show this help message"
    echo ""
    exit 0
fi

# Check if Docker is installed and running
if ! command -v docker &> /dev/null || ! docker info &> /dev/null; then
    echo "Error: Docker is not installed or not running."
    echo "Please install Docker and docker-compose, and ensure the Docker daemon is running."
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose is not installed."
    echo "Please install docker-compose to run NeuroDock."
    exit 1
fi

# Banner
echo "========================================="
echo "          NeuroDock MCP System           "
echo "========================================="
echo ""
echo "  Web Interface: http://localhost:4000/ui/memories"
echo "  API Docs:      http://localhost:4000/docs"
echo "  Neo4j Browser: http://localhost:7474"
echo ""
echo "========================================="

# Execute the requested action
cd "$SCRIPT_DIR"

case $ACTION in
    start)
        echo "Starting NeuroDock containers..."
        if [ "$DETACHED" = true ]; then
            docker-compose up -d
            echo "Containers started in detached mode."
            
            # Wait for services to be ready
            echo "Waiting for services to start..."
            sleep 5
            
            # Populate sample data if requested
            if [ "$POPULATE" = true ]; then
                echo "Populating with $SAMPLE_COUNT sample memories..."
                docker-compose exec app python -m neurodock.scripts.populate_sample_data $SAMPLE_COUNT
            fi
            
            # Open the memory dashboard in browser
            if [ "$DASHBOARD" = true ]; then
                echo "Opening Memory Dashboard in browser..."
                if command -v open &> /dev/null; then
                    # macOS
                    open "http://localhost:4000/ui/memories"
                elif command -v xdg-open &> /dev/null; then
                    # Linux
                    xdg-open "http://localhost:4000/ui/memories"
                elif command -v start &> /dev/null; then
                    # Windows
                    start "http://localhost:4000/ui/memories"
                else
                    echo "Could not automatically open the browser."
                    echo "Please visit http://localhost:4000/ui/memories to access the Memory Dashboard."
                fi
            fi
            
            echo "NeuroDock is now running."
            echo "Run './docker.sh logs' to view logs."
            echo "Run './docker.sh stop' to stop the services."
        else
            # In foreground mode
            docker-compose up
        fi
        ;;
        
    stop)
        echo "Stopping NeuroDock containers..."
        docker-compose down
        echo "Containers stopped."
        ;;
        
    restart)
        echo "Restarting NeuroDock containers..."
        docker-compose down
        if [ "$DETACHED" = true ]; then
            docker-compose up -d
            echo "Containers restarted in detached mode."
        else
            docker-compose up
        fi
        ;;
        
    logs)
        echo "Showing container logs (press Ctrl+C to exit)..."
        docker-compose logs -f
        ;;
esac

exit 0
