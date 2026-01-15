"""add foreign key constraints to rbac permission tables

Revision ID: f8a9b3c2d1e0
Revises: 71343531dd5a
Create Date: 2026-01-14 20:30:00.000000

"""

import textwrap

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "f8a9b3c2d1e0"
down_revision = "71343531dd5a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Step 1: Clean up orphan records in permission_groups
    # Delete permission_groups where role_id does not exist in roles table
    # Using NOT EXISTS for better performance with large roles table
    conn.execute(
        sa.text(
            textwrap.dedent("""\
                DELETE FROM permission_groups pg
                WHERE NOT EXISTS (
                    SELECT 1 FROM roles r WHERE r.id = pg.role_id
                )
            """)
        )
    )

    # Step 2: Clean up orphan records in permissions
    # Delete permissions where permission_group_id does not exist in permission_groups table
    # Using NOT EXISTS for better performance with large permission_groups table
    conn.execute(
        sa.text(
            textwrap.dedent("""\
                DELETE FROM permissions p
                WHERE NOT EXISTS (
                    SELECT 1 FROM permission_groups pg WHERE pg.id = p.permission_group_id
                )
            """)
        )
    )

    # Step 3: Add permission_group_id column to object_permissions (nullable first)
    op.add_column(
        "object_permissions",
        sa.Column("permission_group_id", GUID(), nullable=True),
    )

    # Step 4: Migrate data - set permission_group_id based on role_id and scope mapping
    # Find permission_group with same role_id where object_permission's entity is mapped to the scope
    # Using CTE with DISTINCT ON for better performance (single pass instead of correlated subquery)
    conn.execute(
        sa.text(
            textwrap.dedent("""\
                WITH matched AS (
                    SELECT DISTINCT ON (op.id) op.id AS op_id, pg.id AS pg_id
                    FROM object_permissions op
                    JOIN permission_groups pg ON pg.role_id = op.role_id
                    JOIN association_scopes_entities ase
                        ON pg.scope_type = ase.scope_type
                        AND pg.scope_id = ase.scope_id
                        AND ase.entity_type = op.entity_type
                        AND ase.entity_id = op.entity_id
                )
                UPDATE object_permissions op
                SET permission_group_id = matched.pg_id
                FROM matched
                WHERE op.id = matched.op_id
            """)
        )
    )

    # Step 5: Delete object_permissions that couldn't be mapped (orphans)
    conn.execute(
        sa.text(
            textwrap.dedent("""\
                DELETE FROM object_permissions
                WHERE permission_group_id IS NULL
            """)
        )
    )

    # Step 6: Make permission_group_id NOT NULL
    op.alter_column(
        "object_permissions",
        "permission_group_id",
        nullable=False,
    )

    # Step 7: Add FK constraint to object_permissions.permission_group_id -> permission_groups.id
    op.create_foreign_key(
        op.f("fk_object_permissions_permission_group_id_permission_groups"),
        "object_permissions",
        "permission_groups",
        ["permission_group_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Step 8: Add FK constraint to permissions.permission_group_id -> permission_groups.id
    op.create_foreign_key(
        op.f("fk_permissions_permission_group_id_permission_groups"),
        "permissions",
        "permission_groups",
        ["permission_group_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Step 9: Add index for the new column
    op.create_index(
        "ix_object_permissions_permission_group_id",
        "object_permissions",
        ["permission_group_id"],
    )


def downgrade() -> None:
    # Drop index
    op.drop_index("ix_object_permissions_permission_group_id", table_name="object_permissions")

    # Drop FK constraints
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

    # Drop column
    op.drop_column("object_permissions", "permission_group_id")
