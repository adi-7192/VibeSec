"""
VibeSec Backend - LLM Provider Base

Abstract base class and common utilities for LLM providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class FixSuggestion:
    """Generated fix suggestion from LLM."""
    original_code: str
    fixed_code: str
    explanation: str
    diff: Optional[str] = None


@dataclass
class TestSuggestion:
    """Generated test from LLM."""
    test_code: str
    test_framework: str
    explanation: str


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    @abstractmethod
    async def validate_key(self) -> bool:
        """Validate the API key by making a test call."""
        pass
    
    @abstractmethod
    async def generate_fix(
        self,
        code_snippet: str,
        vulnerability_type: str,
        vulnerability_description: str,
        file_path: str,
        language: str,
    ) -> FixSuggestion:
        """Generate a fix for a security vulnerability."""
        pass
    
    @abstractmethod
    async def generate_test(
        self,
        code_snippet: str,
        vulnerability_type: str,
        file_path: str,
        language: str,
    ) -> TestSuggestion:
        """Generate a test case for a vulnerability."""
        pass
    
    def _get_fix_prompt(
        self,
        code_snippet: str,
        vulnerability_type: str,
        vulnerability_description: str,
        file_path: str,
        language: str,
    ) -> str:
        """Generate the prompt for fix generation."""
        return f"""You are a security expert helping to fix a vulnerability in code.

**Vulnerability Type:** {vulnerability_type}
**Description:** {vulnerability_description}
**File:** {file_path}
**Language:** {language}

**Vulnerable Code:**
```{language}
{code_snippet}
```

Please provide:
1. The fixed code that addresses the vulnerability
2. A brief explanation of what was changed and why

Format your response EXACTLY as:
```{language}
[FIXED CODE HERE]
```

**Explanation:**
[Your explanation here]

Focus on:
- Minimal changes to fix the issue
- Following security best practices
- Maintaining code readability
- Not changing unrelated functionality"""

    def _get_test_prompt(
        self,
        code_snippet: str,
        vulnerability_type: str,
        file_path: str,
        language: str,
    ) -> str:
        """Generate the prompt for test generation."""
        framework = "jest" if language in ["javascript", "typescript"] else "pytest"
        
        return f"""You are a security expert creating a test to verify a vulnerability is fixed.

**Vulnerability Type:** {vulnerability_type}
**File:** {file_path}
**Language:** {language}
**Test Framework:** {framework}

**Code to Test:**
```{language}
{code_snippet}
```

Generate a test that:
1. Verifies the vulnerability cannot be exploited
2. Tests both safe and malicious inputs
3. Follows the {framework} testing style

Format your response EXACTLY as:
```{language}
[TEST CODE HERE]
```

**Explanation:**
[Brief explanation of what the test covers]"""
