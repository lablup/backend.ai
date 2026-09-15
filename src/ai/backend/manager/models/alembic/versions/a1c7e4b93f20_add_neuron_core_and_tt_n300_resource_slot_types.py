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

``downgrade`` deliberately leaves both rows in place; see the comment there.

Create Date: 2026-09-12

"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "a1c7e4b93f20"
down_revision = "c58b0d3a9e14"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


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
    # Intentionally a no-op: five tables carry an FK onto `resource_slot_types.slot_name`,
    # so deleting a seeded row is destructive rather than reversible.  An older manager
    # simply never looks the rows up.  Removing them is an operator decision.
    pass
