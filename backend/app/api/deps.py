"""
VibeSec Backend - API Dependencies

Common dependencies for API routes.
"""

from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.firebase import verify_firebase_token, get_user_from_token
from app.models.user import User

# Security scheme for Bearer token
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Dependency to get the current authenticated user.
    
    Verifies Firebase token and returns the corresponding User from database.
    Creates user if they don't exist (first login).
    
    Args:
        credentials: Bearer token from Authorization header.
        db: Database session.
        
    Returns:
        User object for the authenticated user.
        
    Raises:
        HTTPException: If authentication fails.
    """
    token = credentials.credentials
    
    # Verify Firebase token
    decoded_token = await verify_firebase_token(token)
    user_info = get_user_from_token(decoded_token)
    
    # Look up user in database
    result = await db.execute(
        select(User).where(User.firebase_uid == user_info["firebase_uid"])
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        # Create new user on first login
        user = User(
            firebase_uid=user_info["firebase_uid"],
            email=user_info["email"],
            name=user_info.get("name"),
            picture=user_info.get("picture"),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    return user


# Type alias for dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
DBSession = Annotated[AsyncSession, Depends(get_db)]
