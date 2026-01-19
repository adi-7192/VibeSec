"""
VibeSec Backend - Demo Data Service

Creates demo projects and findings for new users.
"""

from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.project import Project, SourceType, StackType
from app.models.scan import Scan, ScanStatus
from app.models.finding import Finding, FindingType, Severity, FindingCategory


DEMO_SAST_FINDINGS = [
    {
        "finding_type": FindingType.SAST,
        "severity": Severity.CRITICAL,
        "category": FindingCategory.SECRETS,
        "title": "Hardcoded API Key Detected",
        "description": "A hardcoded API key was found in the source code. This key could be exposed if the code is shared or the repository becomes public.",
        "file_path": "src/lib/api-client.ts",
        "line_start": 15,
        "line_end": 15,
        "code_snippet": 'const API_KEY = "sk-prod-abc123xyz789...";',
        "cwe_id": "CWE-798",
        "rule_id": "secrets.hardcoded-api-key",
    },
    {
        "finding_type": FindingType.SAST,
        "severity": Severity.HIGH,
        "category": FindingCategory.INJECTION,
        "title": "SQL Injection Vulnerability",
        "description": "User input is directly concatenated into a SQL query without sanitization, allowing potential SQL injection attacks.",
        "file_path": "src/api/users.ts",
        "line_start": 42,
        "line_end": 44,
        "code_snippet": 'const query = `SELECT * FROM users WHERE id = ${userId}`;',
        "cwe_id": "CWE-89",
        "rule_id": "javascript.sql-injection",
    },
    {
        "finding_type": FindingType.SAST,
        "severity": Severity.HIGH,
        "category": FindingCategory.XSS,
        "title": "Cross-Site Scripting (XSS)",
        "description": "User-controlled data is rendered as HTML without proper escaping, potentially allowing XSS attacks.",
        "file_path": "src/components/Comment.tsx",
        "line_start": 28,
        "line_end": 28,
        "code_snippet": '<div dangerouslySetInnerHTML={{ __html: userComment }} />',
        "cwe_id": "CWE-79",
        "rule_id": "react.xss-dangerouslysetinnerhtml",
    },
    {
        "finding_type": FindingType.SAST,
        "severity": Severity.MEDIUM,
        "category": FindingCategory.AUTH,
        "title": "Missing CSRF Protection",
        "description": "State-changing operation lacks CSRF token validation, making it vulnerable to cross-site request forgery attacks.",
        "file_path": "src/api/settings.ts",
        "line_start": 18,
        "line_end": 25,
        "code_snippet": "export async function updateSettings(data) {\n  return fetch('/api/settings', { method: 'POST', body: data });\n}",
        "cwe_id": "CWE-352",
        "rule_id": "javascript.csrf-missing",
    },
    {
        "finding_type": FindingType.SAST,
        "severity": Severity.MEDIUM,
        "category": FindingCategory.VALIDATION,
        "title": "Missing Input Validation",
        "description": "User input is used without validation, potentially allowing unexpected data to be processed.",
        "file_path": "src/api/upload.ts",
        "line_start": 12,
        "line_end": 15,
        "code_snippet": "const { filename, size } = req.body;\nfs.writeFileSync(`/uploads/${filename}`, data);",
        "cwe_id": "CWE-20",
        "rule_id": "javascript.path-traversal",
    },
]

DEMO_SCA_FINDINGS = [
    {
        "finding_type": FindingType.SCA,
        "severity": Severity.CRITICAL,
        "category": FindingCategory.DEPENDENCY,
        "title": "Prototype Pollution in lodash",
        "description": "Versions of lodash before 4.17.21 are vulnerable to Prototype Pollution via the `set` and `setWith` functions.",
        "package_name": "lodash",
        "package_version": "4.17.15",
        "fixed_version": "4.17.21",
        "cve_id": "CVE-2020-8203",
    },
    {
        "finding_type": FindingType.SCA,
        "severity": Severity.HIGH,
        "category": FindingCategory.DEPENDENCY,
        "title": "Regular Expression Denial of Service in axios",
        "description": "Axios before 1.6.0 is vulnerable to ReDoS (Regular Expression Denial of Service) via crafted HTTP headers.",
        "package_name": "axios",
        "package_version": "0.21.1",
        "fixed_version": "1.6.0",
        "cve_id": "CVE-2023-45857",
    },
    {
        "finding_type": FindingType.SCA,
        "severity": Severity.MEDIUM,
        "category": FindingCategory.DEPENDENCY,
        "title": "Denial of Service in express",
        "description": "Express versions before 4.19.2 are vulnerable to denial of service via malformed HTTP headers.",
        "package_name": "express",
        "package_version": "4.17.1",
        "fixed_version": "4.19.2",
        "cve_id": "CVE-2024-29041",
    },
]

DEMO_DOMAIN_SCORES = {
    "security": {"score": 55.0, "issues": 8},
    "testing": {"score": 45.0, "issues": 3},
    "reliability": {"score": 70.0, "issues": 2},
    "observability": {"score": 40.0, "issues": 4},
    "performance": {"score": 75.0, "issues": 1},
    "infrastructure": {"score": 60.0, "issues": 2},
}


async def create_demo_project(db: AsyncSession, user: User) -> Project:
    """Create a demo project with sample scan data."""
    
    # Create demo project
    project = Project(
        user_id=user.id,
        name="Demo E-commerce App",
        description="A sample Next.js e-commerce application with intentional security issues for demonstration.",
        source_type=SourceType.DEMO,
        stack=StackType.NEXTJS,
    )
    
    db.add(project)
    await db.flush()
    
    # Create demo scan
    scan = Scan(
        project_id=project.id,
        status=ScanStatus.COMPLETED,
        branch="main",
        progress=100,
        started_at=datetime.utcnow() - timedelta(minutes=5),
        completed_at=datetime.utcnow(),
        overall_score=57.0,
        domain_scores=DEMO_DOMAIN_SCORES,
        total_findings=len(DEMO_SAST_FINDINGS) + len(DEMO_SCA_FINDINGS),
        critical_count=2,
        high_count=3,
        medium_count=3,
        low_count=0,
    )
    
    db.add(scan)
    await db.flush()
    
    # Update project with scan info
    project.latest_score = scan.overall_score
    project.latest_scan_id = scan.id
    
    # Add demo findings
    for finding_data in DEMO_SAST_FINDINGS:
        finding = Finding(scan_id=scan.id, **finding_data)
        db.add(finding)
    
    for finding_data in DEMO_SCA_FINDINGS:
        finding = Finding(scan_id=scan.id, **finding_data)
        db.add(finding)
    
    await db.commit()
    await db.refresh(project)
    
    return project
