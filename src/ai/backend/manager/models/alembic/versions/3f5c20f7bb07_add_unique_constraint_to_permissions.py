"""add unique constraint to permissions table

Revision ID: 3f5c20f7bb07
Revises: 32ad43817452
Create Date: 2026-02-27 00:00:00.000000

"""

import textwrap

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3f5c20f7bb07"
down_revision = "32ad43817452"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Remove duplicate records from permissions table
    # Keep the first record (by id) for each unique combination
    conn.execute(
        sa.text(
            textwrap.dedent("""\
                DELETE FROM permissions
                WHERE id IN (
                    SELECT id FROM (
                        SELECT id,
                            ROW_NUMBER() OVER (
                                PARTITION BY role_id, scope_type, scope_id, entity_type, operation
                                ORDER BY id
                            ) AS rn
                        FROM permissions
                    ) duplicates
                    WHERE rn > 1
                )
            """)
        )
    )

    op.create_unique_constraint(
        "uq_permissions_role_scope_entity_op",
        "permissions",
        ["role_id", "scope_type", "scope_id", "entity_type", "operation"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_permissions_role_scope_entity_op",
        "permissions",
        type_="unique",
    )
