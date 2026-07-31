"""add covering indexes for virtual scope permission resolution

Revision ID: aa27f1d5cd35
Revises: 45d3064b95c9
Create Date: 2026-07-14 10:36:47.557321

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "aa27f1d5cd35"
down_revision = "45d3064b95c9"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    # entity_memberships: promote the existing (entity_type, entity_id) index to a
    # covering index so the virtual-scope resolution join is index-only (no heap
    # fetch for virtual_scope_id / permission_cap). DROP first because CREATE ...
    # IF NOT EXISTS matches by name only and would keep the old non-covering index.
    op.execute("DROP INDEX IF EXISTS ix_entity_memberships_entity")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_entity_memberships_entity "
        "ON entity_memberships (entity_type, entity_id) "
        "INCLUDE (virtual_scope_id, permission_cap)"
    )

    # permissions: promote the existing (scope_type, scope_id, entity_type) index to a
    # covering index so the permission-bitmask lookup is index-only (no heap fetch for
    # permission / role_id).
    op.execute("DROP INDEX IF EXISTS ix_permissions_scope_entity")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_permissions_scope_entity "
        "ON permissions (scope_type, scope_id, entity_type) "
        "INCLUDE (permission, role_id)"
    )

    # scope_bindings: add a covering index keyed on virtual_scope_id. The primary key
    # (virtual_scope_id, scope_type, scope_id) does not carry permission_cap, so the
    # scope-binding hop otherwise falls back to a sequential scan + hash join.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_scope_bindings_virtual_scope "
        "ON scope_bindings (virtual_scope_id) "
        "INCLUDE (scope_type, scope_id, permission_cap)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_scope_bindings_virtual_scope")

    # Restore the non-covering permissions index.
    op.execute("DROP INDEX IF EXISTS ix_permissions_scope_entity")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_permissions_scope_entity "
        "ON permissions (scope_type, scope_id, entity_type)"
    )

    # Restore the non-covering entity_memberships index.
    op.execute("DROP INDEX IF EXISTS ix_entity_memberships_entity")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_entity_memberships_entity "
        "ON entity_memberships (entity_type, entity_id)"
    )
