"""Put every entity in the graph

A row written before the graph existed has none of the graph rows its creation writes
now, and the earlier revisions filled them for a few entity types only. Write, for every
row on file, what the runtime writes: its node, the edges to the scopes it was created
in, the project rosters, the relations, and the accepted shares. Then give the scopes
that had no node when the preset roles were written their roles and grants.

Revision ID: dafe06a6c763
Revises: bf75b41e80ae
Create Date: 2026-09-16

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "dafe06a6c763"  # Part of: NEXT_RELEASE_VERSION
down_revision = "bf75b41e80ae"
branch_labels = None
depends_on = None

# (entity type, table, id column) of every table holding entity rows.
NODE_SOURCES: Final[tuple[tuple[str, str, str], ...]] = (
    ("agent", "agents", "uuid"),
    ("app_config_allow_list", "app_config_allow_list", "id"),
    ("app_config_definition", "app_config_definitions", "id"),
    ("app_config_fragment", "app_config_fragments", "id"),
    ("artifact", "artifacts", "id"),
    ("artifact_registry", "huggingface_registries", "id"),
    ("artifact_registry", "reservoir_registries", "id"),
    ("client_ip_masking_policy", "client_ip_masking_policies", "id"),
    ("container_registry", "container_registries", "id"),
    ("deployment", "endpoints", "id"),
    ("deployment_preset", "deployment_revision_presets", "id"),
    ("domain", "domains", "id"),
    ("entity_share", "entity_shares", "id"),
    ("idle_checker", "idle_checkers", "id"),
    ("image", "images", "id"),
    ("keypair_resource_policy", "keypair_resource_policies", "uuid"),
    ("login_client_type", "login_client_types", "id"),
    ("model_card", "model_cards", "id"),
    ("network", "networks", "id"),
    ("notification_channel", "notification_channels", "id"),
    ("notification_rule", "notification_rules", "id"),
    ("object_storage", "object_storages", "id"),
    ("project", "groups", "id"),
    ("project_resource_policy", "project_resource_policies", "uuid"),
    ("prometheus_query_preset", "prometheus_query_presets", "id"),
    ("prometheus_query_preset_category", "prometheus_query_preset_categories", "id"),
    ("resource_group", "scaling_groups", "id"),
    ("resource_preset", "resource_presets", "id"),
    ("resource_slot_type", "resource_slot_types", "uuid"),
    ("retention_policy", "retention_policies", "id"),
    ("role", "roles", "id"),
    ("role_preset", "role_presets", "id"),
    ("runtime_variant", "runtime_variants", "id"),
    ("runtime_variant_preset", "runtime_variant_presets", "id"),
    ("service_catalog", "service_catalog", "id"),
    ("session", "sessions", "id"),
    ("session_group", "session_groups", "id"),
    ("session_template", "session_templates", "id"),
    ("storage_namespace", "storage_namespace", "id"),
    ("user", "users", "uuid"),
    ("user_resource_policy", "user_resource_policies", "uuid"),
    ("vfolder", "vfolders", "id"),
    ("vfs_storage", "vfs_storages", "id"),
)

# (entity type, query answering entity_id, scope_type, scope_id) for each scope a
# creator spec's ``created_in`` names.
CREATED_IN_SOURCES: Final[tuple[tuple[str, str], ...]] = (
    ("agent", "SELECT uuid, 'resource_group', resource_group_id FROM agents"),
    (
        "app_config_fragment",
        "SELECT id, scope_type, scope_id FROM app_config_fragments"
        " WHERE scope_type IN ('domain', 'user')",
    ),
    ("deployment", "SELECT id, 'project', project FROM endpoints"),
    ("deployment", "SELECT id, 'user', session_owner FROM endpoints"),
    ("entity_share", "SELECT id, target_entity_type, target_entity_id FROM entity_shares"),
    ("image", "SELECT id, 'container_registry', registry_id FROM images"),
    (
        "image",
        "SELECT i.id, 'project', g.id FROM images i"
        " JOIN groups g ON g.type = 'personal' AND g.creator_id = i.creator_id"
        " WHERE i.customized",
    ),
    ("model_card", "SELECT id, 'project', project FROM model_cards"),
    ("network", "SELECT id, 'project', project FROM networks"),
    (
        "project",
        "SELECT g.id, 'domain', d.id FROM groups g JOIN domains d ON d.name = g.domain_name",
    ),
    ("role", "SELECT id, scope_type, scope_id FROM roles"),
    ("session", "SELECT id, 'user', user_uuid FROM sessions"),
    ("session", "SELECT id, 'project', group_id FROM sessions"),
    ("session_group", "SELECT id, 'project', project_id FROM session_groups"),
    ("session_group", "SELECT id, 'user', owner_user_id FROM session_groups"),
    ("session_template", "SELECT id, 'user', user_uuid FROM session_templates"),
    (
        "session_template",
        "SELECT id, 'project', group_id FROM session_templates WHERE group_id IS NOT NULL",
    ),
    ("user", "SELECT uuid, 'domain', domain_id FROM users"),
    ("vfolder", """SELECT id, 'project', "group" FROM vfolders WHERE "group" IS NOT NULL"""),
)

# (target type, query answering target_id, scope_type, scope_id) for each relation row.
RELATION_SOURCES: Final[tuple[tuple[str, str], ...]] = (
    (
        "container_registry",
        "SELECT registry_id, 'project', group_id FROM association_container_registries_groups",
    ),
    ("idle_checker", "SELECT idle_checker_id, scope_type, scope_id FROM idle_checker_bindings"),
    ("idle_checker", "SELECT idle_checker_id, 'session', session_id FROM session_idle_checks"),
    ("resource_group", "SELECT resource_group_id, 'domain', domain_id FROM sgroups_for_domains"),
    ("resource_group", """SELECT resource_group_id, 'project', "group" FROM sgroups_for_groups"""),
    (
        "resource_group",
        """SELECT s.resource_group_id, 'user', k."user" FROM sgroups_for_keypairs s"""
        " JOIN keypairs k ON k.access_key = s.access_key",
    ),
)

_READ: Final = 1
_PERMISSION_BITS: Final = (1, 2, 4, 8, 16)
_MAX_ROLE_NAME_LENGTH: Final = 64
PROJECT_ADMIN_PRESET_ID: Final = "22c4db03-24aa-5ff8-b5a9-64b2a2182413"

_ADD_SELF_MEMBERSHIPS: Final = sa.text("""
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT id, id, FALSE FROM virtual_entities
    ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
""")

_ADD_SELF_BINDINGS: Final = sa.text("""
    INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
    SELECT id, id, NULL FROM virtual_entities
    ON CONFLICT DO NOTHING
""")

# An own edge lends everything, so no cap row stands under one.
_DROP_CAPS_OF_OWN_EDGES: Final = sa.text("""
    DELETE FROM entity_membership_caps c
    USING entity_memberships m
    WHERE c.membership_id = m.id AND m.capped IS FALSE
""")

# A bit lent on every field names no paths.
_DROP_PATHS_OF_WHOLE_CAPS: Final = sa.text("""
    DELETE FROM entity_membership_fields f
    USING entity_membership_caps c
    WHERE f.cap_id = c.id AND c.all_fields
""")

_PROJECT_USER_EDGES: Final = """
    SELECT m.id
    FROM entity_memberships m
    JOIN virtual_entities p ON p.id = m.virtual_entity_id AND p.entity_type = 'project'
    JOIN virtual_entities u ON u.id = m.member_entity_id AND u.entity_type = 'user'
"""

_CAP_ROSTER_EDGES: Final = sa.text(f"""
    UPDATE entity_memberships SET capped = TRUE
    WHERE capped IS FALSE AND id IN ({_PROJECT_USER_EDGES})
""")

# A personal project's creator is its one member. Every other member's edge is already in
# the graph; `association_groups_users` stopped being written before that and is not read.
_ADD_PERSONAL_ROSTER_EDGES: Final = sa.text("""
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT p.id, u.id, TRUE
    FROM groups g
    JOIN virtual_entities p ON p.entity_type = 'project' AND p.entity_id = g.id
    JOIN virtual_entities u ON u.entity_type = 'user' AND u.entity_id = g.creator_id
    WHERE g.type = 'personal'
    ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
""")

_ADD_ROSTER_CAPS: Final = sa.text(f"""
    INSERT INTO entity_membership_caps (membership_id, permission, all_fields)
    SELECT id, {_READ}, TRUE FROM ({_PROJECT_USER_EDGES}) e
    ON CONFLICT (membership_id, permission) DO UPDATE SET all_fields = TRUE
""")

# A project governs no user: the binding the association table left is dropped.
_DROP_PROJECT_BINDINGS_OF_USERS: Final = sa.text("""
    DELETE FROM scope_bindings b
    USING virtual_entities u, virtual_entities p
    WHERE b.virtual_entity_id = u.id AND u.entity_type = 'user'
      AND b.scope_entity_id = p.id AND p.entity_type = 'project'
""")

# Where a scope takes a share: a project itself, a user into their personal project.
_ACCEPTED_SHARES: Final = """
    SELECT DISTINCT landing.id AS landing_node, target.id AS target_node,
           COALESCE(s.permission_cap, 31) AS cap
    FROM entity_shares s
    LEFT JOIN groups personal
      ON s.recipient_entity_type = 'user'
     AND personal.type = 'personal' AND personal.creator_id = s.recipient_entity_id
    JOIN virtual_entities landing
      ON landing.entity_type = 'project'
     AND landing.entity_id = CASE WHEN s.recipient_entity_type = 'project'
                                  THEN s.recipient_entity_id ELSE personal.id END
    JOIN virtual_entities target
      ON target.entity_type = s.target_entity_type AND target.entity_id = s.target_entity_id
    WHERE s.status = 'accepted' AND s.recipient_entity_id IS NOT NULL
"""

_ADD_SHARE_EDGES: Final = sa.text(f"""
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT DISTINCT a.landing_node, a.target_node, TRUE FROM ({_ACCEPTED_SHARES}) a
    ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
""")

_ADD_SHARE_CAPS: Final = sa.text(f"""
    INSERT INTO entity_membership_caps (membership_id, permission, all_fields)
    SELECT DISTINCT m.id, bit, TRUE
    FROM ({_ACCEPTED_SHARES}) a
    JOIN entity_memberships m
      ON m.virtual_entity_id = a.landing_node AND m.member_entity_id = a.target_node
    CROSS JOIN unnest(ARRAY{list(_PERMISSION_BITS)}) AS bit
    WHERE m.capped AND a.cap & bit <> 0
    ON CONFLICT (membership_id, permission) DO UPDATE SET all_fields = TRUE
""")

_SUFFIX_LENGTH: Final = 9

# The role of each active preset every domain, project and user in the graph lacks,
# named as the runtime names a role of a preset without a name template.
_ADD_PRESET_ROLES: Final = sa.text(f"""
    INSERT INTO roles (name, source, status, auto_assign, role_preset_id, scope_type, scope_id)
    SELECT
        CASE WHEN p.role_name_template IS NULL
             THEN left(p.name, {_MAX_ROLE_NAME_LENGTH - _SUFFIX_LENGTH})
                  || '-' || left(s.entity_id::text, 8)
             ELSE s.entity_type || '-' || left(s.entity_id::text, 8) || '-role' END,
        'system', 'active', p.auto_assign, p.id, s.entity_type, s.entity_id
    FROM role_presets p
    JOIN virtual_entities s ON s.entity_type = p.scope_type
    WHERE p.deleted IS FALSE
      AND s.entity_type IN ('domain', 'project', 'user')
      AND NOT EXISTS (
          SELECT 1 FROM roles r
          WHERE r.role_preset_id = p.id AND r.scope_type = s.entity_type
            AND r.scope_id = s.entity_id
      )
    RETURNING id
""")

_ADD_ROLE_PERMISSIONS: Final = sa.text("""
    INSERT INTO permissions (role_id, entity_type, permission)
    SELECT r.id, pp.entity_type, pp.permission
    FROM roles r
    JOIN role_permission_presets pp ON pp.role_preset_id = r.role_preset_id
    WHERE r.id = ANY(:role_ids) AND pp.permission <> 0
""")

_GRANT_USER_AND_DOMAIN_ROLES: Final = sa.text("""
    INSERT INTO user_roles (user_id, role_id)
    SELECT u.uuid, r.id
    FROM users u
    JOIN roles r
      ON (r.scope_type = 'user' AND r.scope_id = u.uuid)
      OR (r.scope_type = 'domain' AND r.scope_id = u.domain_id)
    WHERE r.auto_assign IS TRUE AND r.status = 'active'
    ON CONFLICT (user_id, role_id) DO NOTHING
""")

_ROSTER: Final = """
    SELECT p.entity_id AS project_id, u.entity_id AS user_id
    FROM entity_memberships m
    JOIN virtual_entities p ON p.id = m.virtual_entity_id AND p.entity_type = 'project'
    JOIN virtual_entities u ON u.id = m.member_entity_id AND u.entity_type = 'user'
"""

_GRANT_PROJECT_ROLES: Final = sa.text(f"""
    INSERT INTO user_roles (user_id, role_id)
    SELECT roster.user_id, r.id
    FROM ({_ROSTER}) roster
    JOIN roles r ON r.scope_type = 'project' AND r.scope_id = roster.project_id
    WHERE r.auto_assign IS TRUE AND r.status = 'active'
    ON CONFLICT (user_id, role_id) DO NOTHING
""")

_GRANT_CREATOR_ROLES: Final = sa.text(f"""
    INSERT INTO user_roles (user_id, role_id)
    SELECT g.creator_id, r.id
    FROM groups g
    JOIN ({_ROSTER}) roster ON roster.project_id = g.id AND roster.user_id = g.creator_id
    JOIN roles r
      ON r.scope_type = 'project' AND r.scope_id = g.id
     AND r.role_preset_id = CAST(:preset_id AS uuid)
    ON CONFLICT (user_id, role_id) DO NOTHING
""")


def _add_nodes(conn: sa.Connection, sources: tuple[tuple[str, str, str], ...]) -> None:
    for entity_type, table, id_column in sources:
        conn.execute(
            sa.text(f"""
                INSERT INTO virtual_entities (entity_type, entity_id)
                SELECT :entity_type, {id_column} FROM {table}
                ON CONFLICT (entity_type, entity_id) DO NOTHING
            """),
            {"entity_type": entity_type},
        )


def _node_pairs(entity_type_param: str, source: str) -> str:
    """The distinct (entity node, scope node) pairs a source names."""
    return f"""
        SELECT DISTINCT node.id AS node, scope.id AS scope
        FROM ({source}) s (entity_id, scope_type, scope_id)
        JOIN virtual_entities node
          ON node.entity_type = :{entity_type_param} AND node.entity_id = s.entity_id
        JOIN virtual_entities scope
          ON scope.entity_type = s.scope_type AND scope.entity_id = s.scope_id
    """


def _add_created_in_edges(conn: sa.Connection) -> None:
    for entity_type, source in CREATED_IN_SOURCES:
        pairs = _node_pairs("entity_type", source)
        params = {"entity_type": entity_type}
        conn.execute(
            sa.text(f"""
                INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
                SELECT n.scope, n.node, FALSE FROM ({pairs}) n
                ON CONFLICT (virtual_entity_id, member_entity_id) DO UPDATE SET capped = FALSE
            """),
            params,
        )
        conn.execute(
            sa.text(f"""
                INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
                SELECT n.node, n.scope, NULL FROM ({pairs}) n
                ON CONFLICT DO NOTHING
            """),
            params,
        )
    conn.execute(_DROP_CAPS_OF_OWN_EDGES)


def _add_relation_edges(conn: sa.Connection) -> None:
    """The scope governs the target under READ; the target holds READ on the scope."""
    for target_type, source in RELATION_SOURCES:
        pairs = _node_pairs("target_type", source)
        params = {"target_type": target_type}
        conn.execute(
            sa.text(f"""
                INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
                SELECT n.node, n.scope, {_READ} FROM ({pairs}) n
                ON CONFLICT DO NOTHING
            """),
            params,
        )
        conn.execute(
            sa.text(f"""
                INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
                SELECT n.node, n.scope, TRUE FROM ({pairs}) n
                ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
            """),
            params,
        )
        conn.execute(
            sa.text(f"""
                INSERT INTO entity_membership_caps (membership_id, permission, all_fields)
                SELECT m.id, {_READ}, TRUE
                FROM ({pairs}) n
                JOIN entity_memberships m
                  ON m.virtual_entity_id = n.node AND m.member_entity_id = n.scope
                WHERE m.capped
                ON CONFLICT (membership_id, permission) DO UPDATE SET all_fields = TRUE
            """),
            params,
        )


def _add_rosters(conn: sa.Connection) -> None:
    conn.execute(_CAP_ROSTER_EDGES)
    conn.execute(_ADD_PERSONAL_ROSTER_EDGES)
    conn.execute(_ADD_ROSTER_CAPS)
    conn.execute(_DROP_PROJECT_BINDINGS_OF_USERS)


def _add_accepted_shares(conn: sa.Connection) -> None:
    conn.execute(_ADD_SHARE_EDGES)
    conn.execute(_ADD_SHARE_CAPS)


def _add_preset_roles(conn: sa.Connection) -> None:
    role_ids = [row.id for row in conn.execute(_ADD_PRESET_ROLES)]
    if role_ids:
        conn.execute(
            _ADD_ROLE_PERMISSIONS.bindparams(
                sa.bindparam("role_ids", role_ids, type_=sa.ARRAY(sa.Uuid))
            )
        )


def _grant_roles(conn: sa.Connection) -> None:
    conn.execute(_GRANT_USER_AND_DOMAIN_ROLES)
    conn.execute(_GRANT_PROJECT_ROLES)
    conn.execute(_GRANT_CREATOR_ROLES, {"preset_id": PROJECT_ADMIN_PRESET_ID})


def put_every_entity_in_the_graph(conn: sa.Connection) -> None:
    """Scope edges go in before shares and relations, which leave an own edge alone."""
    _add_nodes(conn, NODE_SOURCES)
    _add_preset_roles(conn)
    _add_nodes(conn, tuple(source for source in NODE_SOURCES if source[0] == "role"))
    conn.execute(_ADD_SELF_MEMBERSHIPS)
    conn.execute(_ADD_SELF_BINDINGS)
    _add_created_in_edges(conn)
    _add_rosters(conn)
    _add_relation_edges(conn)
    _add_accepted_shares(conn)
    conn.execute(_DROP_PATHS_OF_WHOLE_CAPS)
    _grant_roles(conn)


def upgrade() -> None:
    put_every_entity_in_the_graph(op.get_bind())


def downgrade() -> None:
    # Nothing is removed: a row this revision added cannot be told apart from one an
    # entity creation made.
    pass
