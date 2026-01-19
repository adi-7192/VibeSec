"""
VibeSec Backend - Auth API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import DBSession, CurrentUser, get_current_user
from app.core.firebase import verify_firebase_token, get_user_from_token
from app.models.user import User
from app.schemas.user import (
    TokenVerifyRequest,
    TokenVerifyResponse,
    UserResponse,
    UserUpdate,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/verify", response_model=TokenVerifyResponse)
async def verify_token(request: TokenVerifyRequest, db: DBSession):
    """
    Verify Firebase ID token and return user info.
    
    Creates user if this is their first login.
    """
    # Verify token
    decoded_token = await verify_firebase_token(request.token)
    user_info = get_user_from_token(decoded_token)
    
    # Check if user exists
    result = await db.execute(
        select(User).where(User.firebase_uid == user_info["firebase_uid"])
    )
    user = result.scalar_one_or_none()
    is_new_user = False
    
    if user is None:
        # Create new user
        user = User(
            firebase_uid=user_info["firebase_uid"],
            email=user_info["email"],
            name=user_info.get("name"),
            picture=user_info.get("picture"),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        is_new_user = True
    else:
        # Update user info if changed
        if user_info.get("name") and user.name != user_info.get("name"):
            user.name = user_info.get("name")
        if user_info.get("picture") and user.picture != user_info.get("picture"):
            user.picture = user_info.get("picture")
        await db.commit()
        await db.refresh(user)
    
    return TokenVerifyResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            picture=user.picture,
            llm_provider=user.llm_provider,
            has_llm_key=user.encrypted_llm_api_key is not None,
            github_connected=user.github_access_token is not None,
            github_username=user.github_username,
            created_at=user.created_at,
        ),
        is_new_user=is_new_user,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: CurrentUser):
    """Get current user info."""
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        picture=user.picture,
        llm_provider=user.llm_provider,
        has_llm_key=user.encrypted_llm_api_key is not None,
        github_connected=user.github_access_token is not None,
        github_username=user.github_username,
        created_at=user.created_at,
    )


@router.patch("/me", response_model=UserResponse)
async def update_me(updates: UserUpdate, user: CurrentUser, db: DBSession):
    """Update current user info."""
    if updates.name is not None:
        user.name = updates.name
    if updates.picture is not None:
        user.picture = updates.picture
    
    await db.commit()
    await db.refresh(user)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        picture=user.picture,
        llm_provider=user.llm_provider,
        has_llm_key=user.encrypted_llm_api_key is not None,
        github_connected=user.github_access_token is not None,
        github_username=user.github_username,
        created_at=user.created_at,
    )
