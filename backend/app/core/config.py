"""
VibeSec Backend - Core Configuration

Environment-based configuration using pydantic-settings.
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application
    app_name: str = "VibeSec"
    debug: bool = False
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/vibesec"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Firebase
    firebase_credentials_path: str = "./firebase-service-account.json"
    
    # GitHub OAuth
    github_client_id: Optional[str] = None
    github_client_secret: Optional[str] = None
    github_redirect_uri: str = "http://localhost:8000/api/v1/github/callback"
    
    # Cloudflare R2 / S3
    r2_access_key_id: Optional[str] = None
    r2_secret_access_key: Optional[str] = None
    r2_endpoint_url: Optional[str] = None
    r2_bucket_name: str = "vibesec-uploads"
    
    # Security
    encryption_key: Optional[str] = None  # For API key encryption
    secret_key: str = "change-me-in-production"
    
    # CORS
    cors_origins: str = "http://localhost:3000"
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
