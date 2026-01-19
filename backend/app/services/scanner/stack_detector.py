"""
VibeSec Backend - Stack Detection Service

Detects the technology stack of a project by analyzing file patterns.
"""

import os
import json
from enum import Enum
from typing import Optional
from dataclasses import dataclass


class StackType(str, Enum):
    """Detected technology stacks."""
    NEXTJS = "nextjs"
    EXPRESS = "express"
    DJANGO = "django"
    FASTAPI = "fastapi"
    UNKNOWN = "unknown"


@dataclass
class StackDetectionResult:
    """Result of stack detection."""
    stack: StackType
    confidence: float  # 0.0 to 1.0
    details: dict


class StackDetector:
    """Service to detect project stack from file structure."""
    
    def __init__(self, project_path: str):
        self.project_path = project_path
    
    def detect(self) -> StackDetectionResult:
        """Detect the stack of the project."""
        # Check for each stack in order of specificity
        
        # Check Next.js first (more specific than general Node)
        nextjs_result = self._check_nextjs()
        if nextjs_result.confidence > 0.7:
            return nextjs_result
        
        # Check FastAPI (more specific than general Python)
        fastapi_result = self._check_fastapi()
        if fastapi_result.confidence > 0.7:
            return fastapi_result
        
        # Check Django
        django_result = self._check_django()
        if django_result.confidence > 0.7:
            return django_result
        
        # Check Express/Node
        express_result = self._check_express()
        if express_result.confidence > 0.7:
            return express_result
        
        # Return the best match if any has decent confidence
        results = [nextjs_result, fastapi_result, django_result, express_result]
        best_result = max(results, key=lambda x: x.confidence)
        
        if best_result.confidence > 0.3:
            return best_result
        
        return StackDetectionResult(
            stack=StackType.UNKNOWN,
            confidence=0.0,
            details={"reason": "No recognizable stack patterns found"}
        )
    
    def _file_exists(self, *paths: str) -> bool:
        """Check if a file exists in the project."""
        return os.path.exists(os.path.join(self.project_path, *paths))
    
    def _read_file(self, *paths: str) -> Optional[str]:
        """Read a file from the project."""
        filepath = os.path.join(self.project_path, *paths)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                return None
        return None
    
    def _check_nextjs(self) -> StackDetectionResult:
        """Check for Next.js project."""
        confidence = 0.0
        details = {}
        
        # Check for next.config.* files
        if self._file_exists("next.config.js") or self._file_exists("next.config.mjs") or self._file_exists("next.config.ts"):
            confidence += 0.4
            details["next_config"] = True
        
        # Check for app or pages directory
        if self._file_exists("app") or self._file_exists("src", "app"):
            confidence += 0.2
            details["app_router"] = True
        elif self._file_exists("pages") or self._file_exists("src", "pages"):
            confidence += 0.2
            details["pages_router"] = True
        
        # Check package.json for next dependency
        package_json = self._read_file("package.json")
        if package_json:
            try:
                pkg = json.loads(package_json)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                if "next" in deps:
                    confidence += 0.3
                    details["next_version"] = deps.get("next")
                if "react" in deps:
                    confidence += 0.1
                    details["react_version"] = deps.get("react")
            except json.JSONDecodeError:
                pass
        
        return StackDetectionResult(
            stack=StackType.NEXTJS,
            confidence=min(confidence, 1.0),
            details=details
        )
    
    def _check_express(self) -> StackDetectionResult:
        """Check for Express.js project."""
        confidence = 0.0
        details = {}
        
        # Check package.json for express dependency
        package_json = self._read_file("package.json")
        if package_json:
            try:
                pkg = json.loads(package_json)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                if "express" in deps:
                    confidence += 0.5
                    details["express_version"] = deps.get("express")
                
                # Additional Node.js indicators
                if "node" in pkg.get("engines", {}):
                    confidence += 0.1
                    
                # Check for common Express patterns
                for dep in ["body-parser", "cors", "helmet", "morgan"]:
                    if dep in deps:
                        confidence += 0.05
                        
            except json.JSONDecodeError:
                pass
        
        # Check for common entry files
        for entry in ["server.js", "index.js", "app.js", "src/server.js", "src/index.js", "src/app.js"]:
            if self._file_exists(entry):
                content = self._read_file(entry) or ""
                if "express" in content.lower() or "require('express')" in content:
                    confidence += 0.2
                    details["entry_file"] = entry
                    break
        
        return StackDetectionResult(
            stack=StackType.EXPRESS,
            confidence=min(confidence, 1.0),
            details=details
        )
    
    def _check_django(self) -> StackDetectionResult:
        """Check for Django project."""
        confidence = 0.0
        details = {}
        
        # Check for manage.py
        if self._file_exists("manage.py"):
            manage_content = self._read_file("manage.py") or ""
            if "django" in manage_content.lower():
                confidence += 0.4
                details["manage_py"] = True
        
        # Check for settings.py patterns
        for pattern in ["settings.py", "config/settings.py", "*/settings.py"]:
            # Simple check without glob
            if self._file_exists("settings.py"):
                settings_content = self._read_file("settings.py") or ""
                if "INSTALLED_APPS" in settings_content or "django" in settings_content.lower():
                    confidence += 0.3
                    details["settings_py"] = True
                    break
        
        # Check requirements.txt for Django
        requirements = self._read_file("requirements.txt")
        if requirements:
            if "django" in requirements.lower():
                confidence += 0.3
                details["in_requirements"] = True
        
        # Check pyproject.toml
        pyproject = self._read_file("pyproject.toml")
        if pyproject:
            if "django" in pyproject.lower():
                confidence += 0.2
                details["in_pyproject"] = True
        
        return StackDetectionResult(
            stack=StackType.DJANGO,
            confidence=min(confidence, 1.0),
            details=details
        )
    
    def _check_fastapi(self) -> StackDetectionResult:
        """Check for FastAPI project."""
        confidence = 0.0
        details = {}
        
        # Check requirements.txt for fastapi
        requirements = self._read_file("requirements.txt")
        if requirements:
            if "fastapi" in requirements.lower():
                confidence += 0.4
                details["in_requirements"] = True
            if "uvicorn" in requirements.lower():
                confidence += 0.1
                details["uses_uvicorn"] = True
        
        # Check pyproject.toml
        pyproject = self._read_file("pyproject.toml")
        if pyproject:
            if "fastapi" in pyproject.lower():
                confidence += 0.3
                details["in_pyproject"] = True
        
        # Check for main.py or app.py with FastAPI imports
        for entry in ["main.py", "app.py", "app/main.py", "src/main.py"]:
            if self._file_exists(entry):
                content = self._read_file(entry) or ""
                if "from fastapi import" in content or "import fastapi" in content.lower():
                    confidence += 0.4
                    details["entry_file"] = entry
                    break
                elif "FastAPI(" in content:
                    confidence += 0.3
                    details["fastapi_app"] = True
                    break
        
        return StackDetectionResult(
            stack=StackType.FASTAPI,
            confidence=min(confidence, 1.0),
            details=details
        )


async def detect_stack(project_path: str) -> StackDetectionResult:
    """Async wrapper for stack detection."""
    detector = StackDetector(project_path)
    return detector.detect()
