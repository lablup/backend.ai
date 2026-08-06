"""add uuid column to resource_slot_types table

Revision ID: 8f21c46a0b73
Revises: c04f8b1a6e37
Create Date: 2026-08-06 10:12:44.813022

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "8f21c46a0b73"
down_revision = "c04f8b1a6e37"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

# The uuids ``fixtures/manager/example-resource-slot-types.json`` assigns to the
# slots it seeds. Pinned here as well so an upgraded deployment ends up with the
# same identity a fresh install gets, instead of a random one per database.
# Any slot outside this list — one the seeding migration derived from an agent's
# reported keys — keeps the generated default.
_SEEDED_SLOT_UUIDS = [
    ("cpu", "eff6619c-a85c-40f4-ae59-608b0f683b4f"),
    ("mem", "9d1a589e-2a78-491e-97d0-32d2a0079564"),
    ("cuda.device", "12fb9a43-2abb-403f-ae78-f04287f0223e"),
    ("cuda.shares", "6d6e386d-fecd-424b-b651-6c60bca59ab1"),
    ("rocm.device", "3759b036-ba21-4c54-90d3-0834aa7e5753"),
    ("tpu.device", "d8f5ef16-9977-4c9f-9117-99abb23ffc3d"),
    ("ipu.device", "0898aff8-166b-4e43-8967-b3fb9d419f4a"),
    ("atom.device", "572eb443-ad2f-4269-9aa0-89a3c219c4e1"),
    ("atom-plus.device", "1d56735e-583f-4e43-b7f8-4409e9c60b56"),
    ("atom-max.device", "1c7add00-830d-426d-94e8-aad96ad1d42c"),
    ("gaudi2.device", "a7aafaaa-dc67-45c9-813f-5d2ed7961aef"),
    ("warboy.device", "feabbb54-3f27-4ed3-ba53-495fc32a53c9"),
    ("rngd.device", "c0a50265-9d5c-4cad-9082-42ef751e5db0"),
    ("hyperaccel-lpu.device", "d788d8b6-f27b-4639-91b9-1337705b55b7"),
]


def upgrade() -> None:
    op.add_column(
        "resource_slot_types",
        sa.Column(
            "uuid",
            GUID(),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
    )
    values = ", ".join(f"('{name}', '{value}'::uuid)" for name, value in _SEEDED_SLOT_UUIDS)
    op.execute(
        sa.text(f"""
            UPDATE resource_slot_types AS t
            SET uuid = v.uuid
            FROM (VALUES {values}) AS v(slot_name, uuid)
            WHERE t.slot_name = v.slot_name
        """)
    )
    op.create_unique_constraint("uq_resource_slot_types_uuid", "resource_slot_types", ["uuid"])


def downgrade() -> None:
    op.drop_constraint("uq_resource_slot_types_uuid", "resource_slot_types", type_="unique")
    op.drop_column("resource_slot_types", "uuid")
