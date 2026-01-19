"""
VibeSec Backend - Security Utilities

Encryption for API keys and other sensitive data.
"""

import base64
import os
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import get_settings

settings = get_settings()


def get_encryption_key() -> bytes:
    """
    Get the encryption key from settings or generate a warning.
    
    Returns:
        32-byte encryption key.
    """
    if settings.encryption_key:
        # Convert hex string to bytes
        return bytes.fromhex(settings.encryption_key)
    else:
        # Derive key from secret_key (not recommended for production)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"vibesec-salt",  # In production, use a proper random salt
            iterations=100000,
        )
        return kdf.derive(settings.secret_key.encode())


def encrypt_api_key(api_key: str) -> str:
    """
    Encrypt an API key using AES-256-GCM.
    
    Args:
        api_key: The plaintext API key to encrypt.
        
    Returns:
        Base64-encoded encrypted data (nonce + ciphertext).
    """
    key = get_encryption_key()
    aesgcm = AESGCM(key)
    
    # Generate a random 12-byte nonce
    nonce = os.urandom(12)
    
    # Encrypt the API key
    ciphertext = aesgcm.encrypt(nonce, api_key.encode(), None)
    
    # Combine nonce and ciphertext, then base64 encode
    encrypted_data = nonce + ciphertext
    return base64.b64encode(encrypted_data).decode()


def decrypt_api_key(encrypted_data: str) -> str:
    """
    Decrypt an encrypted API key.
    
    Args:
        encrypted_data: Base64-encoded encrypted data.
        
    Returns:
        The decrypted API key.
        
    Raises:
        ValueError: If decryption fails.
    """
    key = get_encryption_key()
    aesgcm = AESGCM(key)
    
    # Decode base64
    data = base64.b64decode(encrypted_data)
    
    # Extract nonce (first 12 bytes) and ciphertext
    nonce = data[:12]
    ciphertext = data[12:]
    
    # Decrypt
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode()
    except Exception as e:
        raise ValueError(f"Failed to decrypt API key: {e}")


def generate_secret_key(length: int = 32) -> str:
    """
    Generate a cryptographically secure secret key.
    
    Args:
        length: Length of the key in bytes.
        
    Returns:
        Hex-encoded secret key.
    """
    return secrets.token_hex(length)


def mask_api_key(api_key: str) -> str:
    """
    Mask an API key for display purposes.
    
    Args:
        api_key: The API key to mask.
        
    Returns:
        Masked API key (e.g., "sk-...abc123").
    """
    if len(api_key) <= 10:
        return "*" * len(api_key)
    
    prefix = api_key[:4]
    suffix = api_key[-6:]
    return f"{prefix}...{suffix}"
