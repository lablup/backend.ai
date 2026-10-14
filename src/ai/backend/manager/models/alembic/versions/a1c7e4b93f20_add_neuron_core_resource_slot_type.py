"""Add the neuron.core resource slot type

Adds the ``neuron.core`` slot type for the AWS Neuron accelerator plugin.

``agent_resources.slot_name`` has a hard FK onto ``resource_slot_types.slot_name`` and
the manager upserts one ``agent_resources`` row per reported slot on every heartbeat,
but the heartbeat path does not register slot types. ``resource_slot_to_quantities``
preserves zero-valued slots, so a host without Neuron hardware still reports
``neuron.core: 0``; without this row, every agent carrying the plugin fails its
heartbeat on the FK.

The uuid is pinned to the one ``fixtures/manager/example-resource-slot-types.json``
assigns, following ``8f21c46a0b73``, so an upgraded deployment gets the same slot
identity a fresh install gets.

Revision ID: a1c7e4b93f20
Revises: d0a201e9be45
Create Date: 2026-09-12

"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "a1c7e4b93f20"
down_revision = "d0a201e9be45"
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
    # simply never looks the row up.  Removing it is an operator decision.
    pass
