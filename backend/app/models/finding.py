"""
VibeSec Backend - Finding Model

SQLAlchemy model for security findings.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, Text, Integer, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.scan import Scan


class FindingType(str, enum.Enum):
    """Type of finding."""
    SAST = "sast"
    SCA = "sca"


class Severity(str, enum.Enum):
    """Finding severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingCategory(str, enum.Enum):
    """Finding categories for grouping."""
    INJECTION = "injection"
    XSS = "xss"
    SECRETS = "secrets"
    AUTH = "auth"
    VALIDATION = "validation"
    CRYPTO = "crypto"
    DEPENDENCY = "dependency"
    CONFIG = "config"
    OTHER = "other"


class Finding(Base):
    """Finding model for security vulnerabilities."""
    
    __tablename__ = "findings"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id"), index=True)
    
    # Type and Severity
    finding_type: Mapped[FindingType] = mapped_column(SQLEnum(FindingType, values_callable=lambda x: [e.value for e in x]))
    severity: Mapped[Severity] = mapped_column(SQLEnum(Severity, values_callable=lambda x: [e.value for e in x]), index=True)
    category: Mapped[FindingCategory] = mapped_column(
        SQLEnum(FindingCategory, values_callable=lambda x: [e.value for e in x]), 
        default=FindingCategory.OTHER
    )
    
    # Location (for SAST)
    file_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    line_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    line_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    code_snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # For SCA (dependency vulnerabilities)
    package_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    package_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    fixed_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Description
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str] = mapped_column(Text)
    
    # References
    cwe_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # e.g., CWE-89
    cve_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # e.g., CVE-2023-1234
    owasp_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Rule info (for SAST)
    rule_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # LLM-generated content (cached)
    fix_suggestion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fix_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    test_suggestion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    is_fixed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_ignored: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow
    )
    
    # Relationships
    scan: Mapped["Scan"] = relationship("Scan", back_populates="findings")
    
    def __repr__(self) -> str:
        return f"<Finding {self.title[:50]} - {self.severity}>"
