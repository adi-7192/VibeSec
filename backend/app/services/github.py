"""
VibeSec Backend - GitHub Integration Service

GitHub OAuth and repository management.
"""

import httpx
from typing import Optional
from urllib.parse import urlencode

from app.core.config import get_settings

settings = get_settings()

GITHUB_OAUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_URL = "https://api.github.com"


class GitHubService:
    """Service for GitHub OAuth and API operations."""
    
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token
        self.client = httpx.AsyncClient(
            headers={
                "Accept": "application/json",
                "User-Agent": "VibeSec/1.0",
            },
            timeout=30.0,
        )
    
    async def close(self):
        await self.client.aclose()
    
    def get_auth_url(self, state: str) -> str:
        """Generate GitHub OAuth authorization URL."""
        params = {
            "client_id": settings.github_client_id,
            "redirect_uri": settings.github_redirect_uri,
            "scope": "repo read:user",
            "state": state,
        }
        return f"{GITHUB_OAUTH_URL}?{urlencode(params)}"
    
    async def exchange_code(self, code: str) -> dict:
        """Exchange authorization code for access token."""
        response = await self.client.post(
            GITHUB_TOKEN_URL,
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        return response.json()
    
    async def get_user(self) -> dict:
        """Get authenticated user info."""
        response = await self.client.get(
            f"{GITHUB_API_URL}/user",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        response.raise_for_status()
        return response.json()
    
    async def get_repos(self, page: int = 1, per_page: int = 30) -> list[dict]:
        """List repositories accessible to the authenticated user."""
        response = await self.client.get(
            f"{GITHUB_API_URL}/user/repos",
            params={
                "page": page,
                "per_page": per_page,
                "sort": "updated",
                "direction": "desc",
                "type": "all",
            },
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        response.raise_for_status()
        return response.json()
    
    async def get_repo(self, owner: str, repo: str) -> dict:
        """Get repository details."""
        response = await self.client.get(
            f"{GITHUB_API_URL}/repos/{owner}/{repo}",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        response.raise_for_status()
        return response.json()
    
    async def get_repo_contents(
        self, owner: str, repo: str, path: str = "", ref: Optional[str] = None
    ) -> list[dict]:
        """Get repository contents at a path."""
        params = {}
        if ref:
            params["ref"] = ref
        
        response = await self.client.get(
            f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{path}",
            params=params,
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else [data]
    
    async def get_file_content(
        self, owner: str, repo: str, path: str, ref: Optional[str] = None
    ) -> str:
        """Get raw file content."""
        params = {}
        if ref:
            params["ref"] = ref
        
        response = await self.client.get(
            f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{path}",
            params=params,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/vnd.github.raw+json",
            },
        )
        response.raise_for_status()
        return response.text
    
    async def get_default_branch(self, owner: str, repo: str) -> str:
        """Get the default branch of a repository."""
        repo_info = await self.get_repo(owner, repo)
        return repo_info.get("default_branch", "main")
    
    async def create_branch(
        self, owner: str, repo: str, branch_name: str, from_sha: str
    ) -> dict:
        """Create a new branch."""
        response = await self.client.post(
            f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/refs",
            json={
                "ref": f"refs/heads/{branch_name}",
                "sha": from_sha,
            },
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        response.raise_for_status()
        return response.json()
    
    async def create_commit(
        self,
        owner: str,
        repo: str,
        branch: str,
        message: str,
        files: list[dict],
    ) -> dict:
        """
        Create a commit with file changes.
        
        files: list of {"path": "...", "content": "..."}
        """
        # Get current commit SHA
        ref_response = await self.client.get(
            f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/ref/heads/{branch}",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        ref_response.raise_for_status()
        current_sha = ref_response.json()["object"]["sha"]
        
        # Get current tree
        commit_response = await self.client.get(
            f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/commits/{current_sha}",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        commit_response.raise_for_status()
        tree_sha = commit_response.json()["tree"]["sha"]
        
        # Create blobs for files
        tree_items = []
        for file in files:
            blob_response = await self.client.post(
                f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/blobs",
                json={"content": file["content"], "encoding": "utf-8"},
                headers={"Authorization": f"Bearer {self.access_token}"},
            )
            blob_response.raise_for_status()
            blob_sha = blob_response.json()["sha"]
            tree_items.append({
                "path": file["path"],
                "mode": "100644",
                "type": "blob",
                "sha": blob_sha,
            })
        
        # Create tree
        tree_response = await self.client.post(
            f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/trees",
            json={"base_tree": tree_sha, "tree": tree_items},
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        tree_response.raise_for_status()
        new_tree_sha = tree_response.json()["sha"]
        
        # Create commit
        new_commit_response = await self.client.post(
            f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/commits",
            json={
                "message": message,
                "tree": new_tree_sha,
                "parents": [current_sha],
            },
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        new_commit_response.raise_for_status()
        new_commit_sha = new_commit_response.json()["sha"]
        
        # Update branch reference
        await self.client.patch(
            f"{GITHUB_API_URL}/repos/{owner}/{repo}/git/refs/heads/{branch}",
            json={"sha": new_commit_sha},
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        
        return new_commit_response.json()
    
    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str,
    ) -> dict:
        """Create a pull request."""
        response = await self.client.post(
            f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls",
            json={
                "title": title,
                "body": body,
                "head": head,
                "base": base,
            },
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        response.raise_for_status()
        return response.json()
    
    async def download_repo_archive(
        self, owner: str, repo: str, ref: str = "main"
    ) -> bytes:
        """Download repository as tarball."""
        response = await self.client.get(
            f"{GITHUB_API_URL}/repos/{owner}/{repo}/tarball/{ref}",
            headers={"Authorization": f"Bearer {self.access_token}"},
            follow_redirects=True,
        )
        response.raise_for_status()
        return response.content
