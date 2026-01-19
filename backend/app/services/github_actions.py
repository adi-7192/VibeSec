"""
VibeSec Backend - GitHub Actions Workflow Generator

Generates GitHub Actions workflow files for CI/CD integration.
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class WorkflowConfig:
    """Configuration for workflow generation."""
    project_name: str
    api_url: str
    api_token: str
    scan_on_push: bool = True
    scan_on_pr: bool = True
    branches: list[str] = None
    fail_on_critical: bool = True
    fail_on_high: bool = False
    min_score: Optional[int] = None
    
    def __post_init__(self):
        if self.branches is None:
            self.branches = ["main", "master"]


def generate_vibesec_workflow(config: WorkflowConfig) -> str:
    """
    Generate a VibeSec GitHub Actions workflow.
    
    This workflow:
    1. Triggers on push/PR to specified branches
    2. Calls VibeSec API to trigger a scan
    3. Polls for scan completion
    4. Posts results as PR comment
    5. Fails if criteria not met
    """
    
    branches_str = ", ".join(config.branches)
    
    workflow = f'''name: VibeSec Security Scan

on:
  push:
    branches: [{branches_str}]
  pull_request:
    branches: [{branches_str}]

jobs:
  vibesec-scan:
    runs-on: ubuntu-latest
    name: Security & Readiness Scan
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Trigger VibeSec Scan
        id: trigger
        run: |
          RESPONSE=$(curl -s -X POST \\
            -H "Authorization: Bearer ${{{{ secrets.VIBESEC_API_TOKEN }}}}" \\
            -H "Content-Type: application/json" \\
            "{config.api_url}/api/v1/projects/${{{{ secrets.VIBESEC_PROJECT_ID }}}}/scans" \\
            -d '{{"branch": "${{{{ github.head_ref || github.ref_name }}}}"}}')
          
          SCAN_ID=$(echo $RESPONSE | jq -r '.id')
          echo "scan_id=$SCAN_ID" >> $GITHUB_OUTPUT
          echo "Started scan: $SCAN_ID"

      - name: Wait for Scan Completion
        id: wait
        run: |
          SCAN_ID="${{{{ steps.trigger.outputs.scan_id }}}}"
          MAX_ATTEMPTS=60
          ATTEMPT=0
          
          while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
            RESPONSE=$(curl -s \\
              -H "Authorization: Bearer ${{{{ secrets.VIBESEC_API_TOKEN }}}}" \\
              "{config.api_url}/api/v1/scans/$SCAN_ID")
            
            STATUS=$(echo $RESPONSE | jq -r '.status')
            PROGRESS=$(echo $RESPONSE | jq -r '.progress')
            
            echo "Scan status: $STATUS ($PROGRESS%)"
            
            if [ "$STATUS" = "completed" ]; then
              SCORE=$(echo $RESPONSE | jq -r '.overall_score')
              CRITICAL=$(echo $RESPONSE | jq -r '.critical_count')
              HIGH=$(echo $RESPONSE | jq -r '.high_count')
              
              echo "score=$SCORE" >> $GITHUB_OUTPUT
              echo "critical=$CRITICAL" >> $GITHUB_OUTPUT
              echo "high=$HIGH" >> $GITHUB_OUTPUT
              echo "response=$RESPONSE" >> $GITHUB_OUTPUT
              
              exit 0
            elif [ "$STATUS" = "failed" ]; then
              echo "Scan failed!"
              exit 1
            fi
            
            sleep 10
            ATTEMPT=$((ATTEMPT + 1))
          done
          
          echo "Scan timed out"
          exit 1

      - name: Post Results to PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const score = '${{{{ steps.wait.outputs.score }}}}';
            const critical = '${{{{ steps.wait.outputs.critical }}}}';
            const high = '${{{{ steps.wait.outputs.high }}}}';
            const scanId = '${{{{ steps.trigger.outputs.scan_id }}}}';
            
            const emoji = score >= 85 ? '✅' : score >= 60 ? '⚠️' : '❌';
            const status = score >= 85 ? 'Ready' : score >= 60 ? 'Needs Work' : 'Not Ready';
            
            const body = `## ${{emoji}} VibeSec Security Report
            
            | Metric | Value |
            |--------|-------|
            | **Readiness Score** | ${{score}}/100 (${{status}}) |
            | **Critical Issues** | ${{critical}} |
            | **High Issues** | ${{high}} |
            
            [View Full Report]({config.api_url}/projects/${{{{secrets.VIBESEC_PROJECT_ID}}}}/scans/${{scanId}})
            `;
            
            github.rest.issues.createComment({{
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: body
            }});

      - name: Check Thresholds
        run: |
          SCORE="${{{{ steps.wait.outputs.score }}}}"
          CRITICAL="${{{{ steps.wait.outputs.critical }}}}"
          HIGH="${{{{ steps.wait.outputs.high }}}}"
          
          echo "📊 Readiness Score: $SCORE/100"
          echo "🔴 Critical Issues: $CRITICAL"
          echo "🟠 High Issues: $HIGH"
'''

    # Add threshold checks
    if config.fail_on_critical:
        workflow += '''
          if [ "$CRITICAL" -gt 0 ]; then
            echo "❌ Build failed: Critical security issues found"
            exit 1
          fi
'''
    
    if config.fail_on_high:
        workflow += '''
          if [ "$HIGH" -gt 0 ]; then
            echo "❌ Build failed: High security issues found"
            exit 1
          fi
'''
    
    if config.min_score:
        workflow += f'''
          if [ "$SCORE" -lt {config.min_score} ]; then
            echo "❌ Build failed: Readiness score $SCORE is below minimum {config.min_score}"
            exit 1
          fi
'''
    
    workflow += '''
          echo "✅ All checks passed!"
'''
    
    return workflow


def generate_pr_check_workflow(api_url: str) -> str:
    """Generate a minimal PR check workflow."""
    return f'''name: VibeSec PR Check

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  security-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run VibeSec Scan
        uses: vibesec/scan-action@v1
        with:
          api-token: ${{{{ secrets.VIBESEC_API_TOKEN }}}}
          project-id: ${{{{ secrets.VIBESEC_PROJECT_ID }}}}
          fail-on-critical: true
'''


def generate_setup_instructions(project_name: str) -> str:
    """Generate setup instructions for the workflow."""
    return f'''# VibeSec GitHub Actions Setup

## 1. Add Repository Secrets

Go to your repository: **Settings → Secrets and variables → Actions**

Add these secrets:
- `VIBESEC_API_TOKEN`: Your VibeSec API token
- `VIBESEC_PROJECT_ID`: Your project ID from VibeSec dashboard

## 2. Add Workflow File

Create `.github/workflows/vibesec.yml` with the generated content.

## 3. Commit and Push

```bash
git add .github/workflows/vibesec.yml
git commit -m "Add VibeSec security scanning"
git push
```

## 4. Verify

- Push a commit or open a PR
- Check the Actions tab for scan results
- PR comments will show the security report

## Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `fail-on-critical` | Fail if critical issues | `true` |
| `fail-on-high` | Fail if high issues | `false` |
| `min-score` | Minimum passing score | None |
'''
