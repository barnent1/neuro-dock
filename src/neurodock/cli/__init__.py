"""
Command line interface for NeuroDock.
"""
import sys
import os
import click
import asyncio
import subprocess
import time
from typing import Optional

@click.group()
def cli():
    """NeuroDock CLI - Manage your NeuroDock system."""
    pass

@cli.command("serve")
@click.option("--host", default="0.0.0.0", help="Host to bind to.")
@click.option("--port", default=4000, help="Port to bind to.")
@click.option("--reload", is_flag=True, help="Enable auto reload on code changes.")
def serve(host: str, port: int, reload: bool):
    """Run the NeuroDock server locally (without Docker)."""
    import uvicorn
    uvicorn.run(
        "neurodock.main:app",
        host=host,
        port=port,
        reload=reload
    )

@cli.command("docker")
@click.option("--action", "-a", type=click.Choice(['start', 'stop', 'restart', 'logs']), default='start', help="Docker action to perform.")
@click.option("--populate", "-p", is_flag=True, help="Populate with sample data after starting.")
@click.option("--test", "-t", is_flag=True, help="Run MCP tests after starting.")
def docker_command(action: str, populate: bool, test: bool):
    """Manage NeuroDock Docker deployment."""
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    if action == 'start':
        click.echo("Starting NeuroDock Docker containers...")
        subprocess.run(['docker-compose', 'up', '-d'], cwd=project_root, check=True)
        
        # Removed automatic sample data population for production/real data use
        
        if test:
            click.echo("Running MCP integration tests...")
            subprocess.run(['./run_mcp_tests.sh'], cwd=project_root, check=True)
            
    elif action == 'stop':
        click.echo("Stopping NeuroDock Docker containers...")
        subprocess.run(['docker-compose', 'down'], cwd=project_root, check=True)
        
    elif action == 'restart':
        click.echo("Restarting NeuroDock Docker containers...")
        subprocess.run(['docker-compose', 'restart'], cwd=project_root, check=True)
        
    elif action == 'logs':
        click.echo("Showing NeuroDock Docker logs...")
        subprocess.run(['docker-compose', 'logs', '-f'], cwd=project_root)

@cli.command("dashboard")
@click.option("--docker/--no-docker", default=True, help="Whether to use Docker deployment.")
def dashboard(docker: bool):
    """Open the Memory Dashboard in the default browser."""
    import webbrowser
    
    if docker:
        # Make sure Docker containers are running
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        try:
            subprocess.run(
                ['docker-compose', 'ps', '-q', 'app'],
                cwd=project_root,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError:
            click.echo("Docker containers are not running. Starting them now...")
            subprocess.run(['docker-compose', 'up', '-d'], cwd=project_root, check=True)
            click.echo("Waiting for services to start...")
            time.sleep(5)
    
    # Open dashboard in browser
    webbrowser.open("http://localhost:4000/ui/memories")
    click.echo("Memory Dashboard opened in your default browser.")

@cli.command("init")
@click.option("--project-dir", "-d", default=".", help="Project directory.")
@click.option("--project-id", "-p", help="Project ID.")
def init_project(project_dir: str, project_id: Optional[str]):
    """Initialize a new NeuroDock project."""
    from neurodock.services.project_settings import ProjectSettings
    
    if not project_id:
        import uuid
        project_id = str(uuid.uuid4())
    
    # Get absolute path
    project_dir = os.path.abspath(project_dir)
    
    # Create project config
    settings = {
        "project_id": project_id,
        "memory_isolation_level": "strict"
    }
    
    # Save settings
    ProjectSettings.save_settings(project_dir, settings)
    click.echo(f"Project initialized with ID: {project_id}")
    click.echo(f"Configuration saved to: {os.path.join(project_dir, 'neurodock.json')}")

@cli.command("populate")
@click.option("--count", "-n", default=10, help="Number of memories to create.")
def populate(count: int):
    """Populate the database with sample data."""
    click.echo("Sample data population is disabled.")

def main():
    """Main entry point for the CLI."""
    cli()

if __name__ == "__main__":
    main()
    
