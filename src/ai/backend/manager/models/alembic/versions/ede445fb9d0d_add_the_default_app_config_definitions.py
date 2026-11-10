"""Add the default app config definitions

Write the definitions and allow-list entries `seeds/manager/app_config_definition/` and
`seeds/manager/app_config_allow_list/` declare, each created in the `global` scope. A
config name or `(config_name, scope_type)` already registered is left as it stands.

Revision ID: ede445fb9d0d
Revises: d6e297fca9ae
Create Date: 2026-10-13

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "ede445fb9d0d"  # Part of: NEXT_RELEASE_VERSION
down_revision = "d6e297fca9ae"
branch_labels = None
depends_on = None

# Fixed ids mark the rows this revision wrote, so the downgrade removes only those.
DEFINITIONS: Final[dict[str, str]] = {
    "userConfig": "50ea3cb2-7ee3-422d-a7bc-f18ff0fee73b",
    "domainConfig": "a2aceaa0-09ff-43f3-b7f6-2a65b3f4aab5",
    "publicConfigByDomain": "1e388833-096b-4f2b-9818-56a342f8ed75",
}

# (config_name, scope_type, rank) to id.
ALLOW_LIST: Final[dict[tuple[str, str, int], str]] = {
    ("userConfig", "domain", 200): "e4b02b1c-5881-4a2b-9c0b-c7bc3efd0e80",
    ("userConfig", "user", 300): "35a638e8-9bae-45aa-81be-2e4a809357db",
    ("domainConfig", "domain", 200): "ede1dfb6-432b-4f0a-8754-c8a02281d2ee",
    ("publicConfigByDomain", "public", 100): "7da2f1ee-640f-4e4a-aed0-e0674f4b3293",
}

_GLOBAL_NODE: Final[str] = """
    SELECT ve.id FROM virtual_entities ve
    JOIN global_entities ge ON ve.entity_type = 'global' AND ve.entity_id = ge.id
    WHERE ge.name = 'global'
"""

_NODES: Final[str] = """
    SELECT ve.id FROM virtual_entities ve
    WHERE ve.entity_type = :entity_type
      AND ve.entity_id = ANY(CAST(:entity_ids AS uuid[]))
"""

_ADD_DEFINITION: Final = sa.text("""
    INSERT INTO app_config_definitions (id, config_name)
    VALUES (CAST(:id AS uuid), :config_name)
    ON CONFLICT (config_name) DO NOTHING
""")

_ADD_ALLOW_LIST: Final = sa.text("""
    INSERT INTO app_config_allow_list (id, config_name, scope_type, rank)
    VALUES (CAST(:id AS uuid), :config_name, :scope_type, :rank)
    ON CONFLICT (config_name, scope_type) DO NOTHING
""")

# Each row's own node, owning and governing itself, as the runtime provisions it.
_ADD_NODES: Final[str] = """
    INSERT INTO virtual_entities (entity_type, entity_id)
    SELECT :entity_type, t.id FROM {table} t
    WHERE t.id = ANY(CAST(:entity_ids AS uuid[]))
    ON CONFLICT (entity_type, entity_id) DO NOTHING
"""

_ADD_SELF_MEMBERSHIPS: Final = sa.text(f"""
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT n.id, n.id, FALSE FROM ({_NODES}) n
    ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
""")

_ADD_SELF_BINDINGS: Final = sa.text(f"""
    INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
    SELECT n.id, n.id, NULL FROM ({_NODES}) n
    ON CONFLICT DO NOTHING
""")

_ADD_GLOBAL_MEMBERSHIPS: Final = sa.text(f"""
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT g.id, n.id, FALSE FROM ({_GLOBAL_NODE}) g, ({_NODES}) n
    ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
""")

_ADD_GLOBAL_BINDINGS: Final = sa.text(f"""
    INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
    SELECT n.id, g.id, NULL FROM ({_GLOBAL_NODE}) g, ({_NODES}) n
    ON CONFLICT DO NOTHING
""")

# A row of this revision something else now refers to stays: deleting it would cascade.
_REMOVE_ALLOW_LIST: Final = sa.text("""
    DELETE FROM app_config_allow_list a
    WHERE a.id = ANY(CAST(:ids AS uuid[]))
      AND NOT EXISTS (
          SELECT 1 FROM app_config_fragments f
          WHERE f.config_name = a.config_name AND f.scope_type = a.scope_type
      )
    RETURNING a.id
""")

_REMOVE_DEFINITIONS: Final = sa.text("""
    DELETE FROM app_config_definitions d
    WHERE d.id = ANY(CAST(:ids AS uuid[]))
      AND NOT EXISTS (SELECT 1 FROM app_config_allow_list a WHERE a.config_name = d.config_name)
    RETURNING d.id
""")

# The edges naming a node go with it by FK.
_REMOVE_NODES: Final = sa.text("""
    DELETE FROM virtual_entities
    WHERE entity_type = :entity_type AND entity_id = ANY(CAST(:entity_ids AS uuid[]))
""")


def _add_to_graph(conn: Connection, table: str, entity_type: str, ids: list[str]) -> None:
    params = {"entity_type": entity_type, "entity_ids": ids}
    conn.execute(sa.text(_ADD_NODES.format(table=table)), params)
    for statement in (
        _ADD_SELF_MEMBERSHIPS,
        _ADD_SELF_BINDINGS,
        _ADD_GLOBAL_MEMBERSHIPS,
        _ADD_GLOBAL_BINDINGS,
    ):
        conn.execute(statement, params)


def add_defaults(conn: Connection) -> None:
    for config_name, definition_id in DEFINITIONS.items():
        conn.execute(_ADD_DEFINITION, {"id": definition_id, "config_name": config_name})
    for (config_name, scope_type, rank), entry_id in ALLOW_LIST.items():
        conn.execute(
            _ADD_ALLOW_LIST,
            {"id": entry_id, "config_name": config_name, "scope_type": scope_type, "rank": rank},
        )
    _add_to_graph(
        conn, "app_config_definitions", "app_config_definition", list(DEFINITIONS.values())
    )
    _add_to_graph(conn, "app_config_allow_list", "app_config_allow_list", list(ALLOW_LIST.values()))


def remove_defaults(conn: Connection) -> None:
    entries = conn.scalars(_REMOVE_ALLOW_LIST, {"ids": list(ALLOW_LIST.values())}).all()
    conn.execute(
        _REMOVE_NODES,
        {"entity_type": "app_config_allow_list", "entity_ids": [str(e) for e in entries]},
    )
    definitions = conn.scalars(_REMOVE_DEFINITIONS, {"ids": list(DEFINITIONS.values())}).all()
    conn.execute(
        _REMOVE_NODES,
        {"entity_type": "app_config_definition", "entity_ids": [str(d) for d in definitions]},
    )


def upgrade() -> None:
    add_defaults(op.get_bind())


def downgrade() -> None:
    remove_defaults(op.get_bind())
