"""The events and states tables.

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Make the events and states tables."""
    op.create_table(
        "events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("kind", sa.String, nullable=False),
        sa.Column("urgency", sa.String, nullable=False),
        sa.Column("announce", sa.Boolean, nullable=False),
        sa.Column("state", sa.String, nullable=False),
        sa.Column("subject_action", sa.String, nullable=True),
        sa.Column("details", JSONB, nullable=False),
        sa.Column("model_output", JSONB, nullable=False),
    )
    op.create_table(
        "states",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("data", sa.Text, nullable=False),
        sa.Column("since", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    """Drop both tables."""
    op.drop_table("states")
    op.drop_table("events")
