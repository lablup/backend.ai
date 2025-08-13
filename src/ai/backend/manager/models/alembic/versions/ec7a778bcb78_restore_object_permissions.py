"""restore object permissions

Revision ID: ec7a778bcb78
Revises: 28fecac94e67
Create Date: 2025-08-07 20:34:59.442159

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "ec7a778bcb78"
down_revision = "28fecac94e67"
branch_labels = None
depends_on = None


def upgrade() -> None:
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
    op.create_index(
        "ix_role_id_entity_id",
        "object_permissions",
        ["status", "role_id", "entity_id"],
        unique=False,
    )
    op.drop_constraint(
        "uq_scope_permissions_entity_operation_scope_id", "scope_permissions", type_="unique"
    )


def downgrade() -> None:
    op.create_unique_constraint(
        "uq_scope_permissions_entity_operation_scope_id",
        "scope_permissions",
        ["entity_type", "operation", "scope_id"],
    )
    op.drop_index("ix_role_id_entity_id", table_name="object_permissions")
    op.drop_table("object_permissions")
