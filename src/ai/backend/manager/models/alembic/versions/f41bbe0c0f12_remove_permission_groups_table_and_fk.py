"""remove_permission_groups_table_and_fk

Revision ID: f41bbe0c0f12
Revises: 8fd6f47bd226
Create Date: 2026-02-11 02:43:17.099347

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "f41bbe0c0f12"
down_revision = "8fd6f47bd226"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop FK constraints from permissions and object_permissions
    op.drop_constraint(
        op.f("fk_permissions_permission_group_id_permission_groups"),
        "permissions",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_object_permissions_permission_group_id_permission_groups"),
        "object_permissions",
        type_="foreignkey",
    )

    # Drop indexes on permission_group_id columns
    op.drop_index("ix_id_permission_group_id", table_name="permissions")
    op.drop_index("ix_object_permissions_permission_group_id", table_name="object_permissions")

    # Drop permission_group_id columns
    op.drop_column("permissions", "permission_group_id")
    op.drop_column("object_permissions", "permission_group_id")

    # Drop indexes and constraints on permission_groups table
    op.drop_index("ix_id_role_id_scope_id", table_name="permission_groups")
    op.drop_constraint("uq_permission_groups_role_scope", "permission_groups", type_="unique")

    # Drop permission_groups table
    op.drop_table("permission_groups")


def downgrade() -> None:
    # Recreate permission_groups table
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
    op.create_unique_constraint(
        "uq_permission_groups_role_scope",
        "permission_groups",
        ["role_id", "scope_type", "scope_id"],
    )

    # Restore permission_group_id columns
    op.add_column(
        "permissions",
        sa.Column("permission_group_id", GUID(), nullable=False),
    )
    op.add_column(
        "object_permissions",
        sa.Column("permission_group_id", GUID(), nullable=False),
    )

    # Restore indexes
    op.create_index(
        "ix_id_permission_group_id", "permissions", ["id", "permission_group_id"], unique=False
    )
    op.create_index(
        "ix_object_permissions_permission_group_id",
        "object_permissions",
        ["permission_group_id"],
        unique=False,
    )

    # Restore FK constraints
    op.create_foreign_key(
        op.f("fk_permissions_permission_group_id_permission_groups"),
        "permissions",
        "permission_groups",
        ["permission_group_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        op.f("fk_object_permissions_permission_group_id_permission_groups"),
        "object_permissions",
        "permission_groups",
        ["permission_group_id"],
        ["id"],
        ondelete="CASCADE",
    )
