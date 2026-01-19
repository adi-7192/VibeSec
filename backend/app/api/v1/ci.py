"""
VibeSec Backend - GitHub Actions API Routes

Workflow generation and CI/CD integration.
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import Optional

from app.api.deps import CurrentUser
from app.services.github_actions import (
    WorkflowConfig, 
    generate_vibesec_workflow,
    generate_pr_check_workflow,
    generate_setup_instructions,
)
from app.core.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/ci", tags=["ci/cd"])


class WorkflowRequest(BaseModel):
    """Request to generate a workflow."""
    project_id: int
    scan_on_push: bool = True
    scan_on_pr: bool = True
    branches: list[str] = ["main", "master"]
    fail_on_critical: bool = True
    fail_on_high: bool = False
    min_score: Optional[int] = None


class WorkflowResponse(BaseModel):
    """Generated workflow response."""
    workflow_yaml: str
    setup_instructions: str
    filename: str


@router.post("/workflow", response_model=WorkflowResponse)
async def generate_workflow(request: WorkflowRequest, user: CurrentUser):
    """Generate a GitHub Actions workflow for a project."""
    
    # Build API URL
    api_url = settings.cors_origins.split(",")[0].replace(":3000", ":8000") if settings.cors_origins else "https://api.vibesec.dev"
    
    config = WorkflowConfig(
        project_name=f"project-{request.project_id}",
        api_url=api_url,
        api_token="VIBESEC_API_TOKEN",  # Will use secret
        scan_on_push=request.scan_on_push,
        scan_on_pr=request.scan_on_pr,
        branches=request.branches,
        fail_on_critical=request.fail_on_critical,
        fail_on_high=request.fail_on_high,
        min_score=request.min_score,
    )
    
    workflow_yaml = generate_vibesec_workflow(config)
    instructions = generate_setup_instructions(config.project_name)
    
    return WorkflowResponse(
        workflow_yaml=workflow_yaml,
        setup_instructions=instructions,
        filename=".github/workflows/vibesec.yml",
    )


@router.get("/workflow/simple")
async def get_simple_workflow(user: CurrentUser):
    """Get a simple PR check workflow."""
    api_url = settings.cors_origins.split(",")[0].replace(":3000", ":8000") if settings.cors_origins else "https://api.vibesec.dev"
    
    return {
        "workflow_yaml": generate_pr_check_workflow(api_url),
        "filename": ".github/workflows/vibesec-pr.yml",
    }


@router.get("/workflow/download", response_class=PlainTextResponse)
async def download_workflow(
    project_id: int,
    user: CurrentUser,
    fail_on_critical: bool = True,
    fail_on_high: bool = False,
    min_score: Optional[int] = None,
):
    """Download workflow as YAML file."""
    api_url = settings.cors_origins.split(",")[0].replace(":3000", ":8000") if settings.cors_origins else "https://api.vibesec.dev"
    
    config = WorkflowConfig(
        project_name=f"project-{project_id}",
        api_url=api_url,
        api_token="VIBESEC_API_TOKEN",
        fail_on_critical=fail_on_critical,
        fail_on_high=fail_on_high,
        min_score=min_score,
    )
    
    return generate_vibesec_workflow(config)
