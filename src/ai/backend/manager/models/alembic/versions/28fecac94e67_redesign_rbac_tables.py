"""redesign rbac tables

Revision ID: 28fecac94e67
Revises: 643deb439458
Create Date: 2025-08-06 10:22:55.140194

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "28fecac94e67"
down_revision = "643deb439458"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("object_permissions")


def downgrade() -> None:
    op.create_table(
        "object_permissions",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="active"),
        sa.Column("role_id", GUID(), nullable=False),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("operation", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_object_permissions")),
    )
