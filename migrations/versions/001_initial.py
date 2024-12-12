"""initial

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-10 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create conversation_logs table
    op.create_table(
        'conversation_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('initial_query', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create message_logs table
    op.create_table(
        'message_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('message_type', sa.String(), nullable=False),  # Changed to String
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('destination', sa.String(), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('correlation_id', sa.String(), nullable=False),
        sa.Column('context', postgresql.JSON(), nullable=True),
        sa.Column('processing_details', postgresql.JSON(), nullable=True),
        sa.Column('parent_message_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversation_logs.id'], ),
        sa.ForeignKeyConstraint(['parent_message_id'], ['message_logs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create processing_metrics table
    op.create_table(
        'processing_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('service', sa.String(), nullable=False),
        sa.Column('operation_type', sa.String(), nullable=False),
        sa.Column('tokens_used', sa.Integer(), nullable=False),
        sa.Column('processing_time', sa.Float(), nullable=False),
        sa.Column('model_parameters', postgresql.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['message_logs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Add indexes
    op.create_index('ix_conversation_logs_started_at', 'conversation_logs', ['started_at'])
    op.create_index('ix_message_logs_timestamp', 'message_logs', ['timestamp'])
    op.create_index('ix_message_logs_correlation_id', 'message_logs', ['correlation_id'])
    op.create_index('ix_processing_metrics_timestamp', 'processing_metrics', ['timestamp'])

def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_processing_metrics_timestamp')
    op.drop_index('ix_message_logs_correlation_id')
    op.drop_index('ix_message_logs_timestamp')
    op.drop_index('ix_conversation_logs_started_at')
    
    # Drop tables
    op.drop_table('processing_metrics')
    op.drop_table('message_logs')
    op.drop_table('conversation_logs')