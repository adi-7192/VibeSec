"""
VibeSec Backend - User Model

SQLAlchemy model for users.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class LLMProvider(str, enum.Enum):
    """Supported LLM providers."""
    GEMINI = "gemini"
    OPENAI = "openai"


class User(Base):
    """User model for VibeSec users."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    firebase_uid: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    picture: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    
    # LLM Configuration
    llm_provider: Mapped[Optional[LLMProvider]] = mapped_column(
        SQLEnum(LLMProvider, values_callable=lambda x: [e.value for e in x]), 
        nullable=True,
        default=LLMProvider.GEMINI
    )
    encrypted_llm_api_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # GitHub Integration
    github_access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    github_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
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
    projects: Mapped[list["Project"]] = relationship(
        "Project", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User {self.email}>"
