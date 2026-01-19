"""
VibeSec Backend - Pydantic Schemas for Scans
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.models.scan import ScanStatus


class DomainScore(BaseModel):
    """Individual domain score."""
    score: float
    issues: int = 0
    details: Optional[dict] = None


class DomainScores(BaseModel):
    """All domain scores."""
    security: Optional[DomainScore] = None
    testing: Optional[DomainScore] = None
    reliability: Optional[DomainScore] = None
    observability: Optional[DomainScore] = None
    performance: Optional[DomainScore] = None
    infrastructure: Optional[DomainScore] = None


class ScanCreate(BaseModel):
    """Schema for triggering a scan."""
    branch: Optional[str] = None  # Use project's default if not specified
    commit_sha: Optional[str] = None  # Use latest if not specified


class ScanProgress(BaseModel):
    """Schema for scan progress updates (WebSocket)."""
    scan_id: int
    status: ScanStatus
    progress: int
    status_message: Optional[str] = None


class ScanResponse(BaseModel):
    """Response schema for scan."""
    id: int
    project_id: int
    status: ScanStatus
    status_message: Optional[str] = None
    progress: int
    commit_sha: Optional[str] = None
    commit_message: Optional[str] = None
    branch: Optional[str] = None
    overall_score: Optional[float] = None
    domain_scores: Optional[DomainScores] = None
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    
    model_config = {"from_attributes": True}


class ScanListResponse(BaseModel):
    """Response schema for scan list."""
    scans: list[ScanResponse]
    total: int


class ScanSummary(BaseModel):
    """Brief scan summary for lists."""
    id: int
    status: ScanStatus
    overall_score: Optional[float] = None
    total_findings: int
    critical_count: int
    high_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None
