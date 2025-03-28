"""Add `AuditLog` table

Revision ID: ae15edaeedda
Revises: 683ca0a32f41
Create Date: 2025-03-17 10:28:00.375666

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "ae15edaeedda"
down_revision = "683ca0a32f41"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "audit_logs",
        sa.Column("id", GUID, primary_key=True, nullable=False),
        sa.Column("entity_type", sa.String(), nullable=False, index=True),
        sa.Column("operation", sa.String(), nullable=False, index=True),
        sa.Column("entity_id", sa.String(), nullable=False, index=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            index=True,
        ),
        sa.Column("request_id", GUID, nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("duration", sa.Interval(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
    )


def downgrade():
    op.drop_table("audit_logs")
