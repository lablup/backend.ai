"""change permission table names

Revision ID: 643deb439458
Revises: ed84197be4fe
Create Date: 2025-07-11 22:10:52.126619

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "643deb439458"
down_revision = "ed84197be4fe"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("role_permissions", "scope_permissions")
    op.drop_constraint("pk_role_permissions", "scope_permissions", type_="primary")
    op.create_primary_key("pk_scope_permissions", "scope_permissions", ["id"])

    op.rename_table("resource_permissions", "object_permissions")
    op.drop_constraint("pk_resource_permissions", "object_permissions", type_="primary")
    op.create_primary_key("pk_object_permissions", "object_permissions", ["id"])

    op.drop_column("user_roles", "state")
    op.drop_column("user_roles", "expires_at")
    op.drop_column("user_roles", "deleted_at")
    op.alter_column("roles", "state", new_column_name="status")
    op.add_column(
        "scope_permissions",
        sa.Column(
            "status",
            sa.VARCHAR(length=16),
            nullable=False,
            server_default="active",
        ),
    )
    op.add_column(
        "object_permissions",
        sa.Column(
            "status",
            sa.VARCHAR(length=16),
            nullable=False,
            server_default="active",
        ),
    )

    # Create indexes and constraints
    op.create_index(
        "ix_role_id_entity_id",
        "object_permissions",
        ["status", "role_id", "entity_id"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_object_permissions_entity_id_operation",
        "object_permissions",
        ["entity_id", "operation"],
    )
    op.create_index("ix_id_status", "roles", ["id", "status"], unique=False)
    op.create_index(
        "ix_role_id_entity_type_scope_id",
        "scope_permissions",
        ["status", "role_id", "entity_type", "scope_id"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_scope_permissions_entity_operation_scope_id",
        "scope_permissions",
        ["entity_type", "operation", "scope_id"],
    )
    op.create_unique_constraint("uq_user_id_role_id", "user_roles", ["user_id", "role_id"])


def downgrade() -> None:
    # Drop indexes and constraints created in upgrade
    op.drop_constraint("uq_user_id_role_id", "user_roles", type_="unique")
    op.drop_constraint(
        "uq_scope_permissions_entity_operation_scope_id", "scope_permissions", type_="unique"
    )
    op.drop_index("ix_role_id_entity_type_scope_id", table_name="scope_permissions")
    op.drop_index("ix_id_status", table_name="roles")
    op.drop_constraint(
        "uq_object_permissions_entity_id_operation", "object_permissions", type_="unique"
    )
    op.drop_index("ix_role_id_entity_id", table_name="object_permissions")

    op.rename_table("scope_permissions", "role_permissions")
    op.drop_constraint("pk_scope_permissions", "role_permissions", type_="primary")
    op.create_primary_key("pk_role_permissions", "role_permissions", ["id"])

    op.rename_table("object_permissions", "resource_permissions")
    op.drop_constraint("pk_object_permissions", "resource_permissions", type_="primary")
    op.create_primary_key("pk_resource_permissions", "resource_permissions", ["id"])

    op.add_column(
        "user_roles",
        sa.Column(
            "state",
            sa.VARCHAR(length=16),
            nullable=False,
            server_default="active",
        ),
    )
    op.add_column(
        "user_roles",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "user_roles",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.alter_column("roles", "status", new_column_name="state")
    op.drop_column("role_permissions", "status")
    op.drop_column("resource_permissions", "status")
