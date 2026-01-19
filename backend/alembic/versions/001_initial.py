"""Initial migration - create all tables

Revision ID: 001
Revises: 
Create Date: 2026-01-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('firebase_uid', sa.String(128), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('picture', sa.String(512), nullable=True),
        sa.Column('llm_provider', sa.Enum('gemini', 'openai', name='llmprovider'), nullable=True),
        sa.Column('encrypted_llm_api_key', sa.Text(), nullable=True),
        sa.Column('github_access_token', sa.Text(), nullable=True),
        sa.Column('github_username', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_firebase_uid', 'users', ['firebase_uid'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source_type', sa.Enum('github', 'zip', 'demo', name='sourcetype'), nullable=False),
        sa.Column('repo_url', sa.String(512), nullable=True),
        sa.Column('repo_full_name', sa.String(255), nullable=True),
        sa.Column('default_branch', sa.String(100), nullable=False),
        sa.Column('storage_path', sa.String(512), nullable=True),
        sa.Column('stack', sa.Enum('nextjs', 'express', 'django', 'fastapi', 'unknown', name='stacktype'), nullable=False),
        sa.Column('latest_score', sa.Float(), nullable=True),
        sa.Column('latest_scan_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_projects_id', 'projects', ['id'])
    op.create_index('ix_projects_user_id', 'projects', ['user_id'])

    # Create scans table
    op.create_table(
        'scans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'cloning', 'detecting', 'scanning_sast', 'scanning_sca', 'scoring', 'completed', 'failed', name='scanstatus'), nullable=False),
        sa.Column('status_message', sa.String(512), nullable=True),
        sa.Column('progress', sa.Integer(), nullable=False),
        sa.Column('commit_sha', sa.String(40), nullable=True),
        sa.Column('commit_message', sa.String(512), nullable=True),
        sa.Column('branch', sa.String(100), nullable=True),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('domain_scores', sa.JSON(), nullable=True),
        sa.Column('total_findings', sa.Integer(), nullable=False),
        sa.Column('critical_count', sa.Integer(), nullable=False),
        sa.Column('high_count', sa.Integer(), nullable=False),
        sa.Column('medium_count', sa.Integer(), nullable=False),
        sa.Column('low_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scans_id', 'scans', ['id'])
    op.create_index('ix_scans_project_id', 'scans', ['project_id'])

    # Create findings table
    op.create_table(
        'findings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scan_id', sa.Integer(), nullable=False),
        sa.Column('finding_type', sa.Enum('sast', 'sca', name='findingtype'), nullable=False),
        sa.Column('severity', sa.Enum('critical', 'high', 'medium', 'low', 'info', name='severity'), nullable=False),
        sa.Column('category', sa.Enum('injection', 'xss', 'secrets', 'auth', 'validation', 'crypto', 'dependency', 'config', 'other', name='findingcategory'), nullable=False),
        sa.Column('file_path', sa.String(512), nullable=True),
        sa.Column('line_start', sa.Integer(), nullable=True),
        sa.Column('line_end', sa.Integer(), nullable=True),
        sa.Column('code_snippet', sa.Text(), nullable=True),
        sa.Column('package_name', sa.String(255), nullable=True),
        sa.Column('package_version', sa.String(100), nullable=True),
        sa.Column('fixed_version', sa.String(100), nullable=True),
        sa.Column('title', sa.String(512), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('cwe_id', sa.String(20), nullable=True),
        sa.Column('cve_id', sa.String(20), nullable=True),
        sa.Column('owasp_category', sa.String(50), nullable=True),
        sa.Column('rule_id', sa.String(100), nullable=True),
        sa.Column('fix_suggestion', sa.Text(), nullable=True),
        sa.Column('fix_explanation', sa.Text(), nullable=True),
        sa.Column('test_suggestion', sa.Text(), nullable=True),
        sa.Column('is_fixed', sa.Boolean(), nullable=False),
        sa.Column('is_ignored', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['scan_id'], ['scans.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_findings_id', 'findings', ['id'])
    op.create_index('ix_findings_scan_id', 'findings', ['scan_id'])
    op.create_index('ix_findings_severity', 'findings', ['severity'])


def downgrade() -> None:
    op.drop_table('findings')
    op.drop_table('scans')
    op.drop_table('projects')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS findingcategory')
    op.execute('DROP TYPE IF EXISTS severity')
    op.execute('DROP TYPE IF EXISTS findingtype')
    op.execute('DROP TYPE IF EXISTS scanstatus')
    op.execute('DROP TYPE IF EXISTS stacktype')
    op.execute('DROP TYPE IF EXISTS sourcetype')
    op.execute('DROP TYPE IF EXISTS llmprovider')
