"""VibeSec Backend - API v1 Routes"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.projects import router as projects_router
from app.api.v1.github import router as github_router
from app.api.v1.scans import router as scans_router
from app.api.v1.settings import router as settings_router
from app.api.v1.fixes import router as fixes_router
from app.api.v1.ci import router as ci_router
from app.api.v1.demo import router as demo_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(github_router)
api_router.include_router(scans_router)
api_router.include_router(settings_router)
api_router.include_router(fixes_router)
api_router.include_router(ci_router)
api_router.include_router(demo_router)


