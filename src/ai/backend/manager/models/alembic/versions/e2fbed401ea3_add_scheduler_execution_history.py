"""Add scheduler execution history table

Revision ID: e2fbed401ea3
Revises: ffcf0ed13a25
Create Date: 2025-11-16 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from ai.backend.manager.models.base import GUID, SessionIDColumnType

# revision identifiers, used by Alembic.
revision = "e2fbed401ea3"
down_revision = "ffcf0ed13a25"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scheduler_execution_history",
        sa.Column(
            "id",
            GUID(),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "session_id",
            SessionIDColumnType(),
            nullable=False,
        ),
        sa.Column(
            "step",
            sa.VARCHAR(length=64),
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "finished_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "retry_count",
            sa.Integer(),
            nullable=False,
            default=0,
        ),
        sa.Column(
            "last_retry_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.VARCHAR(length=64),
            nullable=False,
        ),
        sa.Column(
            "error_info",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "details",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["sessions.id"],
            name=op.f("fk_scheduler_execution_history_session_id_sessions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scheduler_execution_history")),
    )

    # Create indexes
    op.create_index(
        op.f("ix_scheduler_execution_history_session_id"),
        "scheduler_execution_history",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_scheduler_execution_history_step"),
        "scheduler_execution_history",
        ["step"],
        unique=False,
    )
    op.create_index(
        "ix_scheduler_execution_history_session_step",
        "scheduler_execution_history",
        ["session_id", "step", "started_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_scheduler_execution_history_session_step",
        table_name="scheduler_execution_history",
    )
    op.drop_index(
        op.f("ix_scheduler_execution_history_step"),
        table_name="scheduler_execution_history",
    )
    op.drop_index(
        op.f("ix_scheduler_execution_history_session_id"),
        table_name="scheduler_execution_history",
    )
    op.drop_table("scheduler_execution_history")
