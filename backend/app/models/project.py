"""
VibeSec Backend - Project Model

SQLAlchemy model for projects.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, Text, ForeignKey, Enum as SQLEnum, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.scan import Scan


class SourceType(str, enum.Enum):
    """Project source types."""
    GITHUB = "github"
    ZIP = "zip"
    DEMO = "demo"


class StackType(str, enum.Enum):
    """Detected technology stacks."""
    NEXTJS = "nextjs"
    EXPRESS = "express"
    DJANGO = "django"
    FASTAPI = "fastapi"
    UNKNOWN = "unknown"


class Project(Base):
    """Project model for VibeSec projects."""
    
    __tablename__ = "projects"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    # Basic Info
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Source
    source_type: Mapped[SourceType] = mapped_column(SQLEnum(SourceType, values_callable=lambda x: [e.value for e in x]))
    repo_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    repo_full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # owner/repo
    default_branch: Mapped[str] = mapped_column(String(100), default="main")
    
    # For ZIP uploads
    storage_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    
    # Detected Stack
    stack: Mapped[StackType] = mapped_column(
        SQLEnum(StackType, values_callable=lambda x: [e.value for e in x]), 
        default=StackType.UNKNOWN
    )
    
    # Latest Scores (cached for quick access)
    latest_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    latest_scan_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="projects")
    scans: Mapped[list["Scan"]] = relationship(
        "Scan",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="desc(Scan.created_at)"
    )
    
    def __repr__(self) -> str:
        return f"<Project {self.name}>"
