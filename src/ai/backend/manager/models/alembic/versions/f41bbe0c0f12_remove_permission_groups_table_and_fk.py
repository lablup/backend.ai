"""remove_permission_groups_table_and_fk

Revision ID: f41bbe0c0f12
Revises: 299deadfb77e
Create Date: 2026-02-11 02:43:17.099347

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "f41bbe0c0f12"
down_revision = "299deadfb77e"
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
    conn = op.get_bind()

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

    # Populate permission_groups from existing permissions data
    conn.execute(
        sa.text("""
        INSERT INTO permission_groups (role_id, scope_type, scope_id)
        SELECT DISTINCT role_id, scope_type, scope_id FROM permissions
    """)
    )

    # Add permission_group_id columns as nullable first
    op.add_column(
        "permissions",
        sa.Column("permission_group_id", GUID(), nullable=True),
    )
    op.add_column(
        "object_permissions",
        sa.Column("permission_group_id", GUID(), nullable=True),
    )

    # Backfill permissions.permission_group_id
    conn.execute(
        sa.text("""
        UPDATE permissions p
        SET permission_group_id = pg.id
        FROM permission_groups pg
        WHERE pg.role_id = p.role_id
          AND pg.scope_type = p.scope_type
          AND pg.scope_id = p.scope_id
    """)
    )

    # Backfill object_permissions.permission_group_id
    conn.execute(
        sa.text("""
        UPDATE object_permissions op
        SET permission_group_id = pg.id
        FROM permission_groups pg, association_scopes_entities ase
        WHERE pg.scope_type = ase.scope_type
          AND pg.scope_id = ase.scope_id
          AND ase.entity_type = op.entity_type
          AND ase.entity_id = op.entity_id
          AND pg.role_id = op.role_id
    """)
    )

    # Delete orphan object_permissions that couldn't be mapped to a permission_group
    conn.execute(
        sa.text("""
        DELETE FROM object_permissions WHERE permission_group_id IS NULL
    """)
    )

    # Set columns to NOT NULL after backfill
    op.alter_column("permissions", "permission_group_id", nullable=False)
    op.alter_column("object_permissions", "permission_group_id", nullable=False)

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
