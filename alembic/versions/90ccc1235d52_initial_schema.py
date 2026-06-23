"""initial schema

Revision ID: 90ccc1235d52
Revises: 
Create Date: 2026-06-22 14:38:43.646143

"""
from typing import Sequence, Union

from alembic import op
import pgvector.sqlalchemy
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '90ccc1235d52'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table('jobs',
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('company', sa.String(length=255), nullable=False),
    sa.Column('url', sa.String(length=1000), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('fit_score', sa.Float(), nullable=True),
    sa.Column('recommendation', sa.String(length=10), nullable=True),
    sa.Column('fit_reasoning', sa.Text(), nullable=True),
    sa.Column('scraped_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('url')
    )
    op.create_table('users',
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_table('applications',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('job_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'job_id', name='uq_user_job')
    )
    op.create_table('job_chunks',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('job_id', sa.UUID(), nullable=False),
    sa.Column('chunk_text', sa.Text(), nullable=False),
    sa.Column('embedding', pgvector.sqlalchemy.vector.VECTOR(dim=384), nullable=True),
    sa.Column('chunk_index', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('memory_entries',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('entry_type', sa.String(length=50), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('embedding', pgvector.sqlalchemy.vector.VECTOR(dim=384), nullable=True),
    sa.Column('source_outcome', sa.String(length=20), nullable=True),
    sa.Column('stored_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_memory_entries_entry_type'), 'memory_entries', ['entry_type'], unique=False)
    op.create_index(op.f('ix_memory_entries_user_id'), 'memory_entries', ['user_id'], unique=False)
    op.create_table('resumes',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('file_path', sa.String(length=500), nullable=True),
    sa.Column('raw_text', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )
    op.create_table('search_preferences',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('target_role', sa.String(length=255), nullable=True),
    sa.Column('location', sa.String(length=255), nullable=True),
    sa.Column('seniority_level', sa.String(length=50), nullable=True),
    sa.Column('excluded_companies', sa.Text(), nullable=True),
    sa.Column('keywords', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('application_outcomes',
    sa.Column('application_id', sa.UUID(), nullable=False),
    sa.Column('outcome', sa.String(length=20), nullable=False),
    sa.Column('outcome_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('application_id')
    )
    op.create_table('cover_letters',
    sa.Column('application_id', sa.UUID(), nullable=False),
    sa.Column('draft_text', sa.Text(), nullable=True),
    sa.Column('final_text', sa.Text(), nullable=True),
    sa.Column('resume_bullets', sa.Text(), nullable=True),
    sa.Column('revision_count', sa.Integer(), nullable=False),
    sa.Column('critic_approved', sa.Boolean(), nullable=False),
    sa.Column('generated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('application_id')
    )
    op.create_table('critic_reviews',
    sa.Column('application_id', sa.UUID(), nullable=False),
    sa.Column('verdict', sa.String(length=10), nullable=False),
    sa.Column('feedback_text', sa.Text(), nullable=True),
    sa.Column('attempt_number', sa.Integer(), nullable=False),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('feedback',
    sa.Column('application_id', sa.UUID(), nullable=False),
    sa.Column('rating', sa.String(length=10), nullable=False),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('resume_chunks',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('resume_id', sa.UUID(), nullable=False),
    sa.Column('chunk_text', sa.Text(), nullable=False),
    sa.Column('embedding', pgvector.sqlalchemy.vector.VECTOR(dim=384), nullable=True),
    sa.Column('chunk_index', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('resume_chunks')
    op.drop_table('feedback')
    op.drop_table('critic_reviews')
    op.drop_table('cover_letters')
    op.drop_table('application_outcomes')
    op.drop_table('search_preferences')
    op.drop_table('resumes')
    op.drop_index(op.f('ix_memory_entries_user_id'), table_name='memory_entries')
    op.drop_index(op.f('ix_memory_entries_entry_type'), table_name='memory_entries')
    op.drop_table('memory_entries')
    op.drop_table('job_chunks')
    op.drop_table('applications')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_table('jobs')
    # ### end Alembic commands ###
