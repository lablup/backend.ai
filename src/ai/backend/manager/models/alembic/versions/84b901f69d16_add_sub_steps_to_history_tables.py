"""Add sub_steps to history tables

Revision ID: 84b901f69d16
Revises: 2185ae0dd371
Create Date: 2026-01-11

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "84b901f69d16"
down_revision = "2185ae0dd371"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add sub_steps to deployment_history and route_history
    op.add_column(
        "deployment_history",
        sa.Column(
            "sub_steps",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "route_history",
        sa.Column(
            "sub_steps",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )

    # Migrate existing session_scheduling_history: NULL -> []
    op.execute(
        "UPDATE session_scheduling_history SET sub_steps = '[]'::jsonb WHERE sub_steps IS NULL"
    )
    op.alter_column(
        "session_scheduling_history",
        "sub_steps",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
        server_default=sa.text("'[]'::jsonb"),
    )


def downgrade() -> None:
    # Revert session_scheduling_history back to nullable
    op.alter_column(
        "session_scheduling_history",
        "sub_steps",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=True,
        server_default=None,
    )

    # Remove sub_steps from deployment_history and route_history
    op.drop_column("deployment_history", "sub_steps")
    op.drop_column("route_history", "sub_steps")
