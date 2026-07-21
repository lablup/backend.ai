"""add kernel history read permissions to roles that can read sessions

Revision ID: a1c4e7b93f22
Revises: 3f9a1c7b2e04
Create Date: 2026-07-20 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1c4e7b93f22"
down_revision = "3f9a1c7b2e04"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_ENTITY_TYPE = "kernel:history"

# A kernel is reachable through its owning session, and nothing grants the bare
# `kernel` entity, so session READ is what carries kernel history access.
_SOURCE_ENTITY_TYPE = "session"


def upgrade() -> None:
    conn = op.get_bind()

    # Mirror every session READ grant onto the history entity within the same
    # scope, carrying the source permission bits (the column is NOT NULL).
    # ON CONFLICT DO NOTHING keeps this idempotent for release-branch backports.
    conn.execute(
        sa.text("""
            INSERT INTO permissions (
                role_id, scope_type, scope_id, entity_type, operation, permission
            )
            SELECT DISTINCT p.role_id, p.scope_type, p.scope_id,
                   :entity_type, 'read', p.permission
            FROM permissions p
            WHERE p.entity_type = :source_entity_type
              AND p.operation = 'read'
            ON CONFLICT DO NOTHING
        """),
        {"entity_type": _ENTITY_TYPE, "source_entity_type": _SOURCE_ENTITY_TYPE},
    )


def downgrade() -> None:
    # No-op: kernel:history READ is part of each scope role's intended permission
    # set (granted natively at role creation for roles created after the fix).
    # A mirror-based DELETE cannot distinguish rows inserted by this backfill
    # from those granted at creation, so it would strip permissions the roles
    # legitimately hold. Leaving the backfilled rows in place is safe.
    pass
