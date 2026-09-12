"""Add the neuron.core and tt-n300.device resource slot types

Adds the ``neuron.core`` slot type for the AWS Neuron accelerator plugin.

``agent_resources.slot_name`` has a hard FK to ``resource_slot_types.slot_name``
(``fk_agent_resources_slot_name_resource_slot_types``) and the manager upserts one
``agent_resources`` row per reported slot on *every* agent heartbeat, with no
runtime insert path into ``resource_slot_types``. A slot type that is not seeded
here therefore makes the heartbeat of an agent reporting it fail on the FK.

Also adds the missing ``tt-n300.device`` row as a drive-by fix: the Tenstorrent
n300 plugin has reported that slot since it was added, but it was never seeded,
so a Tenstorrent agent hits the same FK violation today.

The uuids are pinned to the ones ``fixtures/manager/example-resource-slot-types.json``
assigns, following ``8f21c46a0b73``, so an upgraded deployment ends up with the
same slot identity a fresh install gets instead of a random one per database.

Create Date: 2026-09-12

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1c7e4b93f20"
down_revision = "c58b0d3a9e14"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_added_slot_names = (
    "tt-n300.device",
    "neuron.core",
)

# Every table that carries an FK onto `resource_slot_types.slot_name` as of this
# revision.  A slot still referenced from any of them cannot be deleted, so the
# downgrade has to skip it rather than abort the whole migration.
_referencing_tables = (
    "agent_resources",
    "resource_allocations",
    "model_card_resource_requirements",
    "preset_resource_slots",
    "deployment_revision_resource_slots",
)


def upgrade() -> None:
    # Use exec_driver_sql to avoid sa.text() parsing the JSON colons as bind params.
    # `required` and `enabled` keep their server defaults (false / true), matching
    # every other accelerator slot row.
    conn = op.get_bind()
    conn.exec_driver_sql("""
        INSERT INTO resource_slot_types
            (uuid, slot_name, slot_type, display_name, description,
             display_unit, display_icon, number_format, rank)
        VALUES
            ('ef63fa11-609e-4b96-8f90-a08f97a5f04b'::uuid,
             'tt-n300.device','count','Tenstorrent n300 Device','Tenstorrent n300',
             'n300',   'npu_generic', '{"binary":false,"round_length":0}', 1500),
            ('7b968b58-f7cc-472d-b191-d4b19f417efd'::uuid,
             'neuron.core','count','AWS Neuron Core','AWS Neuron NeuronCore',
             'Core',   'aws',         '{"binary":false,"round_length":0}', 1600)
        ON CONFLICT (slot_name) DO UPDATE SET
            slot_type     = EXCLUDED.slot_type,
            display_name  = EXCLUDED.display_name,
            description   = EXCLUDED.description,
            display_unit  = EXCLUDED.display_unit,
            display_icon  = EXCLUDED.display_icon,
            number_format = EXCLUDED.number_format,
            rank          = EXCLUDED.rank
    """)


def downgrade() -> None:
    # Only remove rows that nothing references.  Five tables carry an FK on
    # slot_name, so an unconditional delete would abort the downgrade on any
    # deployment that still has a live Neuron/Tenstorrent agent, a historical
    # allocation, or a model card / preset / deployment revision naming the slot.
    guards = "\n".join(
        f"              AND NOT EXISTS ("
        f"SELECT 1 FROM {table} r WHERE r.slot_name = resource_slot_types.slot_name)"
        for table in _referencing_tables
    )
    conn = op.get_bind()
    conn.execute(
        sa.text(f"""
            DELETE FROM resource_slot_types
            WHERE slot_name = ANY(:names)
{guards}
        """),
        {"names": list(_added_slot_names)},
    )
