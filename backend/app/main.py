"""
VibeSec Backend - FastAPI Application

Main application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import get_settings
from app.core.firebase import init_firebase
from app.api.v1 import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting {settings.app_name}...")
    
    # Initialize Firebase (optional - will skip if credentials not found)
    try:
        init_firebase()
        logger.info("Firebase initialized successfully")
    except Exception as e:
        logger.warning(f"Firebase not initialized: {e}")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.app_name}...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Test your vibe-coded apps before launch",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "name": settings.app_name,
        "status": "healthy",
        "version": "0.1.0",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
