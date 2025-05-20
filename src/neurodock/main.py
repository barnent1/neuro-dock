import logging
import asyncio
import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import pathlib

from neurodock.routes import memory, task, mcp, ui, api, projects
from neurodock.agents.autonomous_agent import agent

# Configure logging
logging_level = logging.DEBUG if os.getenv("DEBUG", "false").lower() == "true" else logging.INFO
logging.basicConfig(
    level=logging_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="NeuroDock",
    description="A memory and task execution system for AI agents using Neo4j and Model Context Protocol",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
app.mount("/static", StaticFiles(directory=pathlib.Path(__file__).parent / "static"), name="static")

# Include routers
app.include_router(memory.router)
app.include_router(task.router)
app.include_router(mcp.router)
app.include_router(api.router)  # API for UI
app.include_router(ui.router, prefix="/ui")  # UI routes

# Agent task
agent_task = None

@app.on_event("startup")
async def startup_event():
    """
    Start the agent loop when the application starts.
    """
    global agent_task
    logger.info("Starting NeuroDock application")
    
    # Start the agent loop if OPENAI_API_KEY is set
    if os.getenv("OPENAI_API_KEY"):
        logger.info("Starting autonomous agent")
        agent_task = asyncio.create_task(agent.run_agent_loop())
    else:
        logger.warning("OPENAI_API_KEY not set, autonomous agent will not start")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Stop the agent loop when the application shuts down.
    """
    global agent_task
    logger.info("Shutting down NeuroDock application")
    
    if agent_task:
        agent.stop()
        try:
            # Wait for the agent task to complete with a timeout
            await asyncio.wait_for(agent_task, timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("Agent task did not complete within the timeout period")
        except Exception as e:
            logger.error(f"Error stopping agent: {str(e)}")


@app.get("/")
async def root():
    """
    Root endpoint, returns basic system information.
    """
    return {
        "name": "NeuroDock",
        "version": "0.1.0",
        "description": "Memory and task execution system for AI agents",
        "endpoints": {
            "memory": "/memory",
            "task": "/task",
            "mcp": "/mcp",
            "ui": "/ui",
            "api": "/api",
            "docs": "/docs",
        }
    }


@app.get("/health")
async def health():
    """
    Health check endpoint.
    """
    agent_status = "running" if agent_task and not agent_task.done() else "stopped"
    
    return {
        "status": "healthy",
        "agent": agent_status,
        "database": "connected"  # In a more advanced implementation, check Neo4j connection
    }
    
    return {
        "status": "ok",
        "agent_status": agent_status
    }


def start_application():
    """
    Function to start the application, useful for gunicorn.
    """
    return app
