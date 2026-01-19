"""
VibeSec Backend - Project API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional

from app.api.deps import DBSession, CurrentUser
from app.models.project import Project, SourceType, StackType
from app.models.scan import Scan
from app.schemas.project import (
    ProjectCreateGitHub,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectWithStats,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    user: CurrentUser,
    db: DBSession,
    skip: int = 0,
    limit: int = 20,
):
    """List all projects for the current user."""
    # Count total
    count_result = await db.execute(
        select(func.count(Project.id)).where(Project.user_id == user.id)
    )
    total = count_result.scalar()
    
    # Fetch projects
    result = await db.execute(
        select(Project)
        .where(Project.user_id == user.id)
        .order_by(Project.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    projects = result.scalars().all()
    
    return ProjectListResponse(
        projects=[ProjectResponse.model_validate(p) for p in projects],
        total=total,
    )


@router.post("/github", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project_from_github(
    project_data: ProjectCreateGitHub,
    user: CurrentUser,
    db: DBSession,
):
    """Create a new project from GitHub repository."""
    # Check if project with same repo already exists for user
    existing = await db.execute(
        select(Project).where(
            Project.user_id == user.id,
            Project.repo_full_name == project_data.repo_full_name,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project for this repository already exists",
        )
    
    project = Project(
        user_id=user.id,
        name=project_data.name,
        description=project_data.description,
        source_type=SourceType.GITHUB,
        repo_url=project_data.repo_url,
        repo_full_name=project_data.repo_full_name,
        default_branch=project_data.default_branch,
        stack=StackType.UNKNOWN,  # Will be detected on first scan
    )
    
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    return ProjectResponse.model_validate(project)


@router.post("/zip", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project_from_zip(
    user: CurrentUser,
    db: DBSession,
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
):
    """Create a new project from ZIP upload."""
    if not file.filename.endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a ZIP archive",
        )
    
    # TODO: Upload to R2 storage
    # For now, we'll save the path placeholder
    storage_path = f"uploads/{user.id}/{file.filename}"
    
    project = Project(
        user_id=user.id,
        name=name,
        description=description,
        source_type=SourceType.ZIP,
        storage_path=storage_path,
        stack=StackType.UNKNOWN,
    )
    
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    return ProjectResponse.model_validate(project)


@router.get("/{project_id}", response_model=ProjectWithStats)
async def get_project(
    project_id: int,
    user: CurrentUser,
    db: DBSession,
):
    """Get project details with stats."""
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id, Project.user_id == user.id)
        .options(selectinload(Project.scans))
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    # Calculate stats from latest scan
    total_scans = len(project.scans)
    critical_findings = 0
    high_findings = 0
    
    if project.scans:
        latest_scan = project.scans[0]  # Already ordered by desc
        critical_findings = latest_scan.critical_count
        high_findings = latest_scan.high_count
    
    return ProjectWithStats(
        id=project.id,
        name=project.name,
        description=project.description,
        source_type=project.source_type,
        repo_url=project.repo_url,
        repo_full_name=project.repo_full_name,
        stack=project.stack,
        latest_score=project.latest_score,
        latest_scan_id=project.latest_scan_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
        total_scans=total_scans,
        critical_findings=critical_findings,
        high_findings=high_findings,
    )


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    updates: ProjectUpdate,
    user: CurrentUser,
    db: DBSession,
):
    """Update project details."""
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    if updates.name is not None:
        project.name = updates.name
    if updates.description is not None:
        project.description = updates.description
    
    await db.commit()
    await db.refresh(project)
    
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    user: CurrentUser,
    db: DBSession,
):
    """Delete a project and all associated data."""
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    await db.delete(project)
    await db.commit()
