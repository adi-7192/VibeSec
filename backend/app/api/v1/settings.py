"""
VibeSec Backend - Settings API Routes

User settings management including LLM configuration.
"""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import DBSession, CurrentUser
from app.core.security import encrypt_api_key, decrypt_api_key, mask_api_key
from app.models.user import LLMProvider
from app.services.llm import get_llm_provider
from app.schemas.user import LLMConfigUpdate, LLMConfigResponse

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/llm", response_model=LLMConfigResponse)
async def get_llm_config(user: CurrentUser):
    """Get LLM configuration (without revealing full API key)."""
    has_key = user.encrypted_llm_api_key is not None
    masked_key = None
    
    if has_key and user.encrypted_llm_api_key:
        try:
            decrypted = decrypt_api_key(user.encrypted_llm_api_key)
            masked_key = mask_api_key(decrypted)
        except:
            masked_key = "****"
    
    return LLMConfigResponse(
        provider=user.llm_provider,
        has_api_key=has_key,
        api_key_masked=masked_key,
    )


@router.put("/llm", response_model=LLMConfigResponse)
async def update_llm_config(
    config: LLMConfigUpdate,
    user: CurrentUser,
    db: DBSession,
):
    """Update LLM configuration."""
    # Encrypt API key
    encrypted_key = encrypt_api_key(config.api_key)
    
    # Update user
    user.llm_provider = config.provider
    user.encrypted_llm_api_key = encrypted_key
    
    await db.commit()
    await db.refresh(user)
    
    return LLMConfigResponse(
        provider=user.llm_provider,
        has_api_key=True,
        api_key_masked=mask_api_key(config.api_key),
    )


@router.post("/llm/validate")
async def validate_llm_key(user: CurrentUser):
    """Validate the stored LLM API key."""
    if not user.encrypted_llm_api_key or not user.llm_provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LLM not configured",
        )
    
    try:
        api_key = decrypt_api_key(user.encrypted_llm_api_key)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to decrypt API key: {str(e)}",
        )
    
    provider = get_llm_provider(user.llm_provider.value, api_key)
    
    try:
        is_valid = await provider.validate_key()
    except Exception as e:
        return {"valid": False, "error": str(e)}
    
    return {"valid": is_valid}


@router.delete("/llm")
async def delete_llm_config(user: CurrentUser, db: DBSession):
    """Remove stored LLM configuration."""
    user.llm_provider = None
    user.encrypted_llm_api_key = None
    
    await db.commit()
    
    return {"message": "LLM configuration removed"}
