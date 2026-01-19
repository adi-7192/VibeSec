"""VibeSec Backend - Schemas"""

from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    LLMConfigUpdate,
    LLMConfigResponse,
    TokenVerifyRequest,
    TokenVerifyResponse,
)
from app.schemas.project import (
    ProjectBase,
    ProjectCreateGitHub,
    ProjectCreateZip,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectWithStats,
)
from app.schemas.scan import (
    ScanCreate,
    ScanProgress,
    ScanResponse,
    ScanListResponse,
    ScanSummary,
    DomainScore,
    DomainScores,
)
from app.schemas.finding import (
    FindingBase,
    FindingResponse,
    FindingListResponse,
    FindingFilters,
    FixRequest,
    FixResponse,
    TestGenerationResponse,
)

__all__ = [
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "LLMConfigUpdate",
    "LLMConfigResponse",
    "TokenVerifyRequest",
    "TokenVerifyResponse",
    # Project
    "ProjectBase",
    "ProjectCreateGitHub",
    "ProjectCreateZip",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectListResponse",
    "ProjectWithStats",
    # Scan
    "ScanCreate",
    "ScanProgress",
    "ScanResponse",
    "ScanListResponse",
    "ScanSummary",
    "DomainScore",
    "DomainScores",
    # Finding
    "FindingBase",
    "FindingResponse",
    "FindingListResponse",
    "FindingFilters",
    "FixRequest",
    "FixResponse",
    "TestGenerationResponse",
]
