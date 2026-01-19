"""
VibeSec Backend - Pydantic Schemas for Projects
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl

from app.models.project import SourceType, StackType


class ProjectBase(BaseModel):
    """Base project schema."""
    name: str
    description: Optional[str] = None


class ProjectCreateGitHub(ProjectBase):
    """Schema for creating a project from GitHub."""
    repo_url: str
    repo_full_name: str
    default_branch: str = "main"


class ProjectCreateZip(ProjectBase):
    """Schema for creating a project from ZIP upload."""
    pass  # File will be handled separately via multipart form


class ProjectUpdate(BaseModel):
    """Schema for updating project info."""
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectResponse(ProjectBase):
    """Response schema for project."""
    id: int
    source_type: SourceType
    repo_url: Optional[str] = None
    repo_full_name: Optional[str] = None
    stack: StackType
    latest_score: Optional[float] = None
    latest_scan_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    """Response schema for project list."""
    projects: list[ProjectResponse]
    total: int


class ProjectWithStats(ProjectResponse):
    """Project response with additional statistics."""
    total_scans: int = 0
    critical_findings: int = 0
    high_findings: int = 0
