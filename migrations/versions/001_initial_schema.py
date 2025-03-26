"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-03-13 21:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create conversation_logs table
    op.create_table('conversation_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('initial_query', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('initial_prompt', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversation_logs_id'), 'conversation_logs', ['id'], unique=False)

    # Create message_logs table
    op.create_table('message_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('message_type', sa.String(), nullable=True),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('destination', sa.String(), nullable=True),
        sa.Column('content', sa.String(), nullable=True),
        sa.Column('correlation_id', sa.String(), nullable=True),
        sa.Column('context', sa.JSON(), nullable=True),
        sa.Column('processing_details', sa.JSON(), nullable=True),
        sa.Column('parent_message_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversation_logs.id'], ),
        sa.ForeignKeyConstraint(['parent_message_id'], ['message_logs.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('conversation_id', 'message_type', 'source', 'destination', 'correlation_id', 
                           name='uq_message_identifier')
    )
    op.create_index(op.f('ix_message_logs_id'), 'message_logs', ['id'], unique=False)

    # Create processing_metrics table
    op.create_table('processing_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('service', sa.String(), nullable=True),
        sa.Column('operation_type', sa.String(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('processing_time', sa.Float(), nullable=True),
        sa.Column('model_parameters', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['message_logs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_processing_metrics_id'), 'processing_metrics', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_processing_metrics_id'), table_name='processing_metrics')
    op.drop_table('processing_metrics')
    op.drop_index(op.f('ix_message_logs_id'), table_name='message_logs')
    op.drop_table('message_logs')
    op.drop_index(op.f('ix_conversation_logs_id'), table_name='conversation_logs')
    op.drop_table('conversation_logs')