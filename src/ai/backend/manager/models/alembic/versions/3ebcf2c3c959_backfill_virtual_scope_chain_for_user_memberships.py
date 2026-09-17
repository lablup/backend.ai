"""backfill virtual-scope chain for user memberships

Revision ID: 3ebcf2c3c959
Revises: 8f21c46a0b73
Create Date: 2026-08-06 14:06:17

"""

# Part of: NEXT_RELEASE_VERSION

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3ebcf2c3c959"
down_revision = "8f21c46a0b73"
branch_labels = None
depends_on = None


_UUID_TEXT = "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"


def upgrade() -> None:
    """Backfill the virtual-scope chain (virtual_scopes, entity_memberships,
    scope_bindings) for the DOMAIN/USER and PROJECT/USER mappings recorded in
    association_scopes_entities, so membership reads can rely on the chain.
    Idempotent via ON CONFLICT.
    """
    # Every domain, project, and user doubles as a scope; materialize the
    # virtual scopes missing for rows created before the virtual-scope chain.
    op.execute(
        sa.text(
            """
            INSERT INTO virtual_scopes (scope_type, scope_id)
            SELECT 'domain', id FROM domains
            ON CONFLICT (scope_type, scope_id) DO NOTHING
            """
        )
    )
    op.execute(
        sa.text(
            """
            INSERT INTO virtual_scopes (scope_type, scope_id)
            SELECT 'project', id FROM groups
            ON CONFLICT (scope_type, scope_id) DO NOTHING
            """
        )
    )
    op.execute(
        sa.text(
            """
            INSERT INTO virtual_scopes (scope_type, scope_id)
            SELECT 'user', uuid FROM users
            ON CONFLICT (scope_type, scope_id) DO NOTHING
            """
        )
    )
    # Pre-rekey rows key a domain scope by its name, so skip anything that is
    # not a UUID: the WHERE filters the association scan before the join casts.
    op.execute(
        sa.text(
            f"""
            INSERT INTO entity_memberships (virtual_scope_id, entity_type, entity_id)
            SELECT vs.id, 'user', CAST(a.entity_id AS uuid)
            FROM association_scopes_entities a
            JOIN virtual_scopes vs
                ON vs.scope_type = a.scope_type
                AND vs.scope_id = CAST(a.scope_id AS uuid)
            WHERE a.entity_type = 'user'
                AND a.scope_type IN ('domain', 'project')
                AND a.scope_id ~ '{_UUID_TEXT}'
                AND a.entity_id ~ '{_UUID_TEXT}'
            ON CONFLICT (virtual_scope_id, entity_type, entity_id) DO NOTHING
            """
        )
    )
    # Bind the scope into each member user's own virtual scope (one-way).
    op.execute(
        sa.text(
            f"""
            INSERT INTO scope_bindings (virtual_scope_id, scope_type, scope_id)
            SELECT uvs.id, a.scope_type, CAST(a.scope_id AS uuid)
            FROM association_scopes_entities a
            JOIN virtual_scopes uvs
                ON uvs.scope_type = 'user'
                AND uvs.scope_id = CAST(a.entity_id AS uuid)
            WHERE a.entity_type = 'user'
                AND a.scope_type IN ('domain', 'project')
                AND a.scope_id ~ '{_UUID_TEXT}'
                AND a.entity_id ~ '{_UUID_TEXT}'
            ON CONFLICT (virtual_scope_id, scope_type, scope_id) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    """No-op: backfilled rows are indistinguishable from runtime-written ones."""
