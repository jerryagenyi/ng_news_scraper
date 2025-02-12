"""add url validation columns

Revision ID: add_url_validation_columns
Create Date: 2025-02-12 00:35:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'add_url_validation_columns'
down_revision = None  # Update this with your last migration's revision ID
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns to sitemaps table
    op.add_column('sitemaps', sa.Column('is_valid', sa.Boolean(), nullable=True))
    op.add_column('sitemaps', sa.Column('last_checked', sa.DateTime(timezone=True), nullable=True))
    op.add_column('sitemaps', sa.Column('status_code', sa.Integer(), nullable=True))

def downgrade():
    # Remove columns if needed
    op.drop_column('sitemaps', 'status_code')
    op.drop_column('sitemaps', 'last_checked')
    op.drop_column('sitemaps', 'is_valid')