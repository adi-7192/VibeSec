"""
VibeSec Backend - Firebase Authentication

Firebase Admin SDK integration for token verification.
"""

import firebase_admin
from firebase_admin import auth, credentials
from fastapi import HTTPException, status
from typing import Optional
import os

from app.core.config import get_settings

settings = get_settings()

# Initialize Firebase Admin SDK
_firebase_app: Optional[firebase_admin.App] = None


def init_firebase() -> firebase_admin.App:
    """Initialize Firebase Admin SDK."""
    global _firebase_app
    
    if _firebase_app is not None:
        return _firebase_app
    
    cred_path = settings.firebase_credentials_path
    
    if not os.path.exists(cred_path):
        raise RuntimeError(
            f"Firebase credentials file not found at: {cred_path}\n"
            "Please download your Firebase service account JSON and place it at this path."
        )
    
    cred = credentials.Certificate(cred_path)
    _firebase_app = firebase_admin.initialize_app(cred)
    return _firebase_app


def get_firebase_app() -> firebase_admin.App:
    """Get the Firebase app instance."""
    global _firebase_app
    if _firebase_app is None:
        return init_firebase()
    return _firebase_app


async def verify_firebase_token(token: str) -> dict:
    """
    Verify a Firebase ID token and return the decoded claims.
    
    Args:
        token: The Firebase ID token to verify.
        
    Returns:
        Dictionary containing the decoded token claims.
        
    Raises:
        HTTPException: If token is invalid or expired.
    """
    try:
        # Ensure Firebase is initialized
        get_firebase_app()
        
        # Verify the token
        decoded_token = auth.verify_id_token(token)
        return decoded_token
        
    except firebase_admin.exceptions.FirebaseError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Firebase token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_user_from_token(decoded_token: dict) -> dict:
    """
    Extract user information from decoded Firebase token.
    
    Args:
        decoded_token: The decoded Firebase token.
        
    Returns:
        Dictionary with user info (uid, email, name, picture).
    """
    return {
        "firebase_uid": decoded_token.get("uid"),
        "email": decoded_token.get("email"),
        "name": decoded_token.get("name"),
        "picture": decoded_token.get("picture"),
        "email_verified": decoded_token.get("email_verified", False),
    }
