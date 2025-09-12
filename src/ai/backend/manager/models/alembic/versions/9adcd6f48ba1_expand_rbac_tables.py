"""expand rbac tables

Revision ID: 9adcd6f48ba1
Revises: 2cc8337d78a3
Create Date: 2025-08-12 21:02:31.660415

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from ai.backend.manager.models.base import (
    GUID,
)

# revision identifiers, used by Alembic.
revision = "9adcd6f48ba1"
down_revision = "2cc8337d78a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "permission_groups",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("role_id", GUID(), nullable=False),
        sa.Column("scope_type", sa.VARCHAR(length=32), nullable=False),
        sa.Column("scope_id", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_permission_groups")),
    )
    op.create_index(
        "ix_id_role_id_scope_id", "permission_groups", ["id", "role_id", "scope_id"], unique=False
    )
    op.create_table(
        "permissions",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("permission_group_id", GUID(), nullable=False),
        sa.Column("entity_type", sa.VARCHAR(length=32), nullable=False),
        sa.Column("operation", sa.VARCHAR(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_permissions")),
    )
    op.create_index(
        "ix_id_permission_group_id", "permissions", ["id", "permission_group_id"], unique=False
    )
    op.drop_index("ix_role_id_entity_type_scope_id", table_name="scope_permissions")
    op.drop_table("scope_permissions")
    op.drop_index("ix_role_id_entity_id", table_name="object_permissions")
    op.create_index(
        "ix_id_role_id_entity_id",
        "object_permissions",
        ["id", "role_id", "entity_id"],
        unique=False,
    )
    op.drop_column("object_permissions", "status")
    op.drop_column("object_permissions", "created_at")


def downgrade() -> None:
    op.add_column(
        "object_permissions",
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.add_column(
        "object_permissions",
        sa.Column(
            "status",
            sa.VARCHAR(length=64),
            server_default=sa.text("'active'::character varying"),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.drop_index("ix_id_role_id_entity_id", table_name="object_permissions")
    op.create_index(
        "ix_role_id_entity_id",
        "object_permissions",
        ["status", "role_id", "entity_id"],
        unique=False,
    )
    op.create_table(
        "scope_permissions",
        sa.Column(
            "id",
            postgresql.UUID(),
            server_default=sa.text("uuid_generate_v4()"),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.VARCHAR(length=64),
            server_default=sa.text("'active'::character varying"),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column("entity_type", sa.VARCHAR(length=32), autoincrement=False, nullable=False),
        sa.Column("operation", sa.VARCHAR(length=32), autoincrement=False, nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column("scope_id", sa.VARCHAR(length=64), autoincrement=False, nullable=False),
        sa.Column("role_id", postgresql.UUID(), autoincrement=False, nullable=False),
        sa.Column("scope_type", sa.VARCHAR(length=32), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_scope_permissions"),
    )
    op.create_index(
        "ix_role_id_entity_type_scope_id",
        "scope_permissions",
        ["status", "role_id", "entity_type", "scope_id"],
        unique=False,
    )
    op.drop_index("ix_id_permission_group_id", table_name="permissions")
    op.drop_table("permissions")
    op.drop_index("ix_id_role_id_scope_id", table_name="permission_groups")
    op.drop_table("permission_groups")
