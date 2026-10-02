"""Add the missing tt-n300.device resource slot type

The Tenstorrent n300 plugin reports ``tt-n300.device``, but the slot type was never
seeded. ``agent_resources.slot_name`` has a hard FK onto ``resource_slot_types.slot_name``
and the heartbeat path does not register slot types, so a Tenstorrent agent's
heartbeat fails on that FK until this row exists.

This revision is a schema fix only, kept apart from the Neuron feature revision
(``a1c7e4b93f20``) so it can be backported on its own. The insert is idempotent.

The uuid is pinned to the one ``fixtures/manager/example-resource-slot-types.json``
assigns, following ``8f21c46a0b73``, so an upgraded deployment gets the same slot
identity a fresh install gets.

Revision ID: d0a201e9be45
Revises: a91c4e7d0b35
Create Date: 2026-09-25

"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "d0a201e9be45"
down_revision = "a91c4e7d0b35"
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
             'n300',   'npu_generic', '{"binary":false,"round_length":0}', 1500)
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
