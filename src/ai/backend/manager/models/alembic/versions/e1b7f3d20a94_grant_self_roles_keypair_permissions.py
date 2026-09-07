"""grant every user's self role the permissions on the keypairs it owns

The self role a user creation provisions covers only the resource entity types, which
leave out ``keypair``, so a user created after 21159a293dfb holds no permission on its
own keypairs and is refused on ``/auth/ssh-keypair``. Backfills those rows, together
with the keypair AUTO edges a keypair created outside the RBAC creator never got, so
the scope chain resolves a keypair to its owner.

Spliced in at the 26.4 release head; f4a2b7c9e105 repeats it at the 26.8 one. No repeat
follows on the main head: there a keypair is a field of its owner, so the permission an
operation on it reads is the one on the ``user`` entity, which the self role already
holds. Idempotent via ``ON CONFLICT DO NOTHING``.

Revision ID: e1b7f3d20a94
Revises: bd1bf0524350
Create Date: 2026-09-07 22:30:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e1b7f3d20a94"
down_revision = "bd1bf0524350"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

# A role its holder carries on that same holder's user scope: the self role. Derived
# from the permissions the role already holds, so both the data-migrated roles
# (``role_user_<username>``) and the runtime ones (``user-<id8>``) match.
_SELF_ROLES = """
    SELECT DISTINCT p.role_id, p.scope_id
    FROM permissions p
    JOIN user_roles ur ON ur.role_id = p.role_id AND ur.user_id::text = p.scope_id
    JOIN roles r ON r.id = p.role_id
    WHERE p.scope_type = 'user'
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
