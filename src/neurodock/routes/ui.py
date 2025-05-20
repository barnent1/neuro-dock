from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
import os
import logging
import pathlib

from neurodock.models.memory import MemoryNode, MemoryCreate, MemoryType
from neurodock.neo4j.memory_repository import MemoryRepository

# Configure logging
logger = logging.getLogger(__name__)

# Set up templates
template_path = pathlib.Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(template_path))

# Create router
router = APIRouter(tags=["ui"])

@router.get("/")
async def dashboard(request: Request):
    """
    Render the main dashboard UI
    """
    return templates.TemplateResponse("memory_dashboard.html", {"request": request})

@router.get("/memories")
async def memories_page(request: Request):
    """
    Render the memories page UI
    """
    return templates.TemplateResponse("memory_dashboard.html", {"request": request})

@router.get("/apps")
async def apps_page(request: Request):
    """
    Render the apps page UI
    """
    # For the future, we'll just use the dashboard for now
    return templates.TemplateResponse("memory_dashboard.html", {"request": request})
