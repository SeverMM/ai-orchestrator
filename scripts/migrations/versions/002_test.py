"""test migration

Revision ID: 002_test
Revises: 001_initial
Create Date: 2024-01-10 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_test'
down_revision = '001_initial'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create a simple test table
    op.create_table(
        'test_table',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('value', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('test_table')