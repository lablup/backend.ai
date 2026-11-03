"""Put auto-generated files in the graph

An auto-generated file becomes an entity. Give each file a node owning and governing
itself, owned and governed by the entity its row names, and grant the role presets their
permissions on the new type. Write the grants to the presets and to every role made from
them.

Revision ID: 592dedb4a39c
Revises: ece8800e945c
Create Date: 2026-11-03

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.cli.role_fixture import _identify

# revision identifiers, used by Alembic.
revision = "592dedb4a39c"  # Part of: NEXT_RELEASE_VERSION
down_revision = "ece8800e945c"
branch_labels = None
depends_on = None


_USER_OWNER_PRESET_ID: Final[str] = "776c1366-dcf3-5abd-b8de-bc3ad3b759ad"
_DOMAIN_ADMIN_PRESET_ID: Final[str] = "9ebf4f57-9e67-5631-997a-d2d79cc3815f"
_PROJECT_MEMBER_PRESET_ID: Final[str] = "06057849-3534-546f-b74c-b79d5d3ecf5e"
_PROJECT_ADMIN_PRESET_ID: Final[str] = "22c4db03-24aa-5ff8-b5a9-64b2a2182413"
_ENTITY_TYPE: Final[str] = "auto_generated_file"
_READ: Final[int] = int(Permission.READ)
_EVERY_OPERATION: Final[tuple[int, ...]] = tuple(int(bit) for bit in Permission.full())

# (preset id, entity type, permission bit) each grant is written for.
_GRANTS: Final[tuple[tuple[str, str, int], ...]] = (
    (_PROJECT_MEMBER_PRESET_ID, _ENTITY_TYPE, _READ),
    *((_USER_OWNER_PRESET_ID, _ENTITY_TYPE, bit) for bit in _EVERY_OPERATION),
    *((_DOMAIN_ADMIN_PRESET_ID, _ENTITY_TYPE, bit) for bit in _EVERY_OPERATION),
    *((_PROJECT_ADMIN_PRESET_ID, _ENTITY_TYPE, bit) for bit in _EVERY_OPERATION),
)
_GRANT_ROWS: Final[list[str]] = []
_GRANT_PARAMS: Final[dict[str, str | int]] = {}

for i, (preset_id, entity_type, permission) in enumerate(_GRANTS):
    _GRANT_ROWS.append(
        f"(CAST(:id_{i} AS uuid), CAST(:preset_id_{i} AS uuid), "
        f":entity_type_{i}, CAST(:permission_{i} AS integer))"
    )
    _GRANT_PARAMS.update({
        f"id_{i}": _identify("role_permission_preset", preset_id, entity_type, str(permission)),
        f"preset_id_{i}": preset_id,
        f"entity_type_{i}": entity_type,
        f"permission_{i}": permission,
    })

_GRANT_VALUES: Final[str] = ", ".join(_GRANT_ROWS)


def upgrade() -> None:
    conn = op.get_bind()
    # Create a virtual entity node for each existing auto-generated file.
    conn.execute(
        sa.text(f"""
            INSERT INTO virtual_entities (entity_type, entity_id)
            SELECT '{_ENTITY_TYPE}', id FROM auto_generated_files
            ON CONFLICT (entity_type, entity_id) DO NOTHING
        """)
    )
    # Add an uncapped ownership edge from each file node to itself.
    conn.execute(
        sa.text(f"""
            INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
            SELECT id, id, FALSE FROM virtual_entities
            WHERE entity_type = '{_ENTITY_TYPE}'
            ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
        """)
    )
    # Bind each file node to its own scope without a permission cap.
    conn.execute(
        sa.text(f"""
            INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
            SELECT id, id, NULL FROM virtual_entities
            WHERE entity_type = '{_ENTITY_TYPE}'
            ON CONFLICT DO NOTHING
        """)
    )
    file_and_owner_nodes = f"""
        SELECT file_node.id AS file_node, owner_node.id AS owner_node
        FROM auto_generated_files f
        JOIN virtual_entities file_node
          ON file_node.entity_type = '{_ENTITY_TYPE}' AND file_node.entity_id = f.id
        JOIN virtual_entities owner_node
          ON owner_node.entity_type = f.entity_type AND owner_node.entity_id = f.entity_id
    """
    # Add an uncapped ownership edge from each owner node to its file node.
    conn.execute(
        sa.text(f"""
            INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
            SELECT n.owner_node, n.file_node, FALSE FROM ({file_and_owner_nodes}) n
            ON CONFLICT (virtual_entity_id, member_entity_id) DO UPDATE SET capped = FALSE
        """)
    )
    # Bind each file node to its owner scope without a permission cap.
    conn.execute(
        sa.text(f"""
            INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
            SELECT n.file_node, n.owner_node, NULL FROM ({file_and_owner_nodes}) n
            ON CONFLICT DO NOTHING
        """)
    )
    # Add the permissions to the presets for roles created in the future.
    conn.execute(
        sa.text(f"""
            WITH grants(id, preset_id, entity_type, permission) AS (VALUES {_GRANT_VALUES})
            INSERT INTO role_permission_presets (id, role_preset_id, entity_type, permission)
            SELECT g.id, p.id, g.entity_type, g.permission
            FROM grants g
            JOIN role_presets p ON p.id = g.preset_id
            ON CONFLICT DO NOTHING
        """).bindparams(**_GRANT_PARAMS)
    )
    # Add the same permissions to existing roles created from the presets.
    conn.execute(
        sa.text(f"""
            WITH grants(id, preset_id, entity_type, permission) AS (VALUES {_GRANT_VALUES})
            INSERT INTO permissions (role_id, entity_type, permission)
            SELECT r.id, g.entity_type, g.permission
            FROM grants g
            JOIN roles r ON r.role_preset_id = g.preset_id
            ON CONFLICT (role_id, entity_type, permission) DO NOTHING
        """).bindparams(**_GRANT_PARAMS)
    )


def downgrade() -> None:
    conn = op.get_bind()
    # Remove the permissions from existing roles created from the presets.
    conn.execute(
        sa.text(f"""
            WITH grants(id, preset_id, entity_type, permission) AS (VALUES {_GRANT_VALUES})
            DELETE FROM permissions p
            USING roles r, grants g
            WHERE p.role_id = r.id AND r.role_preset_id = g.preset_id
              AND p.entity_type = g.entity_type AND p.permission = g.permission
        """).bindparams(**_GRANT_PARAMS)
    )
    # Remove the permissions from the presets for roles created in the future.
    conn.execute(
        sa.text(f"""
            WITH grants(id, preset_id, entity_type, permission) AS (VALUES {_GRANT_VALUES})
            DELETE FROM role_permission_presets p
            USING grants g
            WHERE p.role_preset_id = g.preset_id
              AND p.entity_type = g.entity_type AND p.permission = g.permission
        """).bindparams(**_GRANT_PARAMS)
    )
    # Remove file nodes and cascade removal to their graph edges.
    conn.execute(
        sa.text("DELETE FROM virtual_entities WHERE entity_type = :entity_type").bindparams(
            entity_type=_ENTITY_TYPE
        )
    )
