"""Ensure AuditLogs table exists

Revision ID: c4ea15b77136
Revises: 683ca0a32f41
Create Date: 2025-04-04 01:11:07.003523

"""

import logging

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "c4ea15b77136"
down_revision = "683ca0a32f41"
branch_labels = None
depends_on = None


logger = logging.getLogger("alembic.runtime.migration")


# This migration script was intentionally created as a duplicate of 683ca0a32f41 to address an #4084.
# See https://github.com/lablup/backend.ai/pull/4079.
def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "audit_logs" in inspector.get_table_names():
        return

    op.create_table(
        "audit_logs",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("entity_type", sa.String, nullable=False),
        sa.Column("operation", sa.String, nullable=False),
        sa.Column("entity_id", sa.String, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "request_id",
            GUID,
            nullable=False,
        ),
        sa.Column("description", sa.String, nullable=False),
        sa.Column("duration", sa.Interval, nullable=False),
        sa.Column("status", sa.VARCHAR(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
    )
    op.create_index(op.f("ix_audit_logs_created_at"), "audit_logs", ["created_at"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_type"), "audit_logs", ["entity_type"], unique=False)
    op.create_index(op.f("ix_audit_logs_operation"), "audit_logs", ["operation"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_id"), "audit_logs", ["entity_id"], unique=False)


def downgrade() -> None:
    # Downgrade should be performed in 683ca0a32f41
    pass
