"""Initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2025-11-14 00:00:00.000000

This migration creates the initial database schema for the phishing
simulation prototype. It defines tables for templates, segments,
targets, campaigns, and events, and sets up indexes to optimize
event queries by campaign, target and event type.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create tables and indexes."""
    # templates table
    op.create_table(
        "templates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("channel", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("html_body", sa.Text(), nullable=False),
        sa.Column("signals", sa.JSON(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )

    # segments table
    op.create_table(
        "segments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("age_bracket", sa.String(length=50), nullable=True),
        sa.Column("gender", sa.String(length=50), nullable=True),
        sa.Column("education", sa.String(length=50), nullable=True),
    )

    # targets table
    op.create_table(
        "targets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("segment_id", sa.Integer(), nullable=False),
        sa.Column("recipient", sa.String(length=255), nullable=False),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["segment_id"], ["segments.id"], ondelete="CASCADE"),
    )

    # campaigns table
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("channel", sa.String(length=50), nullable=False),
        sa.Column("launched_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True, server_default="draft"),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("segment_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["template_id"], ["templates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["segment_id"], ["segments.id"], ondelete="CASCADE"),
    )

    # events table
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_id"], ["targets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_id"], ["templates.id"], ondelete="CASCADE"),
    )

    # indexes
    op.create_index("idx_events_campaign", "events", ["campaign_id"])
    op.create_index("idx_events_target", "events", ["target_id"])
    op.create_index("idx_events_type", "events", ["event_type"])


def downgrade() -> None:
    """Drop tables and indexes in reverse order of creation."""
    op.drop_index("idx_events_type", table_name="events")
    op.drop_index("idx_events_target", table_name="events")
    op.drop_index("idx_events_campaign", table_name="events")
    op.drop_table("events")
    op.drop_table("campaigns")
    op.drop_table("targets")
    op.drop_table("segments")
    op.drop_table("templates")