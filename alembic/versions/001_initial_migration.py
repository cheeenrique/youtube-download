"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import ProgrammingError

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    # downloads
    try:
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
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_downloads_created_at'), 'downloads', ['created_at'], unique=False)
        op.create_index(op.f('ix_downloads_status'), 'downloads', ['status'], unique=False)
        op.create_index(op.f('ix_downloads_url'), 'downloads', ['url'], unique=False)
        op.create_index('idx_downloads_status_created', 'downloads', ['status', 'created_at'], unique=False)
        op.create_index('idx_downloads_url_status', 'downloads', ['url', 'status'], unique=False)
    except Exception as e:
        if 'already exists' in str(e):
            pass
        else:
            raise
    # google_drive_configs
    try:
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
    except Exception as e:
        if 'already exists' in str(e):
            pass
        else:
            raise
    # temporary_files
    try:
        op.create_table('temporary_files',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('download_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('file_path', sa.String(length=500), nullable=False),
            sa.Column('expiration_time', sa.DateTime(), nullable=False),
            sa.Column('access_count', sa.Integer(), nullable=True),
            sa.Column('temporary_url', sa.String(length=500), nullable=True),
            sa.Column('file_hash', sa.String(length=64), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['download_id'], ['downloads.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_temporary_files_download_id'), 'temporary_files', ['download_id'], unique=False)
        op.create_index(op.f('ix_temporary_files_expiration_time'), 'temporary_files', ['expiration_time'], unique=False)
        op.create_index(op.f('ix_temporary_files_file_hash'), 'temporary_files', ['file_hash'], unique=False)
        op.create_index(op.f('ix_temporary_files_temporary_url'), 'temporary_files', ['temporary_url'], unique=False)
        op.create_index('idx_temp_files_expiration', 'temporary_files', ['expiration_time'], unique=False)
        op.create_index('idx_temp_files_download_hash', 'temporary_files', ['download_id', 'file_hash'], unique=False)
    except Exception as e:
        if 'already exists' in str(e):
            pass
        else:
            raise
    # download_logs
    try:
        op.create_table('download_logs',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('download_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('level', sa.String(length=20), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('details', sa.Text(), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['download_id'], ['downloads.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_download_logs_download_id'), 'download_logs', ['download_id'], unique=False)
        op.create_index(op.f('ix_download_logs_level'), 'download_logs', ['level'], unique=False)
        op.create_index(op.f('ix_download_logs_timestamp'), 'download_logs', ['timestamp'], unique=False)
        op.create_index('idx_logs_download_timestamp', 'download_logs', ['download_id', 'timestamp'], unique=False)
        op.create_index('idx_logs_level_timestamp', 'download_logs', ['level', 'timestamp'], unique=False)
    except Exception as e:
        if 'already exists' in str(e):
            pass
        else:
            raise


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('idx_logs_level_timestamp', table_name='download_logs')
    op.drop_index('idx_logs_download_timestamp', table_name='download_logs')
    op.drop_index(op.f('ix_download_logs_timestamp'), table_name='download_logs')
    op.drop_index(op.f('ix_download_logs_level'), table_name='download_logs')
    op.drop_index(op.f('ix_download_logs_download_id'), table_name='download_logs')
    op.drop_table('download_logs')
    # ### end Alembic commands ###

    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('idx_temp_files_download_hash', table_name='temporary_files')
    op.drop_index('idx_temp_files_expiration', table_name='temporary_files')
    op.drop_index(op.f('ix_temporary_files_temporary_url'), table_name='temporary_files')
    op.drop_index(op.f('ix_temporary_files_file_hash'), table_name='temporary_files')
    op.drop_index(op.f('ix_temporary_files_expiration_time'), table_name='temporary_files')
    op.drop_index(op.f('ix_temporary_files_download_id'), table_name='temporary_files')
    op.drop_table('temporary_files')
    # ### end Alembic commands ###

    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('idx_drive_config_account', table_name='google_drive_configs')
    op.drop_index('idx_drive_config_active', table_name='google_drive_configs')
    op.drop_table('google_drive_configs')
    # ### end Alembic commands ###

    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('idx_downloads_url_status', table_name='downloads')
    op.drop_index('idx_downloads_status_created', table_name='downloads')
    op.drop_index(op.f('ix_downloads_url'), table_name='downloads')
    op.drop_index(op.f('ix_downloads_status'), table_name='downloads')
    op.drop_index(op.f('ix_downloads_created_at'), table_name='downloads')
    op.drop_table('downloads')
    # ### end Alembic commands ### 