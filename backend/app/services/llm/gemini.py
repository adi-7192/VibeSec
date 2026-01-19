"""
VibeSec Backend - Gemini LLM Provider

Google Gemini integration for generating fixes and tests.
"""

import re
import httpx
from typing import Optional

from app.services.llm.base import LLMProvider, FixSuggestion, TestSuggestion


GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_MODEL = "gemini-1.5-flash"


class GeminiProvider(LLMProvider):
    """Gemini LLM provider implementation."""
    
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        super().__init__(api_key)
        self.model = model
        self.base_url = f"{GEMINI_API_URL}/{model}"
    
    async def validate_key(self) -> bool:
        """Validate the Gemini API key."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}:generateContent?key={self.api_key}",
                    json={
                        "contents": [{"parts": [{"text": "Hello"}]}],
                        "generationConfig": {"maxOutputTokens": 10},
                    },
                )
                return response.status_code == 200
        except Exception:
            return False
    
    async def generate_fix(
        self,
        code_snippet: str,
        vulnerability_type: str,
        vulnerability_description: str,
        file_path: str,
        language: str,
    ) -> FixSuggestion:
        """Generate a fix using Gemini."""
        prompt = self._get_fix_prompt(
            code_snippet, vulnerability_type, vulnerability_description, file_path, language
        )
        
        response_text = await self._call_api(prompt)
        
        # Parse response
        fixed_code = self._extract_code_block(response_text, language)
        explanation = self._extract_explanation(response_text)
        
        return FixSuggestion(
            original_code=code_snippet,
            fixed_code=fixed_code,
            explanation=explanation,
            diff=self._generate_simple_diff(code_snippet, fixed_code),
        )
    
    async def generate_test(
        self,
        code_snippet: str,
        vulnerability_type: str,
        file_path: str,
        language: str,
    ) -> TestSuggestion:
        """Generate a test using Gemini."""
        prompt = self._get_test_prompt(code_snippet, vulnerability_type, file_path, language)
        
        response_text = await self._call_api(prompt)
        
        # Parse response
        test_code = self._extract_code_block(response_text, language)
        explanation = self._extract_explanation(response_text)
        framework = "jest" if language in ["javascript", "typescript"] else "pytest"
        
        return TestSuggestion(
            test_code=test_code,
            test_framework=framework,
            explanation=explanation,
        )
    
    async def _call_api(self, prompt: str) -> str:
        """Make a call to the Gemini API."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}:generateContent?key={self.api_key}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 2048,
                    },
                },
            )
            
            if response.status_code != 200:
                error_data = response.json()
                raise Exception(f"Gemini API error: {error_data.get('error', {}).get('message', 'Unknown error')}")
            
            data = response.json()
            
            # Extract text from response
            candidates = data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            
            return ""
    
    def _extract_code_block(self, text: str, language: str) -> str:
        """Extract code block from response."""
        # Try to find fenced code block
        pattern = rf"```(?:{language}|{language[:2]})?\s*\n(.*?)```"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        # Fallback: return text between first ``` and last ```
        if "```" in text:
            parts = text.split("```")
            if len(parts) >= 2:
                return parts[1].strip().lstrip(language).strip()
        
        return text.strip()
    
    def _extract_explanation(self, text: str) -> str:
        """Extract explanation from response."""
        # Look for explanation section
        patterns = [
            r"\*\*Explanation:\*\*\s*(.*?)(?:$|\n\n)",
            r"Explanation:\s*(.*?)(?:$|\n\n)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Fallback: use text after last code block
        if "```" in text:
            parts = text.split("```")
            if len(parts) > 2:
                return parts[-1].strip()
        
        return "Fix applied to address the security vulnerability."
    
    def _generate_simple_diff(self, original: str, fixed: str) -> str:
        """Generate a simple diff between original and fixed code."""
        original_lines = original.splitlines()
        fixed_lines = fixed.splitlines()
        
        diff_lines = []
        for line in original_lines:
            if line not in fixed_lines:
                diff_lines.append(f"- {line}")
        for line in fixed_lines:
            if line not in original_lines:
                diff_lines.append(f"+ {line}")
        
        return "\n".join(diff_lines) if diff_lines else "No changes detected"
