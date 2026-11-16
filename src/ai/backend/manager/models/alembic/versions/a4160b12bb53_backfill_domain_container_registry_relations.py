"""Relate each domain to the container registries its allowed_docker_registries names.

A name matches every global registry whose registry_name is that name. A non-global
registry belongs to the projects allowed on it, and the domain-scope image access applies
the names to global registries only.
Each relation also gets the graph edges the relation ops write: the domain governs the
registry under READ, and the registry holds READ on the domain. Without them the domain
reads nothing of the registry.
The allowed_docker_registries column is left in place.
"""

from typing import Final

import sqlalchemy as sa
from alembic import op

revision = "a4160b12bb53"  # Part of: NEXT_RELEASE_VERSION
down_revision = "592dedb4a39c"
branch_labels = None
depends_on = None

_READ: Final[int] = 1

# The distinct (registry node, domain node) pairs the relations name.
_NODE_PAIRS: Final[str] = """
    SELECT DISTINCT node.id AS node, scope.id AS scope
    FROM domain_container_registry_relations r
    JOIN virtual_entities node
      ON node.entity_type = 'container_registry' AND node.entity_id = r.container_registry_id
    JOIN virtual_entities scope
      ON scope.entity_type = 'domain' AND scope.entity_id = r.domain_id
"""


def upgrade() -> None:
    # Every statement skips what is already there, so re-running is a no-op.
    conn = op.get_bind()
    conn.execute(
        sa.text("""
        INSERT INTO domain_container_registry_relations (domain_id, container_registry_id)
        SELECT d.id, cr.id
        FROM domains AS d
        JOIN container_registries AS cr
          ON cr.registry_name = ANY(d.allowed_docker_registries) AND cr.is_global
        ON CONFLICT DO NOTHING
    """)
    )
    conn.execute(
        sa.text(f"""
        INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
        SELECT n.node, n.scope, {_READ} FROM ({_NODE_PAIRS}) n
        ON CONFLICT DO NOTHING
    """)
    )
    conn.execute(
        sa.text(f"""
        INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
        SELECT n.node, n.scope, TRUE FROM ({_NODE_PAIRS}) n
        ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
    """)
    )
    conn.execute(
        sa.text(f"""
        INSERT INTO entity_membership_caps (membership_id, permission, all_fields)
        SELECT m.id, {_READ}, TRUE
        FROM ({_NODE_PAIRS}) n
        JOIN entity_memberships m
          ON m.virtual_entity_id = n.node AND m.member_entity_id = n.scope
        WHERE m.capped
        ON CONFLICT (membership_id, permission) DO UPDATE SET all_fields = TRUE
    """)
    )


def downgrade() -> None:
    # A relation or edge written after the upgrade cannot be told apart from a backfilled one.
    pass
