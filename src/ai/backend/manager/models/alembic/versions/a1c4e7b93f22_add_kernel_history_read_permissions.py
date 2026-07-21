"""add kernel history read permissions to roles that can read kernels

Revision ID: a1c4e7b93f22
Revises: 3f9a1c7b2e04
Create Date: 2026-07-20 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1c4e7b93f22"
down_revision = "3f9a1c7b2e04"
branch_labels = None
depends_on = None

_ENTITY_TYPE = "kernel:history"


def upgrade() -> None:
    conn = op.get_bind()

    # Reading a kernel carries reading its scheduling history, so mirror every
    # existing kernel READ grant onto the history entity within the same scope.
    # ON CONFLICT DO NOTHING keeps this idempotent for release-branch backports.
    conn.execute(
        sa.text("""
            INSERT INTO permissions (role_id, scope_type, scope_id, entity_type, operation)
            SELECT DISTINCT p.role_id, p.scope_type, p.scope_id, :entity_type, 'read'
            FROM permissions p
            WHERE p.entity_type = 'kernel'
              AND p.operation = 'read'
            ON CONFLICT DO NOTHING
        """),
        {"entity_type": _ENTITY_TYPE},
    )


def downgrade() -> None:
    conn = op.get_bind()

    conn.execute(
        sa.text("""
            DELETE FROM permissions
            WHERE entity_type = :entity_type
              AND operation = 'read'
        """),
        {"entity_type": _ENTITY_TYPE},
    )
