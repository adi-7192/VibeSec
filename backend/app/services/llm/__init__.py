"""VibeSec Backend - LLM Services"""

from app.services.llm.base import LLMProvider, FixSuggestion, TestSuggestion
from app.services.llm.gemini import GeminiProvider
from app.services.llm.openai import OpenAIProvider


def get_llm_provider(provider: str, api_key: str) -> LLMProvider:
    """
    Get an LLM provider instance.
    
    Args:
        provider: Provider name ('gemini' or 'openai')
        api_key: API key for the provider
        
    Returns:
        LLM provider instance
    """
    if provider == "gemini":
        return GeminiProvider(api_key)
    elif provider == "openai":
        return OpenAIProvider(api_key)
    else:
        raise ValueError(f"Unknown provider: {provider}")


__all__ = [
    "LLMProvider",
    "FixSuggestion",
    "TestSuggestion",
    "GeminiProvider",
    "OpenAIProvider",
    "get_llm_provider",
]
