"""
VibeSec Backend - SCA Service

Software Composition Analysis using OSV (Open Source Vulnerabilities) database.
"""

import json
import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
import httpx

from app.models.finding import Severity, FindingCategory


OSV_API_URL = "https://api.osv.dev/v1/query"


@dataclass
class SCAFinding:
    """A finding from SCA analysis."""
    package_name: str
    package_version: str
    vulnerability_id: str
    title: str
    description: str
    severity: Severity
    fixed_version: Optional[str] = None
    cve_id: Optional[str] = None
    cwe_id: Optional[str] = None
    references: list[str] = field(default_factory=list)


@dataclass
class SCAResult:
    """Result of SCA analysis."""
    findings: list[SCAFinding] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    packages_scanned: int = 0
    vulnerable_packages: int = 0


def _map_osv_severity(severity_data: dict) -> Severity:
    """Map OSV severity to our severity levels."""
    # OSV can have CVSS score or severity string
    score = severity_data.get("score")
    if score is not None:
        if score >= 9.0:
            return Severity.CRITICAL
        elif score >= 7.0:
            return Severity.HIGH
        elif score >= 4.0:
            return Severity.MEDIUM
        else:
            return Severity.LOW
    
    severity_type = severity_data.get("type", "").upper()
    if "CRITICAL" in severity_type:
        return Severity.CRITICAL
    elif "HIGH" in severity_type:
        return Severity.HIGH
    elif "MEDIUM" in severity_type or "MODERATE" in severity_type:
        return Severity.MEDIUM
    
    return Severity.MEDIUM  # Default


def _extract_cve(aliases: list[str]) -> Optional[str]:
    """Extract CVE ID from aliases."""
    for alias in aliases:
        if alias.startswith("CVE-"):
            return alias
    return None


class SCAScanner:
    """SCA scanner using OSV API."""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
    
    async def scan(self) -> SCAResult:
        """Run SCA scan on the project."""
        result = SCAResult()
        
        # Collect all dependencies
        packages = []
        
        # Parse JavaScript/TypeScript dependencies
        packages.extend(await self._parse_npm_packages())
        
        # Parse Python dependencies
        packages.extend(await self._parse_python_packages())
        
        result.packages_scanned = len(packages)
        
        if not packages:
            return result
        
        # Query OSV for vulnerabilities
        vulnerable_pkgs = set()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for pkg in packages:
                try:
                    vulns = await self._query_osv(client, pkg["ecosystem"], pkg["name"], pkg["version"])
                    
                    for vuln in vulns:
                        result.findings.append(vuln)
                        vulnerable_pkgs.add(pkg["name"])
                        
                except Exception as e:
                    result.errors.append(f"Error checking {pkg['name']}: {str(e)}")
        
        result.vulnerable_packages = len(vulnerable_pkgs)
        
        return result
    
    async def _parse_npm_packages(self) -> list[dict]:
        """Parse packages from package.json and lock files."""
        packages = []
        
        # Check package-lock.json first (more accurate versions)
        lock_file = self.project_path / "package-lock.json"
        if lock_file.exists():
            try:
                with open(lock_file, 'r') as f:
                    lock_data = json.load(f)
                    
                # Parse v2/v3 lockfile format
                packages_data = lock_data.get("packages", {})
                for pkg_path, pkg_info in packages_data.items():
                    if not pkg_path or pkg_path == "":  # Skip root
                        continue
                    
                    # Extract package name from path (node_modules/package-name)
                    name = pkg_path.replace("node_modules/", "").split("/")[-1]
                    version = pkg_info.get("version")
                    
                    if name and version and not name.startswith("."):
                        packages.append({
                            "ecosystem": "npm",
                            "name": name,
                            "version": version,
                        })
                
                # Also check dependencies in v1 format
                dependencies = lock_data.get("dependencies", {})
                for name, info in dependencies.items():
                    version = info.get("version") if isinstance(info, dict) else None
                    if version:
                        packages.append({
                            "ecosystem": "npm",
                            "name": name,
                            "version": version,
                        })
                        
            except Exception as e:
                pass  # Fall through to package.json
        
        # Fallback to package.json
        if not packages:
            pkg_file = self.project_path / "package.json"
            if pkg_file.exists():
                try:
                    with open(pkg_file, 'r') as f:
                        pkg_data = json.load(f)
                    
                    for deps_key in ["dependencies", "devDependencies"]:
                        deps = pkg_data.get(deps_key, {})
                        for name, version_spec in deps.items():
                            # Clean version spec (remove ^, ~, etc.)
                            version = re.sub(r'^[\^~>=<]+', '', version_spec)
                            if version and not version.startswith("*"):
                                packages.append({
                                    "ecosystem": "npm",
                                    "name": name,
                                    "version": version,
                                })
                except:
                    pass
        
        return packages
    
    async def _parse_python_packages(self) -> list[dict]:
        """Parse packages from requirements.txt and pyproject.toml."""
        packages = []
        
        # Check requirements.txt
        req_file = self.project_path / "requirements.txt"
        if req_file.exists():
            try:
                with open(req_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or line.startswith("-"):
                            continue
                        
                        # Parse package==version format
                        match = re.match(r'^([a-zA-Z0-9_-]+)==([0-9.]+)', line)
                        if match:
                            packages.append({
                                "ecosystem": "PyPI",
                                "name": match.group(1).lower(),
                                "version": match.group(2),
                            })
            except:
                pass
        
        # Check pyproject.toml
        pyproject_file = self.project_path / "pyproject.toml"
        if pyproject_file.exists():
            try:
                import re
                with open(pyproject_file, 'r') as f:
                    content = f.read()
                
                # Simple regex to extract dependencies
                # Format: "package>=1.0.0" or "package==1.0.0"
                deps_match = re.findall(r'"([a-zA-Z0-9_-]+)[>=<]+([0-9.]+)"', content)
                for name, version in deps_match:
                    packages.append({
                        "ecosystem": "PyPI",
                        "name": name.lower(),
                        "version": version,
                    })
            except:
                pass
        
        return packages
    
    async def _query_osv(
        self, client: httpx.AsyncClient, ecosystem: str, package: str, version: str
    ) -> list[SCAFinding]:
        """Query OSV API for vulnerabilities in a package."""
        findings = []
        
        response = await client.post(
            OSV_API_URL,
            json={
                "package": {
                    "ecosystem": ecosystem,
                    "name": package,
                },
                "version": version,
            },
        )
        
        if response.status_code != 200:
            return findings
        
        data = response.json()
        vulns = data.get("vulns", [])
        
        for vuln in vulns:
            # Get severity
            severity = Severity.MEDIUM
            for sev_info in vuln.get("severity", []):
                severity = _map_osv_severity(sev_info)
                break
            
            # Get fixed version
            fixed_version = None
            for affected in vuln.get("affected", []):
                for range_info in affected.get("ranges", []):
                    for event in range_info.get("events", []):
                        if "fixed" in event:
                            fixed_version = event["fixed"]
                            break
            
            # Extract CVE
            aliases = vuln.get("aliases", [])
            cve_id = _extract_cve(aliases)
            
            # Get references
            references = [ref.get("url") for ref in vuln.get("references", []) if ref.get("url")]
            
            finding = SCAFinding(
                package_name=package,
                package_version=version,
                vulnerability_id=vuln.get("id", ""),
                title=vuln.get("summary", f"Vulnerability in {package}"),
                description=vuln.get("details", vuln.get("summary", "")),
                severity=severity,
                fixed_version=fixed_version,
                cve_id=cve_id,
                references=references[:5],  # Limit references
            )
            
            findings.append(finding)
        
        return findings


async def run_sca_scan(project_path: str) -> SCAResult:
    """Run SCA scan on a project."""
    scanner = SCAScanner(project_path)
    return await scanner.scan()
