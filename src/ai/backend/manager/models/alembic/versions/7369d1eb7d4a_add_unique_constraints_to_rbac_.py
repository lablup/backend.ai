"""add unique constraints to rbac permission tables

Revision ID: 7369d1eb7d4a
Revises: 84b901f69d16
Create Date: 2026-01-11 20:28:35.199474

"""
import textwrap

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "7369d1eb7d4a"
down_revision = "84b901f69d16"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Remove duplicate records from object_permissions table
    # Keep the first record (by id) for each unique combination
    conn.execute(
        sa.text(
            textwrap.dedent("""\
                DELETE FROM object_permissions
                WHERE id IN (
                    SELECT id FROM (
                        SELECT id,
                            ROW_NUMBER() OVER (
                                PARTITION BY role_id, entity_type, entity_id, operation
                                ORDER BY id
                            ) AS rn
                        FROM object_permissions
                    ) duplicates
                    WHERE rn > 1
                )
            """)
        )
    )

    # Remove duplicate records from permission_groups table
    # Keep the first record (by id) for each unique combination
    conn.execute(
        sa.text(
            textwrap.dedent("""\
                DELETE FROM permission_groups
                WHERE id IN (
                    SELECT id FROM (
                        SELECT id,
                            ROW_NUMBER() OVER (
                                PARTITION BY role_id, scope_type, scope_id
                                ORDER BY id
                            ) AS rn
                        FROM permission_groups
                    ) duplicates
                    WHERE rn > 1
                )
            """)
        )
    )

    op.create_unique_constraint(
        "uq_object_permissions_role_entity_op",
        "object_permissions",
        ["role_id", "entity_type", "entity_id", "operation"],
    )
    op.create_unique_constraint(
        "uq_permission_groups_role_scope",
        "permission_groups",
        ["role_id", "scope_type", "scope_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_permission_groups_role_scope",
        "permission_groups",
        type_="unique",
    )
    op.drop_constraint(
        "uq_object_permissions_role_entity_op",
        "object_permissions",
        type_="unique",
    )
