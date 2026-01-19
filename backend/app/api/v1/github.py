"""
VibeSec Backend - GitHub API Routes

GitHub OAuth flow and repository management.
"""

import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from app.api.deps import DBSession, CurrentUser
from app.services.github import GitHubService
from app.core.config import get_settings
from app.models.user import User

settings = get_settings()
router = APIRouter(prefix="/github", tags=["github"])

# In-memory state storage (use Redis in production)
_oauth_states: dict[str, int] = {}


@router.get("/auth")
async def github_auth(user: CurrentUser):
    """
    Start GitHub OAuth flow.
    Returns the authorization URL to redirect the user to.
    """
    if not settings.github_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub integration is not configured",
        )
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = user.id
    
    github = GitHubService()
    auth_url = github.get_auth_url(state)
    await github.close()
    
    return {"auth_url": auth_url}


@router.get("/callback")
async def github_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: DBSession = None,
):
    """
    Handle GitHub OAuth callback.
    Exchanges code for token and saves to user.
    """
    # Verify state
    user_id = _oauth_states.pop(state, None)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state parameter",
        )
    
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Exchange code for token
    github = GitHubService()
    try:
        token_data = await github.exchange_code(code)
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=token_data.get("error_description", "Failed to get access token"),
            )
        
        # Get GitHub user info
        github.access_token = access_token
        github_user = await github.get_user()
        
        # Save to user
        user.github_access_token = access_token
        user.github_username = github_user.get("login")
        await db.commit()
        
    finally:
        await github.close()
    
    # Redirect to frontend GitHub repo selection page
    return RedirectResponse(url=f"{settings.cors_origins.split(',')[0]}/projects/new/github")


@router.delete("/disconnect")
async def disconnect_github(user: CurrentUser, db: DBSession):
    """Disconnect GitHub account."""
    user.github_access_token = None
    user.github_username = None
    await db.commit()
    return {"message": "GitHub disconnected"}


@router.get("/repos")
async def list_repos(
    user: CurrentUser,
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
):
    """List repositories accessible to the user."""
    if not user.github_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub account not connected",
        )
    
    github = GitHubService(access_token=user.github_access_token)
    try:
        repos = await github.get_repos(page=page, per_page=per_page)
        
        # Transform to simpler format
        return {
            "repos": [
                {
                    "id": repo["id"],
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "description": repo.get("description"),
                    "html_url": repo["html_url"],
                    "clone_url": repo["clone_url"],
                    "default_branch": repo["default_branch"],
                    "private": repo["private"],
                    "language": repo.get("language"),
                    "updated_at": repo["updated_at"],
                    "stargazers_count": repo.get("stargazers_count", 0),
                }
                for repo in repos
            ],
            "page": page,
            "per_page": per_page,
        }
    finally:
        await github.close()


@router.get("/repos/{owner}/{repo}")
async def get_repo(owner: str, repo: str, user: CurrentUser):
    """Get repository details."""
    if not user.github_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub account not connected",
        )
    
    github = GitHubService(access_token=user.github_access_token)
    try:
        repo_data = await github.get_repo(owner, repo)
        return {
            "id": repo_data["id"],
            "name": repo_data["name"],
            "full_name": repo_data["full_name"],
            "description": repo_data.get("description"),
            "html_url": repo_data["html_url"],
            "clone_url": repo_data["clone_url"],
            "default_branch": repo_data["default_branch"],
            "private": repo_data["private"],
            "language": repo_data.get("language"),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository not found: {str(e)}",
        )
    finally:
        await github.close()
