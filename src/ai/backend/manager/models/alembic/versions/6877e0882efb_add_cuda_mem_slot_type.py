"""Register the cuda.mem slot type for fractional GPU memory allocation

Write the `cuda.mem` resource slot type created in the `global` and `public` scopes, as
`ResourceSlotTypeUpserter` provisions it. A `cuda.mem` already registered is left as it stands.

Revision ID: 6877e0882efb
Revises: 019493a701bd
Create Date: 2026-10-16

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "6877e0882efb"  # Part of: NEXT_RELEASE_VERSION
down_revision = "019493a701bd"
branch_labels = None
depends_on = None

# A fixed id marks the row this revision wrote, so the downgrade removes only that one.
SLOT_TYPE_ID: Final[str] = "ab149050-da4c-4e1c-b9d9-a3f7fe15b2e2"
ENTITY_TYPE: Final[str] = "resource_slot_type"
NUMBER_FORMAT: Final[str] = '{"binary": true, "round_length": 1}'

# Every table with a foreign key to `resource_slot_types.slot_name`.
_REFERENCING_TABLES: Final[tuple[str, ...]] = (
    "agent_resources",
    "resource_allocations",
    "model_card_resource_requirements",
    "preset_resource_slots",
    "deployment_revision_resource_slots",
    "kernel_group_resource_slots",
)

_ADD_SLOT_TYPE: Final = sa.text("""
    INSERT INTO resource_slot_types
        (uuid, slot_name, slot_type, display_name, description,
         display_unit, display_icon, number_format, rank)
    VALUES
        (CAST(:id AS uuid), 'cuda.mem', 'bytes', 'GPU Memory',
         'CUDA-capable GPU memory (fractional)', 'GiB', 'nvidia',
         CAST(:number_format AS jsonb), 450)
    ON CONFLICT (slot_name) DO NOTHING
""")

# The node of `cuda.mem`, whichever uuid its row carries.
_ADD_NODE: Final = sa.text("""
    INSERT INTO virtual_entities (entity_type, entity_id)
    SELECT :entity_type, uuid FROM resource_slot_types WHERE slot_name = 'cuda.mem'
    ON CONFLICT (entity_type, entity_id) DO NOTHING
""")

_NODE: Final[str] = """
    SELECT ve.id FROM virtual_entities ve
    JOIN resource_slot_types t ON ve.entity_type = :entity_type AND ve.entity_id = t.uuid
    WHERE t.slot_name = 'cuda.mem'
"""

# The node owns and governs itself, and each of `global` and `public` owns and governs it.
_SCOPES: Final[str] = f"""
    SELECT n.id FROM ({_NODE}) n
    UNION ALL
    SELECT ve.id FROM virtual_entities ve
    JOIN global_entities ge ON ve.entity_type = 'global' AND ve.entity_id = ge.id
    WHERE ge.name IN ('global', 'public')
"""

_ADD_MEMBERSHIPS: Final = sa.text(f"""
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT s.id, n.id, FALSE FROM ({_SCOPES}) s, ({_NODE}) n
    ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
""")

_ADD_BINDINGS: Final = sa.text(f"""
    INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
    SELECT n.id, s.id, NULL FROM ({_SCOPES}) s, ({_NODE}) n
    ON CONFLICT DO NOTHING
""")

# The row stays while anything refers to it: the foreign keys would reject the delete.
_REMOVE_SLOT_TYPE: Final = sa.text(
    """
    DELETE FROM resource_slot_types t
    WHERE t.uuid = CAST(:id AS uuid)
    """
    + "".join(
        f"  AND NOT EXISTS (SELECT 1 FROM {table} r WHERE r.slot_name = t.slot_name)\n"
        for table in _REFERENCING_TABLES
    )
    + "RETURNING t.uuid"
)

# The edges naming a node go with it by FK.
_REMOVE_NODE: Final = sa.text("""
    DELETE FROM virtual_entities
    WHERE entity_type = :entity_type AND entity_id = CAST(:id AS uuid)
""")


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(_ADD_SLOT_TYPE, {"id": SLOT_TYPE_ID, "number_format": NUMBER_FORMAT})
    params = {"entity_type": ENTITY_TYPE}
    for statement in (_ADD_NODE, _ADD_MEMBERSHIPS, _ADD_BINDINGS):
        conn.execute(statement, params)


def downgrade() -> None:
    conn = op.get_bind()
    removed = conn.scalars(_REMOVE_SLOT_TYPE, {"id": SLOT_TYPE_ID}).all()
    if removed:
        conn.execute(_REMOVE_NODE, {"entity_type": ENTITY_TYPE, "id": SLOT_TYPE_ID})
