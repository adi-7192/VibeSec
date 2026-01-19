"""
VibeSec Backend - Pydantic Schemas for Users
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

from app.models.user import LLMProvider


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user."""
    firebase_uid: str


class UserUpdate(BaseModel):
    """Schema for updating user info."""
    name: Optional[str] = None
    picture: Optional[str] = None


class LLMConfigUpdate(BaseModel):
    """Schema for updating LLM configuration."""
    provider: LLMProvider
    api_key: str


class LLMConfigResponse(BaseModel):
    """Response schema for LLM configuration."""
    provider: Optional[LLMProvider] = None
    has_api_key: bool = False
    api_key_masked: Optional[str] = None


class UserResponse(UserBase):
    """Response schema for user."""
    id: int
    picture: Optional[str] = None
    llm_provider: Optional[LLMProvider] = None
    has_llm_key: bool = False
    github_connected: bool = False
    github_username: Optional[str] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class TokenVerifyRequest(BaseModel):
    """Request schema for verifying Firebase token."""
    token: str


class TokenVerifyResponse(BaseModel):
    """Response after token verification."""
    user: UserResponse
    is_new_user: bool = False
