"""add replica group history

Revision ID: c4e9f2a7b1d8
Revises: 63be6b4add67
Create Date: 2026-06-02 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from ai.backend.manager.models.base import GUID

# Part of: 26.6.0

# revision identifiers, used by Alembic.
revision = "c4e9f2a7b1d8"
down_revision = "63be6b4add67"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "replica_group_history",
        sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("replica_group_id", GUID, nullable=False),
        sa.Column("deployment_id", GUID, nullable=False),
        sa.Column(
            "category",
            sa.String(length=64),
            nullable=False,
            server_default="lifecycle",
        ),
        sa.Column("phase", sa.String(length=64), nullable=False),
        sa.Column("from_status", sa.String(length=64), nullable=True),
        sa.Column("to_status", sa.String(length=64), nullable=True),
        sa.Column("result", sa.String(length=32), nullable=False),
        sa.Column("error_code", sa.String(length=128), nullable=True),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column(
            "sub_steps",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_replica_group_history_replica_group_id",
        "replica_group_history",
        ["replica_group_id"],
    )
    op.create_index(
        "ix_replica_group_history_deployment_id",
        "replica_group_history",
        ["deployment_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_replica_group_history_deployment_id", "replica_group_history")
    op.drop_index("ix_replica_group_history_replica_group_id", "replica_group_history")
    op.drop_table("replica_group_history")
