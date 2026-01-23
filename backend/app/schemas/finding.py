"""
VibeSec Backend - Pydantic Schemas for Findings
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.models.finding import FindingType, Severity, FindingCategory


class FindingBase(BaseModel):
    """Base finding schema."""
    finding_type: FindingType
    severity: Severity
    category: FindingCategory
    title: str
    description: str


class FindingResponse(FindingBase):
    """Response schema for finding."""
    id: int
    scan_id: int
    
    # Location (SAST)
    file_path: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    code_snippet: Optional[str] = None
    
    # Package info (SCA)
    package_name: Optional[str] = None
    package_version: Optional[str] = None
    fixed_version: Optional[str] = None
    
    # References
    cwe_id: Optional[str] = None
    cve_id: Optional[str] = None
    owasp_category: Optional[str] = None
    rule_id: Optional[str] = None
    
    # Status
    is_fixed: bool = False
    is_ignored: bool = False

    # User-friendly explanation
    layman_explanation: Optional[str] = None
    
    # LLM-generated content availability
    has_fix_suggestion: bool = False
    has_test_suggestion: bool = False
    
    created_at: datetime
    
    model_config = {"from_attributes": True}


class FindingListResponse(BaseModel):
    """Response schema for finding list."""
    findings: list[FindingResponse]
    total: int
    
    # Aggregations
    by_severity: dict[str, int] = {}
    by_category: dict[str, int] = {}


class FindingFilters(BaseModel):
    """Filters for finding queries."""
    severity: Optional[list[Severity]] = None
    category: Optional[list[FindingCategory]] = None
    finding_type: Optional[FindingType] = None
    is_fixed: Optional[bool] = None
    is_ignored: Optional[bool] = None
    file_path: Optional[str] = None


class FixRequest(BaseModel):
    """Request to generate a fix for a finding."""
    regenerate: bool = False  # Force regeneration even if cached


class FixResponse(BaseModel):
    """Response with generated fix."""
    finding_id: int
    original_code: Optional[str] = None
    fixed_code: str
    explanation: str
    diff: Optional[str] = None


class TestGenerationResponse(BaseModel):
    """Response with generated test."""
    finding_id: int
    test_code: str
    test_framework: str  # e.g., "jest", "pytest"
    explanation: str
