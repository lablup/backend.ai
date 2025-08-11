"""expand rbac tables

Revision ID: af94d53c5392
Revises: 42feff246198
Create Date: 2025-08-11 21:01:38.306466

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "af94d53c5392"
down_revision = "42feff246198"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "permission_groups",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("status", sa.VARCHAR(length=32), server_default="active", nullable=False),
        sa.Column("role_id", GUID(), nullable=False),
        sa.Column("scope_type", sa.VARCHAR(length=32), nullable=False),
        sa.Column("scope_id", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_permission_groups")),
    )
    op.create_index(
        "ix_id_status_role_id", "permission_groups", ["id", "status", "role_id"], unique=False
    )
    op.add_column("scope_permissions", sa.Column("permission_group_id", GUID(), nullable=False))
    op.drop_index("ix_role_id_entity_type_scope_id", table_name="scope_permissions")
    op.create_index(
        "ix_status_permission_group_id",
        "scope_permissions",
        ["status", "permission_group_id"],
        unique=False,
    )
    op.drop_column("scope_permissions", "scope_type")
    op.drop_column("scope_permissions", "role_id")
    op.drop_column("scope_permissions", "scope_id")


def downgrade() -> None:
    op.add_column(
        "scope_permissions",
        sa.Column("scope_id", sa.VARCHAR(length=64), autoincrement=False, nullable=False),
    )
    op.add_column(
        "scope_permissions",
        sa.Column("role_id", postgresql.UUID(), autoincrement=False, nullable=False),
    )
    op.add_column(
        "scope_permissions",
        sa.Column("scope_type", sa.VARCHAR(length=32), autoincrement=False, nullable=False),
    )
    op.drop_index("ix_status_permission_group_id", table_name="scope_permissions")
    op.create_index(
        "ix_role_id_entity_type_scope_id",
        "scope_permissions",
        ["status", "role_id", "entity_type", "scope_id"],
        unique=False,
    )
    op.drop_column("scope_permissions", "permission_group_id")
    op.drop_index("ix_id_status_role_id", table_name="permission_groups")
    op.drop_table("permission_groups")
