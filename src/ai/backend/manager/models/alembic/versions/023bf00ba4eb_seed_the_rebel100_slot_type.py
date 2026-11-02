"""Seed the rebel100.device slot type

Write the `rebel100.device` row `fixtures/manager/example-resource-slot-types.json` and
`seeds/manager/resource_slot_type/defaults.yaml` declare, with its node in the `global`
scope. A row already registered under the slot name or the uuid is left as it stands.

Revision ID: 023bf00ba4eb
Revises: de3577e66bae
Create Date: 2026-11-02 12:00:00.000000

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "023bf00ba4eb"
down_revision = "de3577e66bae"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_SLOT_UUID: Final[str] = "e84dafba-8b90-49ad-94ac-2b0bdf45bfc3"

# The row is written outside the entity ops, so it gets the node they would have made:
# owning and governing itself, and created in the `global` scope.
_ADD_SLOT_TYPE: Final = sa.text(
    """
    INSERT INTO resource_slot_types
        (uuid, slot_name, slot_type, required, display_name, description,
         display_unit, display_icon, number_format, rank)
    VALUES
        (CAST(:uuid AS uuid), 'rebel100.device', 'count', false,
         'Rebel100 Device', 'Rebel100', 'Rebel100', 'rebel',
         '{"binary"\\:false,"round_length"\\:0}'::jsonb, 1600)
    ON CONFLICT DO NOTHING
    """
)

_GLOBAL_NODE: Final[str] = """
    SELECT ve.id FROM virtual_entities ve
    JOIN global_entities ge ON ve.entity_type = 'global' AND ve.entity_id = ge.id
    WHERE ge.name = 'global'
"""

_NODE: Final[str] = """
    SELECT ve.id FROM virtual_entities ve
    WHERE ve.entity_type = 'resource_slot_type' AND ve.entity_id = CAST(:uuid AS uuid)
"""

_ADD_NODE: Final = sa.text("""
    INSERT INTO virtual_entities (entity_type, entity_id)
    SELECT 'resource_slot_type', t.uuid FROM resource_slot_types t
    WHERE t.uuid = CAST(:uuid AS uuid)
    ON CONFLICT (entity_type, entity_id) DO NOTHING
""")

_ADD_SELF_MEMBERSHIP: Final = sa.text(f"""
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT n.id, n.id, FALSE FROM ({_NODE}) n
    ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
""")

_ADD_SELF_BINDING: Final = sa.text(f"""
    INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
    SELECT n.id, n.id, NULL FROM ({_NODE}) n
    ON CONFLICT DO NOTHING
""")

_ADD_GLOBAL_MEMBERSHIP: Final = sa.text(f"""
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT g.id, n.id, FALSE FROM ({_GLOBAL_NODE}) g, ({_NODE}) n
    ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
""")

_ADD_GLOBAL_BINDING: Final = sa.text(f"""
    INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
    SELECT n.id, g.id, NULL FROM ({_GLOBAL_NODE}) g, ({_NODE}) n
    ON CONFLICT DO NOTHING
""")


def upgrade() -> None:
    conn = op.get_bind()
    params = {"uuid": _SLOT_UUID}
    for statement in (
        _ADD_SLOT_TYPE,
        _ADD_NODE,
        _ADD_SELF_MEMBERSHIP,
        _ADD_SELF_BINDING,
        _ADD_GLOBAL_MEMBERSHIP,
        _ADD_GLOBAL_BINDING,
    ):
        conn.execute(statement, params)


def downgrade() -> None:
    # Agent resources and allocations may reference the row, so it stays.
    pass
