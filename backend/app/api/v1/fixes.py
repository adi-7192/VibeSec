"""
VibeSec Backend - Fixes API Routes

LLM-generated fix and test generation.
"""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import DBSession, CurrentUser
from app.core.security import decrypt_api_key
from app.models.finding import Finding
from app.models.scan import Scan
from app.models.project import Project
from app.services.llm import get_llm_provider

router = APIRouter(prefix="/findings", tags=["fixes"])


@router.post("/{finding_id}/fix")
async def generate_fix(
    finding_id: int,
    user: CurrentUser,
    db: DBSession,
    regenerate: bool = False,
):
    """Generate a fix for a finding using LLM."""
    # Get finding with ownership check
    result = await db.execute(
        select(Finding)
        .join(Scan)
        .join(Project)
        .where(Finding.id == finding_id, Project.user_id == user.id)
    )
    finding = result.scalar_one_or_none()
    
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")
    
    # Check if fix already cached
    if finding.fix_suggestion and not regenerate:
        return {
            "finding_id": finding.id,
            "original_code": finding.code_snippet,
            "fixed_code": finding.fix_suggestion,
            "explanation": finding.fix_explanation or "Previously generated fix.",
            "cached": True,
        }
    
    # Check LLM configuration
    if not user.encrypted_llm_api_key or not user.llm_provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LLM not configured. Please add your API key in Settings.",
        )
    
    # Decrypt API key
    try:
        api_key = decrypt_api_key(user.encrypted_llm_api_key)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to decrypt API key. Please reconfigure in Settings.",
        )
    
    # Determine language from file path
    language = "javascript"
    if finding.file_path:
        if finding.file_path.endswith(".py"):
            language = "python"
        elif finding.file_path.endswith((".ts", ".tsx")):
            language = "typescript"
        elif finding.file_path.endswith((".js", ".jsx")):
            language = "javascript"
    
    # Get LLM provider
    provider = get_llm_provider(user.llm_provider.value, api_key)
    
    # Generate fix
    try:
        fix = await provider.generate_fix(
            code_snippet=finding.code_snippet or "",
            vulnerability_type=finding.category.value,
            vulnerability_description=finding.description,
            file_path=finding.file_path or "unknown",
            language=language,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate fix: {str(e)}",
        )
    
    # Cache the fix
    finding.fix_suggestion = fix.fixed_code
    finding.fix_explanation = fix.explanation
    await db.commit()
    
    return {
        "finding_id": finding.id,
        "original_code": fix.original_code,
        "fixed_code": fix.fixed_code,
        "explanation": fix.explanation,
        "diff": fix.diff,
        "cached": False,
    }


@router.post("/{finding_id}/test")
async def generate_test(
    finding_id: int,
    user: CurrentUser,
    db: DBSession,
    regenerate: bool = False,
):
    """Generate a test for a finding using LLM."""
    # Get finding with ownership check
    result = await db.execute(
        select(Finding)
        .join(Scan)
        .join(Project)
        .where(Finding.id == finding_id, Project.user_id == user.id)
    )
    finding = result.scalar_one_or_none()
    
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")
    
    # Check if test already cached
    if finding.test_suggestion and not regenerate:
        return {
            "finding_id": finding.id,
            "test_code": finding.test_suggestion,
            "test_framework": "jest" if finding.file_path and not finding.file_path.endswith(".py") else "pytest",
            "explanation": "Previously generated test.",
            "cached": True,
        }
    
    # Check LLM configuration
    if not user.encrypted_llm_api_key or not user.llm_provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LLM not configured. Please add your API key in Settings.",
        )
    
    # Decrypt API key
    try:
        api_key = decrypt_api_key(user.encrypted_llm_api_key)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to decrypt API key. Please reconfigure in Settings.",
        )
    
    # Determine language
    language = "javascript"
    if finding.file_path:
        if finding.file_path.endswith(".py"):
            language = "python"
        elif finding.file_path.endswith((".ts", ".tsx")):
            language = "typescript"
    
    # Get LLM provider
    provider = get_llm_provider(user.llm_provider.value, api_key)
    
    # Generate test
    try:
        test = await provider.generate_test(
            code_snippet=finding.code_snippet or "",
            vulnerability_type=finding.category.value,
            file_path=finding.file_path or "unknown",
            language=language,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate test: {str(e)}",
        )
    
    # Cache the test
    finding.test_suggestion = test.test_code
    await db.commit()
    
    return {
        "finding_id": finding.id,
        "test_code": test.test_code,
        "test_framework": test.test_framework,
        "explanation": test.explanation,
        "cached": False,
    }
