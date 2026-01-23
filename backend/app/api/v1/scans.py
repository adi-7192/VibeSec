"""
VibeSec Backend - Scan API Routes

Scan management and execution endpoints.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.api.deps import DBSession, CurrentUser
from app.models.project import Project
from app.models.scan import Scan, ScanStatus
from app.models.finding import Finding, FindingType, Severity, FindingCategory
from app.schemas.scan import ScanCreate, ScanResponse, ScanListResponse

router = APIRouter(tags=["scans"])


@router.get("/projects/{project_id}/scans", response_model=ScanListResponse)
async def list_scans(
    project_id: int,
    user: CurrentUser,
    db: DBSession,
    skip: int = 0,
    limit: int = 20,
):
    """List all scans for a project."""
    # Verify project ownership
    project_result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    # Count total
    count_result = await db.execute(
        select(func.count(Scan.id)).where(Scan.project_id == project_id)
    )
    total = count_result.scalar()
    
    # Fetch scans
    result = await db.execute(
        select(Scan)
        .where(Scan.project_id == project_id)
        .order_by(Scan.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    scans = result.scalars().all()
    
    return ScanListResponse(
        scans=[ScanResponse.model_validate(s) for s in scans],
        total=total,
    )


@router.post("/projects/{project_id}/scans", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def trigger_scan(
    project_id: int,
    scan_data: ScanCreate,
    user: CurrentUser,
    db: DBSession,
    background_tasks: BackgroundTasks,
):
    """Trigger a new scan for a project."""
    # Verify project ownership
    project_result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    # Check for existing running scan
    running_result = await db.execute(
        select(Scan).where(
            Scan.project_id == project_id,
            Scan.status.in_([ScanStatus.PENDING, ScanStatus.CLONING, ScanStatus.DETECTING, 
                             ScanStatus.SCANNING_SAST, ScanStatus.SCANNING_SCA, ScanStatus.SCORING])
        )
    )
    if running_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A scan is already in progress for this project",
        )
    
    # Create new scan
    scan = Scan(
        project_id=project_id,
        status=ScanStatus.PENDING,
        branch=scan_data.branch or project.default_branch,
        progress=0,
        total_findings=0,
        critical_count=0,
        high_count=0,
        medium_count=0,
        low_count=0,
    )
    
    db.add(scan)
    await db.commit()
    await db.refresh(scan)
    
    # Queue background task
    # In production, this would be sent to Redis/ARQ worker
    # For now, we'll use FastAPI's BackgroundTasks
    background_tasks.add_task(execute_scan, scan.id, project.id, user.id)
    
    return ScanResponse.model_validate(scan)


@router.post("/scans/{scan_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_scan(
    scan_id: int,
    user: CurrentUser,
    db: DBSession,
):
    """Cancel a running scan."""
    # Verify scan ownership
    scan_result = await db.execute(
        select(Scan)
        .join(Project)
        .where(Scan.id == scan_id, Project.user_id == user.id)
    )
    scan = scan_result.scalar_one_or_none()
    
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    
    # Check if cancellable
    terminal_statuses = [ScanStatus.COMPLETED, ScanStatus.FAILED, ScanStatus.CANCELLED]
    if scan.status in terminal_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Scan cannot be cancelled in its current state"
        )
    
    # Mark as cancelled
    scan.status = ScanStatus.CANCELLED
    scan.status_message = "Cancelled by user"
    scan.completed_at = datetime.utcnow()
    await db.commit()
    await db.refresh(scan)
    
    return {"message": "Scan cancelled"}


@router.get("/scans/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: int,
    user: CurrentUser,
    db: DBSession,
):
    """Get scan details."""
    result = await db.execute(
        select(Scan)
        .join(Project)
        .where(Scan.id == scan_id, Project.user_id == user.id)
    )
    scan = result.scalar_one_or_none()
    
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    
    return ScanResponse.model_validate(scan)


@router.get("/scans/{scan_id}/findings")
async def get_findings(
    scan_id: int,
    user: CurrentUser,
    db: DBSession,
    severity: list[str] = None,
    category: list[str] = None,
    finding_type: str = None,
    skip: int = 0,
    limit: int = 50,
):
    """Get findings for a scan with optional filters."""
    # Verify scan ownership
    scan_result = await db.execute(
        select(Scan)
        .join(Project)
        .where(Scan.id == scan_id, Project.user_id == user.id)
    )
    scan = scan_result.scalar_one_or_none()
    
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    
    # Build query with filters
    query = select(Finding).where(Finding.scan_id == scan_id)
    
    if severity:
        query = query.where(Finding.severity.in_([Severity(s) for s in severity]))
    if category:
        query = query.where(Finding.category.in_([FindingCategory(c) for c in category]))
    if finding_type:
        query = query.where(Finding.finding_type == FindingType(finding_type))
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    # Fetch findings
    result = await db.execute(
        query
        .order_by(Finding.severity, Finding.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    findings = result.scalars().all()
    
    # Aggregate by severity and category
    by_severity = {}
    by_category = {}
    
    for finding in findings:
        sev = finding.severity.value
        cat = finding.category.value
        by_severity[sev] = by_severity.get(sev, 0) + 1
        by_category[cat] = by_category.get(cat, 0) + 1
    
    return {
        "findings": [
            {
                "id": f.id,
                "scan_id": f.scan_id,
                "finding_type": f.finding_type.value,
                "severity": f.severity.value,
                "category": f.category.value,
                "title": f.title,
                "description": f.description,
                "file_path": f.file_path,
                "line_start": f.line_start,
                "line_end": f.line_end,
                "code_snippet": f.code_snippet,
                "package_name": f.package_name,
                "package_version": f.package_version,
                "fixed_version": f.fixed_version,
                "cwe_id": f.cwe_id,
                "cve_id": f.cve_id,
                "owasp_category": f.owasp_category,
                "rule_id": f.rule_id,
                "is_fixed": f.is_fixed,
                "is_ignored": f.is_ignored,
                "has_fix_suggestion": f.fix_suggestion is not None,
                "has_test_suggestion": f.test_suggestion is not None,
                "layman_explanation": f.layman_explanation,
                "created_at": f.created_at.isoformat(),
            }
            for f in findings
        ],
        "total": total,
        "by_severity": by_severity,
        "by_category": by_category,
    }


async def execute_scan(scan_id: int, project_id: int, user_id: int):
    """
    Execute a scan in the background.
    
    In production, this would be an ARQ worker task.
    """
    from app.core.database import async_session_maker
    from app.services.scanner import detect_stack, run_sast_scan, run_sca_scan
    from app.services.scoring import calculate_readiness_score
    from app.services.github import GitHubService
    import tempfile
    import tarfile
    import os
    import logging
    
    logger = logging.getLogger(__name__)
    
    async with async_session_maker() as db:
        try:
            # Get scan and project
            scan_result = await db.execute(select(Scan).where(Scan.id == scan_id))
            scan = scan_result.scalar_one()
            
            project_result = await db.execute(
                select(Project).where(Project.id == project_id)
                .options(selectinload(Project.user))
            )
            project = project_result.scalar_one()
            user = project.user
            
            logger.info(f"Starting scan {scan_id} for project {project_id} ({project.name})")
            
            # Helper function to check cancellation status
            async def is_cancelled() -> bool:
                """Check if scan has been cancelled by querying DB directly."""
                result = await db.execute(
                    select(Scan.status).where(Scan.id == scan_id)
                )
                current_status = result.scalar_one_or_none()
                return current_status == ScanStatus.CANCELLED
            
            # Update status: Cloning
            if await is_cancelled():
                logger.info(f"Scan {scan_id} cancelled")
                return

            scan.status = ScanStatus.CLONING
            scan.started_at = datetime.utcnow()
            scan.progress = 10
            await db.commit()
            


            # Clone/download repository
            temp_dir = tempfile.mkdtemp(prefix="vibesec_")
            project_path = temp_dir
            
            if project.source_type.value == "github" and user.github_access_token:
                github = GitHubService(access_token=user.github_access_token)
                try:
                    owner, repo = project.repo_full_name.split("/")
                    tarball = await github.download_repo_archive(owner, repo, scan.branch or "main")
                    
                    # Extract tarball
                    tar_path = os.path.join(temp_dir, "repo.tar.gz")
                    with open(tar_path, "wb") as f:
                        f.write(tarball)
                    
                    with tarfile.open(tar_path, "r:gz") as tar:
                        tar.extractall(temp_dir)
                    
                    # Find extracted directory
                    extracted_dirs = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
                    if extracted_dirs:
                        project_path = os.path.join(temp_dir, extracted_dirs[0])
                    
                finally:
                    await github.close()
            
            # Update status: Detecting
            if await is_cancelled():
                logger.info(f"Scan {scan_id} cancelled")
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                return

            scan.status = ScanStatus.DETECTING
            scan.progress = 20
            await db.commit()


            
            # Detect stack
            stack_result = await detect_stack(project_path)
            if stack_result.stack.value != "unknown":
                project.stack = stack_result.stack.value
                await db.commit()
            
            # Determine languages for scanning
            languages = []
            if stack_result.stack.value in ["nextjs", "express"]:
                languages = ["javascript", "typescript"]
            elif stack_result.stack.value in ["django", "fastapi"]:
                languages = ["python"]
            
            # Update status: SAST
            if await is_cancelled():
                logger.info(f"Scan {scan_id} cancelled")
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                return

            scan.status = ScanStatus.SCANNING_SAST
            scan.progress = 40
            await db.commit()


            
            # Run SAST
            sast_result = await run_sast_scan(project_path, languages)
            
            # Update status: SCA
            if await is_cancelled():
                logger.info(f"Scan {scan_id} cancelled")
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                return

            scan.status = ScanStatus.SCANNING_SCA
            scan.progress = 60
            await db.commit()


            
            # Run SCA
            sca_result = await run_sca_scan(project_path)
            
            # Update status: Scoring
            if await is_cancelled():
                logger.info(f"Scan {scan_id} cancelled")
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                return

            scan.status = ScanStatus.SCORING
            scan.progress = 80
            await db.commit()


            
            # Store findings
            # ... (rest of storage logic unchanged)
            for sast_finding in sast_result.findings:
                finding = Finding(
                    scan_id=scan.id,
                    finding_type=FindingType.SAST,
                    severity=sast_finding.severity,
                    category=sast_finding.category,
                    title=sast_finding.title,
                    description=sast_finding.description,
                    file_path=sast_finding.file_path,
                    line_start=sast_finding.line_start,
                    line_end=sast_finding.line_end,
                    code_snippet=sast_finding.code_snippet,
                    cwe_id=sast_finding.cwe_id,
                    owasp_category=sast_finding.owasp_category,
                    rule_id=sast_finding.rule_id,
                    layman_explanation=sast_finding.layman_explanation,
                )
                db.add(finding)
            
            for sca_finding in sca_result.findings:
                finding = Finding(
                    scan_id=scan.id,
                    finding_type=FindingType.SCA,
                    severity=sca_finding.severity,
                    category=FindingCategory.DEPENDENCY,
                    title=sca_finding.title,
                    description=sca_finding.description,
                    package_name=sca_finding.package_name,
                    package_version=sca_finding.package_version,
                    fixed_version=sca_finding.fixed_version,
                    cve_id=sca_finding.cve_id,
                    layman_explanation=sca_finding.layman_explanation,
                )
                db.add(finding)
            
            # Calculate scores
            readiness = await calculate_readiness_score(
                project_path,
                sast_result.findings,
                sca_result.findings,
            )
            
            # Update scan with results
            scan.status = ScanStatus.COMPLETED
            scan.progress = 100
            scan.completed_at = datetime.utcnow()
            scan.overall_score = readiness.overall
            scan.domain_scores = {
                "security": {"score": readiness.security.score, "issues": readiness.security.issues},
                "testing": {"score": readiness.testing.score, "issues": readiness.testing.issues},
                "reliability": {"score": readiness.reliability.score, "issues": readiness.reliability.issues},
                "observability": {"score": readiness.observability.score, "issues": readiness.observability.issues},
                "performance": {"score": readiness.performance.score, "issues": readiness.performance.issues},
                "infrastructure": {"score": readiness.infrastructure.score, "issues": readiness.infrastructure.issues},
            }
            
            # Count findings by severity
            scan.total_findings = len(sast_result.findings) + len(sca_result.findings)
            scan.critical_count = sum(1 for f in sast_result.findings if f.severity == Severity.CRITICAL)
            scan.critical_count += sum(1 for f in sca_result.findings if f.severity == Severity.CRITICAL)
            scan.high_count = sum(1 for f in sast_result.findings if f.severity == Severity.HIGH)
            scan.high_count += sum(1 for f in sca_result.findings if f.severity == Severity.HIGH)
            scan.medium_count = sum(1 for f in sast_result.findings if f.severity == Severity.MEDIUM)
            scan.medium_count += sum(1 for f in sca_result.findings if f.severity == Severity.MEDIUM)
            scan.low_count = sum(1 for f in sast_result.findings if f.severity == Severity.LOW)
            scan.low_count += sum(1 for f in sca_result.findings if f.severity == Severity.LOW)
            
            # Update project with latest scan info
            project.latest_score = readiness.overall
            project.latest_scan_id = scan.id
            
            await db.commit()
            
            # Cleanup temp directory
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.info("Scan completed successfully")
            
        except Exception as e:
            logger.error(f"Scan failed: {e}", exc_info=True)
            # Mark scan as failed
            scan_result = await db.execute(select(Scan).where(Scan.id == scan_id))
            scan = scan_result.scalar_one_or_none()
            if scan:
                scan.status = ScanStatus.FAILED
                scan.status_message = str(e)[:500]
                scan.completed_at = datetime.utcnow()
                await db.commit()
