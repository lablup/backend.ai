"""grant every user's self role the permissions on the keypairs it owns (26.8 followup)

Repeat of e1b7f3d20a94 appended on the 26.8 release head, which the 26.4 splice sits
behind: a database already past that point never walks e1b7f3d20a94, so it needs the
backfill issued again here. A no-op on databases that did apply it.

The chain carries no third repeat on the main head, where a keypair is a field of its
owner and the permission an operation on it reads is the one on the ``user`` entity.

Revision ID: f4a2b7c9e105
Revises: b93d1c47af52
Create Date: 2026-09-07 22:30:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f4a2b7c9e105"
down_revision = "b93d1c47af52"
# Part of: 26.8.4 (backport), 26.9.0 (main)
branch_labels = None
depends_on = None

# A system role its holder carries on that same holder's user scope: the self role.
# Custom roles are left out: one may be assigned to several people, so a keypair grant
# on it would reach everyone holding it rather than the scope's owner.
_SELF_ROLES = """
    SELECT DISTINCT p.role_id, p.scope_id
    FROM permissions p
    JOIN user_roles ur ON ur.role_id = p.role_id AND ur.user_id::text = p.scope_id
    JOIN roles r ON r.id = p.role_id
    WHERE p.scope_type = 'user'
      AND r.source = 'system'
      AND r.status = 'active'
"""

# The owner operation set 21159a293dfb gave every non-member role. grant:* carries no bit.
_GRANT_KEYPAIR_PERMISSIONS = sa.text(f"""
    INSERT INTO permissions (role_id, scope_type, scope_id, entity_type, operation, permission)
    SELECT self_role.role_id, 'user', self_role.scope_id, 'keypair',
           owner_op.operation, owner_op.permission
    FROM ({_SELF_ROLES}) AS self_role
    CROSS JOIN (VALUES
        ('create', 4), ('read', 1), ('update', 2),
        ('soft-delete', 8), ('hard-delete', 16),
        ('grant:all', 0), ('grant:read', 0), ('grant:update', 0),
        ('grant:soft-delete', 0), ('grant:hard-delete', 0)
    ) AS owner_op(operation, permission)
    ON CONFLICT DO NOTHING
""")

# INSERT ... SELECT binds no per-row parameter, so the keypair count needs no chunking.
_BIND_KEYPAIRS_TO_OWNERS = sa.text("""
    INSERT INTO association_scopes_entities
        (scope_type, scope_id, entity_type, entity_id, relation_type)
    SELECT 'user', k."user"::text, 'keypair', k.access_key, 'auto'
    FROM keypairs k
    ON CONFLICT DO NOTHING
""")


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(_GRANT_KEYPAIR_PERMISSIONS)
    conn.execute(_BIND_KEYPAIRS_TO_OWNERS)


def downgrade() -> None:
    pass
