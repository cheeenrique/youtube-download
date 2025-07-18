"""Add user_id to downloads table

Revision ID: 004
Revises: 80a50e7ad5f9
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '80a50e7ad5f9'
branch_labels = None
depends_on = None


def upgrade():
    try:
        op.add_column('downloads', sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True))
    except Exception as e:
        if 'already exists' in str(e) or 'duplicate column' in str(e):
            pass
        else:
            raise
    try:
        op.create_index(op.f('ix_downloads_user_id'), 'downloads', ['user_id'], unique=False)
    except Exception as e:
        if 'already exists' in str(e) or 'duplicate' in str(e):
            pass
        else:
            raise
    try:
        op.create_foreign_key('fk_downloads_user_id', 'downloads', 'users', ['user_id'], ['id'])
    except Exception as e:
        if 'already exists' in str(e) or 'duplicate' in str(e):
            pass
        else:
            raise
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('fk_downloads_user_id', 'downloads', type_='foreignkey')
    op.drop_index(op.f('ix_downloads_user_id'), table_name='downloads')
    op.drop_column('downloads', 'user_id')
    # ### end Alembic commands ### 