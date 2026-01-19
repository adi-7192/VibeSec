"""
VibeSec Backend - Scoring Engine

Calculates production readiness scores across domains.
"""

from dataclasses import dataclass
from typing import Optional
import re
import os


@dataclass
class DomainScore:
    """Score for a specific domain."""
    score: float  # 0-100
    weight: float
    issues: int
    details: dict


@dataclass
class ReadinessScore:
    """Complete readiness score breakdown."""
    overall: float
    security: DomainScore
    testing: DomainScore
    reliability: DomainScore
    observability: DomainScore
    performance: DomainScore
    infrastructure: DomainScore
    
    @property
    def status(self) -> str:
        """Get status label based on overall score."""
        if self.overall >= 85:
            return "ready"
        elif self.overall >= 60:
            return "needs_work"
        else:
            return "not_ready"


class ScoringEngine:
    """Engine for calculating production readiness scores."""
    
    # Domain weights (should sum to 1.0)
    WEIGHTS = {
        "security": 0.25,
        "testing": 0.20,
        "reliability": 0.20,
        "observability": 0.15,
        "performance": 0.10,
        "infrastructure": 0.10,
    }
    
    def __init__(
        self,
        project_path: str,
        sast_findings: list = None,
        sca_findings: list = None,
    ):
        self.project_path = project_path
        self.sast_findings = sast_findings or []
        self.sca_findings = sca_findings or []
    
    def calculate(self) -> ReadinessScore:
        """Calculate the complete readiness score."""
        
        security = self._score_security()
        testing = self._score_testing()
        reliability = self._score_reliability()
        observability = self._score_observability()
        performance = self._score_performance()
        infrastructure = self._score_infrastructure()
        
        # Calculate weighted overall score
        overall = (
            security.score * security.weight +
            testing.score * testing.weight +
            reliability.score * reliability.weight +
            observability.score * observability.weight +
            performance.score * performance.weight +
            infrastructure.score * infrastructure.weight
        )
        
        return ReadinessScore(
            overall=round(overall, 1),
            security=security,
            testing=testing,
            reliability=reliability,
            observability=observability,
            performance=performance,
            infrastructure=infrastructure,
        )
    
    def _score_security(self) -> DomainScore:
        """Calculate security score based on SAST/SCA findings."""
        base_score = 100.0
        issues = 0
        details = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "sast_findings": len(self.sast_findings),
            "sca_findings": len(self.sca_findings),
        }
        
        # Deduct points based on finding severity
        severity_penalties = {
            "critical": 20,
            "high": 10,
            "medium": 3,
            "low": 1,
        }
        
        for finding in self.sast_findings:
            if hasattr(finding, 'severity'):
                severity = finding.severity
            elif isinstance(finding, dict):
                severity = finding.get('severity', 'medium')
            else:
                severity = 'medium'

            if hasattr(severity, 'value'):
                severity = severity.value
            
            penalty = severity_penalties.get(severity.lower(), 2)
            base_score -= penalty
            details[severity.lower()] = details.get(severity.lower(), 0) + 1
            issues += 1
        
        for finding in self.sca_findings:
            if hasattr(finding, 'severity'):
                severity = finding.severity
            elif isinstance(finding, dict):
                severity = finding.get('severity', 'medium')
            else:
                severity = 'medium'

            if hasattr(severity, 'value'):
                severity = severity.value
            
            penalty = severity_penalties.get(severity.lower(), 2)
            base_score -= penalty
            details[severity.lower()] = details.get(severity.lower(), 0) + 1
            issues += 1
        
        return DomainScore(
            score=max(0, min(100, base_score)),
            weight=self.WEIGHTS["security"],
            issues=issues,
            details=details,
        )
    
    def _score_testing(self) -> DomainScore:
        """Calculate testing score based on test presence and coverage."""
        score = 50.0  # Start at 50%, improve with evidence
        issues = 0
        details = {
            "test_framework_found": False,
            "test_files_count": 0,
            "coverage_file_found": False,
        }
        
        # Check for test frameworks and files
        test_patterns = {
            "jest": ["jest.config.js", "jest.config.ts", "jest.config.mjs"],
            "pytest": ["pytest.ini", "conftest.py", "setup.cfg"],
            "mocha": [".mocharc.js", ".mocharc.json"],
            "vitest": ["vitest.config.ts", "vitest.config.js"],
        }
        
        for framework, config_files in test_patterns.items():
            for config in config_files:
                if self._file_exists(config):
                    details["test_framework_found"] = True
                    details["framework"] = framework
                    score += 15
                    break
            if details["test_framework_found"]:
                break
        
        # Count test files
        test_file_count = self._count_files_matching(
            r'(\.test\.|\.spec\.|_test\.py|test_.*\.py|__tests__)'
        )
        details["test_files_count"] = test_file_count
        
        if test_file_count > 0:
            score += min(20, test_file_count * 2)  # Up to 20 points
        else:
            issues += 1
        
        # Check for coverage files
        coverage_files = ["coverage/", "htmlcov/", ".coverage", "coverage.xml"]
        for cov in coverage_files:
            if self._file_exists(cov):
                details["coverage_file_found"] = True
                score += 15
                break
        
        if not details["coverage_file_found"]:
            issues += 1
        
        return DomainScore(
            score=max(0, min(100, score)),
            weight=self.WEIGHTS["testing"],
            issues=issues,
            details=details,
        )
    
    def _score_reliability(self) -> DomainScore:
        """Calculate reliability score based on error handling patterns."""
        score = 60.0  # Start at 60%
        issues = 0
        details = {
            "error_handling": False,
            "retry_logic": False,
            "env_config": False,
        }
        
        # Search source files for patterns
        source_content = self._read_source_files()
        
        # Check for error handling
        error_patterns = [
            r'try\s*{', r'catch\s*\(', r'\.catch\(',  # JS
            r'try:', r'except\s+', r'except:',  # Python
        ]
        for pattern in error_patterns:
            if re.search(pattern, source_content):
                details["error_handling"] = True
                score += 10
                break
        
        if not details["error_handling"]:
            issues += 1
        
        # Check for retry logic
        retry_patterns = [
            r'retry', r'backoff', r'exponential',
            r'max_retries', r'maxRetries',
        ]
        for pattern in retry_patterns:
            if re.search(pattern, source_content, re.IGNORECASE):
                details["retry_logic"] = True
                score += 15
                break
        
        # Check for environment-based config
        env_patterns = [
            r'process\.env\.', r'os\.environ', r'os\.getenv',
            r'dotenv', r'\.env',
        ]
        for pattern in env_patterns:
            if re.search(pattern, source_content):
                details["env_config"] = True
                score += 15
                break
        
        if not details["env_config"]:
            issues += 1
        
        return DomainScore(
            score=max(0, min(100, score)),
            weight=self.WEIGHTS["reliability"],
            issues=issues,
            details=details,
        )
    
    def _score_observability(self) -> DomainScore:
        """Calculate observability score based on logging and monitoring."""
        score = 50.0
        issues = 0
        details = {
            "structured_logging": False,
            "health_endpoint": False,
            "monitoring": False,
        }
        
        source_content = self._read_source_files()
        
        # Check for logging
        logging_patterns = [
            r'winston', r'pino', r'bunyan', r'log4js',  # JS
            r'import logging', r'from logging',  # Python
            r'console\.log', r'console\.error',  # Basic JS
            r'logger\.',  # Generic
        ]
        for pattern in logging_patterns:
            if re.search(pattern, source_content):
                details["structured_logging"] = True
                score += 20
                break
        
        if not details["structured_logging"]:
            issues += 1
        
        # Check for health endpoints
        health_patterns = [
            r'/health', r'/ready', r'/healthz', r'/readiness',
            r'@app\.get.*health', r'@router\.get.*health',
        ]
        for pattern in health_patterns:
            if re.search(pattern, source_content, re.IGNORECASE):
                details["health_endpoint"] = True
                score += 20
                break
        
        if not details["health_endpoint"]:
            issues += 1
        
        # Check for monitoring tools
        monitoring_patterns = [
            r'sentry', r'datadog', r'newrelic', r'prometheus',
            r'@sentry', r'opentelemetry',
        ]
        for pattern in monitoring_patterns:
            if re.search(pattern, source_content, re.IGNORECASE):
                details["monitoring"] = True
                score += 10
                break
        
        return DomainScore(
            score=max(0, min(100, score)),
            weight=self.WEIGHTS["observability"],
            issues=issues,
            details=details,
        )
    
    def _score_performance(self) -> DomainScore:
        """Calculate performance score based on optimization patterns."""
        score = 70.0  # Start higher as this is often implicit
        issues = 0
        details = {
            "caching": False,
            "async_usage": False,
            "n_plus_one_risk": False,
        }
        
        source_content = self._read_source_files()
        
        # Check for caching
        cache_patterns = [
            r'redis', r'memcached', r'cache', r'lru_cache',
            r'@cache', r'memoize',
        ]
        for pattern in cache_patterns:
            if re.search(pattern, source_content, re.IGNORECASE):
                details["caching"] = True
                score += 15
                break
        
        # Check for async patterns
        async_patterns = [
            r'async\s+function', r'await\s+', r'Promise\.',
            r'async\s+def', r'asyncio',
        ]
        for pattern in async_patterns:
            if re.search(pattern, source_content):
                details["async_usage"] = True
                score += 10
                break
        
        # Check for potential N+1 query patterns (simple heuristic)
        n_plus_one_patterns = [
            r'for.*\n.*\.find\(', r'for.*\n.*\.query\(',
            r'\.map\([^)]*\.find', r'\.forEach\([^)]*query',
        ]
        for pattern in n_plus_one_patterns:
            if re.search(pattern, source_content, re.MULTILINE):
                details["n_plus_one_risk"] = True
                score -= 10
                issues += 1
                break
        
        return DomainScore(
            score=max(0, min(100, score)),
            weight=self.WEIGHTS["performance"],
            issues=issues,
            details=details,
        )
    
    def _score_infrastructure(self) -> DomainScore:
        """Calculate infrastructure score based on CI/CD and config."""
        score = 40.0
        issues = 0
        details = {
            "ci_config": False,
            "dockerfile": False,
            "secrets_in_code": False,
        }
        
        # Check for CI configuration
        ci_files = [
            ".github/workflows",
            ".gitlab-ci.yml",
            "Jenkinsfile",
            ".circleci/config.yml",
            "azure-pipelines.yml",
        ]
        for ci in ci_files:
            if self._file_exists(ci):
                details["ci_config"] = True
                details["ci_system"] = ci.split("/")[0].replace(".", "")
                score += 30
                break
        
        if not details["ci_config"]:
            issues += 1
        
        # Check for Docker
        docker_files = ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"]
        for df in docker_files:
            if self._file_exists(df):
                details["dockerfile"] = True
                score += 20
                break
        
        # Check for hardcoded secrets (negative)
        source_content = self._read_source_files()
        secret_patterns = [
            r'["\']sk-[a-zA-Z0-9]{20,}["\']',  # OpenAI key
            r'["\']AIza[a-zA-Z0-9_-]{35}["\']',  # Google API key
            r'password\s*=\s*["\'][^"\']+["\']',  # Hardcoded password
            r'api_key\s*=\s*["\'][a-zA-Z0-9]{16,}["\']',  # Generic API key
        ]
        for pattern in secret_patterns:
            if re.search(pattern, source_content, re.IGNORECASE):
                details["secrets_in_code"] = True
                score -= 20
                issues += 1
                break
        
        # Add points for environment variable usage
        if re.search(r'process\.env\.|os\.environ|os\.getenv', source_content):
            score += 10
        
        return DomainScore(
            score=max(0, min(100, score)),
            weight=self.WEIGHTS["infrastructure"],
            issues=issues,
            details=details,
        )
    
    def _file_exists(self, path: str) -> bool:
        """Check if a file exists in the project."""
        full_path = os.path.join(self.project_path, path)
        return os.path.exists(full_path)
    
    def _count_files_matching(self, pattern: str) -> int:
        """Count files matching a regex pattern."""
        count = 0
        try:
            for root, dirs, files in os.walk(self.project_path):
                # Skip node_modules and __pycache__
                dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', '.git', 'venv']]
                
                for file in files:
                    if re.search(pattern, file):
                        count += 1
        except:
            pass
        return count
    
    def _read_source_files(self, max_size: int = 1_000_000) -> str:
        """Read source files content for pattern matching."""
        content = []
        total_size = 0
        extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.mjs'}
        
        try:
            for root, dirs, files in os.walk(self.project_path):
                # Skip common non-source directories
                dirs[:] = [d for d in dirs if d not in [
                    'node_modules', '__pycache__', '.git', 'venv', 
                    'dist', 'build', '.next', 'coverage'
                ]]
                
                for file in files:
                    ext = os.path.splitext(file)[1]
                    if ext in extensions:
                        filepath = os.path.join(root, file)
                        try:
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                file_content = f.read(max_size - total_size)
                                content.append(file_content)
                                total_size += len(file_content)
                                
                                if total_size >= max_size:
                                    return '\n'.join(content)
                        except:
                            pass
        except:
            pass
        
        return '\n'.join(content)


async def calculate_readiness_score(
    project_path: str,
    sast_findings: list = None,
    sca_findings: list = None,
) -> ReadinessScore:
    """Calculate production readiness score for a project."""
    engine = ScoringEngine(project_path, sast_findings, sca_findings)
    return engine.calculate()
