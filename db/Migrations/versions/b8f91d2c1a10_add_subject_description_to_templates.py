"""add subject and description to templates

Revision ID: b8f91d2c1a10
Revises: aa81f401f7e0
Create Date: 2026-03-08
"""
from alembic import op
import sqlalchemy as sa


revision = "b8f91d2c1a10"
down_revision = "aa81f401f7e0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("templates", sa.Column("subject", sa.String(length=255), nullable=True))
    op.add_column("templates", sa.Column("description", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("templates", "description")
    op.drop_column("templates", "subject")