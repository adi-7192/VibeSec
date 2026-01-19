"""
VibeSec Backend - SAST Service

Static Application Security Testing using Semgrep.
"""

import os
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

from app.models.finding import Severity, FindingCategory


@dataclass
class SASTFinding:
    """A finding from SAST analysis."""
    rule_id: str
    title: str
    description: str
    severity: Severity
    category: FindingCategory
    file_path: str
    line_start: int
    line_end: int
    code_snippet: str
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None


@dataclass
class SASTResult:
    """Result of SAST analysis."""
    findings: list[SASTFinding] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    files_scanned: int = 0
    duration_seconds: float = 0.0


def _map_semgrep_severity(severity: str) -> Severity:
    """Map Semgrep severity to our severity levels."""
    mapping = {
        "ERROR": Severity.HIGH,
        "WARNING": Severity.MEDIUM,
        "INFO": Severity.LOW,
        "INVENTORY": Severity.INFO,
    }
    return mapping.get(severity.upper(), Severity.MEDIUM)


def _categorize_rule(rule_id: str, message: str) -> FindingCategory:
    """Categorize a finding based on rule ID and message."""
    rule_lower = rule_id.lower()
    message_lower = message.lower()
    
    if any(k in rule_lower or k in message_lower for k in ["sql", "injection", "sqli"]):
        return FindingCategory.INJECTION
    elif any(k in rule_lower or k in message_lower for k in ["xss", "cross-site", "script"]):
        return FindingCategory.XSS
    elif any(k in rule_lower or k in message_lower for k in ["secret", "password", "api_key", "token", "credential", "hardcoded"]):
        return FindingCategory.SECRETS
    elif any(k in rule_lower or k in message_lower for k in ["auth", "session", "jwt", "cookie"]):
        return FindingCategory.AUTH
    elif any(k in rule_lower or k in message_lower for k in ["valid", "sanitiz", "input", "escape"]):
        return FindingCategory.VALIDATION
    elif any(k in rule_lower or k in message_lower for k in ["crypto", "encrypt", "hash", "random"]):
        return FindingCategory.CRYPTO
    elif any(k in rule_lower or k in message_lower for k in ["config", "env", "setting"]):
        return FindingCategory.CONFIG
    else:
        return FindingCategory.OTHER


def _extract_cwe(metadata: dict) -> Optional[str]:
    """Extract CWE ID from Semgrep metadata."""
    cwe = metadata.get("cwe", [])
    if isinstance(cwe, list) and cwe:
        # Format: "CWE-89: SQL Injection"
        cwe_str = cwe[0]
        if "CWE-" in cwe_str:
            return cwe_str.split(":")[0].strip()
    elif isinstance(cwe, str):
        return cwe.split(":")[0].strip()
    return None


def _extract_owasp(metadata: dict) -> Optional[str]:
    """Extract OWASP category from Semgrep metadata."""
    owasp = metadata.get("owasp", [])
    if isinstance(owasp, list) and owasp:
        return owasp[0]
    elif isinstance(owasp, str):
        return owasp
    return None


class SASTScanner:
    """SAST scanner using Semgrep."""
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.custom_rules_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "semgrep-rules"
        )
    
    async def scan(self, languages: Optional[list[str]] = None) -> SASTResult:
        """
        Run SAST scan on the project.
        
        Args:
            languages: Optional list of languages to scan (e.g., ["python", "javascript"])
        """
        result = SASTResult()
        
        try:
            # Build Semgrep command
            cmd = [
                "semgrep",
                "scan",
                "--json",
                "--quiet",
                "--config=auto",  # Use Semgrep's recommended rules
            ]
            
            # Add custom rules if they exist
            if os.path.exists(self.custom_rules_path):
                cmd.extend(["--config", self.custom_rules_path])
            
            # Add language-specific configs
            if languages:
                for lang in languages:
                    if lang.lower() in ["javascript", "typescript", "js", "ts"]:
                        cmd.extend(["--config=p/javascript", "--config=p/typescript"])
                    elif lang.lower() in ["python", "py"]:
                        cmd.extend(["--config=p/python"])
            
            cmd.append(self.project_path)
            
            # Run Semgrep
            import time
            start_time = time.time()
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
            )
            
            result.duration_seconds = time.time() - start_time
            
            # Handle errors
            if process.returncode not in [0, 1]:  # 1 means findings found
                if process.stderr:
                    result.errors.append(process.stderr)
                return result
            
            # Parse results
            if process.stdout:
                try:
                    output = json.loads(process.stdout)
                    result = self._parse_semgrep_output(output, result)
                except json.JSONDecodeError as e:
                    result.errors.append(f"Failed to parse Semgrep output: {e}")
            
        except subprocess.TimeoutExpired:
            result.errors.append("Scan timeout (exceeded 10 minutes)")
        except FileNotFoundError:
            result.errors.append("Semgrep not installed. Install with: pip install semgrep")
        except Exception as e:
            result.errors.append(f"Scan error: {str(e)}")
        
        return result
    
    def _parse_semgrep_output(self, output: dict, result: SASTResult) -> SASTResult:
        """Parse Semgrep JSON output into SASTResult."""
        
        results = output.get("results", [])
        errors = output.get("errors", [])
        
        # Track files scanned
        paths = set()
        
        for finding in results:
            try:
                path = finding.get("path", "")
                paths.add(path)
                
                # Get code snippet
                start_line = finding.get("start", {}).get("line", 1)
                end_line = finding.get("end", {}).get("line", start_line)
                
                extra = finding.get("extra", {})
                lines = extra.get("lines", "")
                message = extra.get("message", "")
                severity_str = extra.get("severity", "WARNING")
                metadata = extra.get("metadata", {})
                
                rule_id = finding.get("check_id", "unknown")
                
                sast_finding = SASTFinding(
                    rule_id=rule_id,
                    title=self._generate_title(rule_id, message),
                    description=message,
                    severity=_map_semgrep_severity(severity_str),
                    category=_categorize_rule(rule_id, message),
                    file_path=path,
                    line_start=start_line,
                    line_end=end_line,
                    code_snippet=lines,
                    cwe_id=_extract_cwe(metadata),
                    owasp_category=_extract_owasp(metadata),
                )
                
                result.findings.append(sast_finding)
                
            except Exception as e:
                result.errors.append(f"Error parsing finding: {e}")
        
        result.files_scanned = len(paths)
        
        # Add parse errors
        for error in errors:
            if isinstance(error, dict):
                result.errors.append(error.get("message", str(error)))
            else:
                result.errors.append(str(error))
        
        return result
    
    def _generate_title(self, rule_id: str, message: str) -> str:
        """Generate a concise title for a finding."""
        # Extract meaningful part from rule_id
        # e.g., "python.django.sql.sql-injection" -> "SQL Injection"
        parts = rule_id.split(".")
        if parts:
            title_part = parts[-1].replace("-", " ").replace("_", " ").title()
            if len(title_part) > 5:
                return title_part
        
        # Fall back to first line of message
        first_line = message.split("\n")[0]
        if len(first_line) > 80:
            return first_line[:77] + "..."
        return first_line


async def run_sast_scan(project_path: str, languages: Optional[list[str]] = None) -> SASTResult:
    """Run SAST scan on a project."""
    scanner = SASTScanner(project_path)
    return await scanner.scan(languages)
