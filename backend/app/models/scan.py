"""
VibeSec Backend - Scan Model

SQLAlchemy model for scans.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, Float, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.finding import Finding


class ScanStatus(str, enum.Enum):
    """Scan execution status."""
    PENDING = "pending"
    CLONING = "cloning"
    DETECTING = "detecting"
    SCANNING_SAST = "scanning_sast"
    SCANNING_SCA = "scanning_sca"
    SCORING = "scoring"
    COMPLETED = "completed"
    FAILED = "failed"


class Scan(Base):
    """Scan model for project scans."""
    
    __tablename__ = "scans"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    
    # Status
    status: Mapped[ScanStatus] = mapped_column(
        SQLEnum(ScanStatus, values_callable=lambda x: [e.value for e in x]), 
        default=ScanStatus.PENDING
    )
    status_message: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    progress: Mapped[int] = mapped_column(default=0)  # 0-100
    
    # Commit info (if GitHub)
    commit_sha: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    commit_message: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    branch: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Overall Scores
    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Domain Scores (stored as JSON for flexibility)
    domain_scores: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Expected structure:
    # {
    #     "security": {"score": 80, "issues": 5},
    #     "testing": {"score": 60, "coverage": 45},
    #     "reliability": {"score": 75, "issues": 2},
    #     "observability": {"score": 50, "issues": 3},
    #     "performance": {"score": 85, "issues": 1},
    #     "infrastructure": {"score": 90, "issues": 0}
    # }
    
    # Statistics
    total_findings: Mapped[int] = mapped_column(default=0)
    critical_count: Mapped[int] = mapped_column(default=0)
    high_count: Mapped[int] = mapped_column(default=0)
    medium_count: Mapped[int] = mapped_column(default=0)
    low_count: Mapped[int] = mapped_column(default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="scans")
    findings: Mapped[list["Finding"]] = relationship(
        "Finding",
        back_populates="scan",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Scan {self.id} - {self.status}>"
    
    @property
    def duration_seconds(self) -> Optional[int]:
        """Calculate scan duration in seconds."""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None
