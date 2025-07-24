"""Consolidated migration - All tables and fields

Revision ID: 001
Revises: 
Create Date: 2025-07-23 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('salt', sa.String(length=64), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('login_count', sa.Integer(), nullable=True),
        sa.Column('login_attempts', sa.Integer(), nullable=True),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('preferences', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # 2. Create downloads table
    op.create_table('downloads',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('progress', sa.Float(), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('thumbnail', sa.String(length=500), nullable=True),
        sa.Column('quality', sa.String(length=50), nullable=True),
        sa.Column('format', sa.String(length=50), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('attempts', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('download_count', sa.Integer(), nullable=True),
        sa.Column('last_accessed', sa.DateTime(), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('storage_type', sa.String(length=20), nullable=True, server_default='temporary'),
        sa.Column('uploaded_to_drive', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('drive_file_id', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_downloads_created_at'), 'downloads', ['created_at'], unique=False)
    op.create_index(op.f('ix_downloads_status'), 'downloads', ['status'], unique=False)
    op.create_index(op.f('ix_downloads_url'), 'downloads', ['url'], unique=False)
    op.create_index('idx_downloads_status_created', 'downloads', ['status', 'created_at'], unique=False)
    op.create_index('idx_downloads_url_status', 'downloads', ['url', 'status'], unique=False)
    op.create_index(op.f('ix_downloads_user_id'), 'downloads', ['user_id'], unique=False)
    op.create_index(op.f('ix_downloads_storage_type'), 'downloads', ['storage_type'], unique=False)
    op.create_foreign_key('fk_downloads_user_id', 'downloads', 'users', ['user_id'], ['id'])

    # 3. Create google_drive_configs table
    op.create_table('google_drive_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_name', sa.String(length=100), nullable=False),
        sa.Column('credentials_file', sa.String(length=500), nullable=False),
        sa.Column('folder_id', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('quota_used', sa.Integer(), nullable=True),
        sa.Column('quota_limit', sa.Integer(), nullable=True),
        sa.Column('last_used', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('account_name')
    )
    op.create_index('idx_drive_config_active', 'google_drive_configs', ['is_active'], unique=False)
    op.create_index('idx_drive_config_account', 'google_drive_configs', ['account_name'], unique=False)

    # 4. Create temporary_files table
    op.create_table('temporary_files',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('download_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('expiration_time', sa.DateTime(), nullable=False),
        sa.Column('access_count', sa.Integer(), nullable=True),
        sa.Column('temporary_url', sa.String(length=500), nullable=True),
        sa.Column('file_hash', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('max_accesses', sa.Integer(), nullable=True),
        sa.Column('custom_filename', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['download_id'], ['downloads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_temporary_files_download_id'), 'temporary_files', ['download_id'], unique=False)
    op.create_index(op.f('ix_temporary_files_expiration_time'), 'temporary_files', ['expiration_time'], unique=False)
    op.create_index(op.f('ix_temporary_files_file_hash'), 'temporary_files', ['file_hash'], unique=False)
    op.create_index(op.f('ix_temporary_files_temporary_url'), 'temporary_files', ['temporary_url'], unique=False)
    op.create_index('idx_temp_files_expiration', 'temporary_files', ['expiration_time'], unique=False)
    op.create_index('idx_temp_files_download_hash', 'temporary_files', ['download_id', 'file_hash'], unique=False)
    op.create_index('idx_temp_files_url', 'temporary_files', ['temporary_url'], unique=False)

    # 5. Create download_logs table
    op.create_table('download_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('download_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('video_url', sa.Text(), nullable=False),
        sa.Column('video_title', sa.String(length=500), nullable=False),
        sa.Column('video_duration', sa.Integer(), nullable=True),
        sa.Column('video_size', sa.BigInteger(), nullable=True),
        sa.Column('video_format', sa.String(length=50), nullable=False),
        sa.Column('video_quality', sa.String(length=50), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('download_duration', sa.Float(), nullable=True),
        sa.Column('download_speed', sa.Float(), nullable=True),
        sa.Column('file_size_downloaded', sa.BigInteger(), nullable=True),
        sa.Column('progress_percentage', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(length=100), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('request_headers', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('response_headers', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('download_path', sa.String(length=500), nullable=True),
        sa.Column('output_format', sa.String(length=50), nullable=True),
        sa.Column('quality_preference', sa.String(length=50), nullable=True),
        sa.Column('google_drive_uploaded', sa.Boolean(), nullable=True),
        sa.Column('google_drive_file_id', sa.String(length=255), nullable=True),
        sa.Column('google_drive_folder_id', sa.String(length=255), nullable=True),
        sa.Column('temporary_url_created', sa.Boolean(), nullable=True),
        sa.Column('temporary_url_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('temporary_url_access_count', sa.Integer(), nullable=True),
        sa.Column('memory_usage', sa.Float(), nullable=True),
        sa.Column('cpu_usage', sa.Float(), nullable=True),
        sa.Column('disk_usage', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['download_id'], ['downloads.id'], ),
        sa.ForeignKeyConstraint(['temporary_url_id'], ['temporary_files.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_download_logs_created_at'), 'download_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_download_logs_status'), 'download_logs', ['status'], unique=False)
    op.create_index(op.f('ix_download_logs_user_id'), 'download_logs', ['user_id'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_download_logs_user_id'), table_name='download_logs')
    op.drop_index(op.f('ix_download_logs_status'), table_name='download_logs')
    op.drop_index(op.f('ix_download_logs_created_at'), table_name='download_logs')
    op.drop_table('download_logs')
    
    op.drop_index('idx_temp_files_url', table_name='temporary_files')
    op.drop_index('idx_temp_files_download_hash', table_name='temporary_files')
    op.drop_index('idx_temp_files_expiration', table_name='temporary_files')
    op.drop_index(op.f('ix_temporary_files_temporary_url'), table_name='temporary_files')
    op.drop_index(op.f('ix_temporary_files_file_hash'), table_name='temporary_files')
    op.drop_index(op.f('ix_temporary_files_expiration_time'), table_name='temporary_files')
    op.drop_index(op.f('ix_temporary_files_download_id'), table_name='temporary_files')
    op.drop_table('temporary_files')
    
    op.drop_index('idx_drive_config_account', table_name='google_drive_configs')
    op.drop_index('idx_drive_config_active', table_name='google_drive_configs')
    op.drop_table('google_drive_configs')
    
    op.drop_index(op.f('ix_downloads_storage_type'), table_name='downloads')
    op.drop_index(op.f('ix_downloads_user_id'), table_name='downloads')
    op.drop_index('idx_downloads_url_status', table_name='downloads')
    op.drop_index('idx_downloads_status_created', table_name='downloads')
    op.drop_index(op.f('ix_downloads_url'), table_name='downloads')
    op.drop_index(op.f('ix_downloads_status'), table_name='downloads')
    op.drop_index(op.f('ix_downloads_created_at'), table_name='downloads')
    op.drop_table('downloads')
    
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users') 