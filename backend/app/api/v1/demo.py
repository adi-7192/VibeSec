"""
VibeSec Backend - Demo API Routes

Demo project creation for new users.
"""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DBSession, CurrentUser
from app.models.project import Project, SourceType
from app.services.demo import create_demo_project

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/project")
async def create_demo(user: CurrentUser, db: DBSession):
    """Create a demo project with sample scan data."""
    
    # Check if user already has a demo project
    result = await db.execute(
        select(Project).where(
            Project.user_id == user.id,
            Project.source_type == SourceType.DEMO,
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        return {
            "message": "Demo project already exists",
            "project_id": existing.id,
            "project_name": existing.name,
            "already_exists": True,
        }
    
    # Create demo project
    project = await create_demo_project(db, user)
    
    return {
        "message": "Demo project created successfully",
        "project_id": project.id,
        "project_name": project.name,
        "already_exists": False,
    }


@router.get("/project")
async def get_demo(user: CurrentUser, db: DBSession):
    """Get the demo project for the current user."""
    result = await db.execute(
        select(Project).where(
            Project.user_id == user.id,
            Project.source_type == SourceType.DEMO,
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No demo project found. Create one first.",
        )
    
    return {
        "project_id": project.id,
        "project_name": project.name,
        "latest_score": project.latest_score,
        "latest_scan_id": project.latest_scan_id,
    }
