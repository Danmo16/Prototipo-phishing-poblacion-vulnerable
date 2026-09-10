"""add uid to targets

Revision ID: aa81f401f7e0
Revises: 0001_initial_schema
Create Date: 2026-03-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "aa81f401f7e0"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "targets",
        sa.Column("uid", sa.String(length=64), nullable=True)
    )
    op.create_index("ix_targets_uid", "targets", ["uid"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_targets_uid", table_name="targets")
    op.drop_column("targets", "uid")
