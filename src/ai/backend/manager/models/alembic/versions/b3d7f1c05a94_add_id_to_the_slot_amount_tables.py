"""give every per-slot amount table an id

Five tables record one slot's amount for one owner and key on the pair
``(owner, slot_name)``. A row that another entity owns is a field row, and the v2
action layer names a field row by a ``FieldIdentifier``, which is a UUID — a
composite key cannot serve as one.

``id`` is added as a unique alternate key; the composite primary key stays where
it is, so every existing query and index is untouched. Existing rows are
backfilled by the column default, so the column is NOT NULL from the start.

Revision ID: b3d7f1c05a94
Revises: 9c1d4a7b62e0
Create Date: 2026-08-18 12:50:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "b3d7f1c05a94"
down_revision = "9c1d4a7b62e0"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_TABLES = (
    "agent_resources",
    "resource_allocations",
    "model_card_resource_requirements",
    "preset_resource_slots",
    "deployment_revision_resource_slots",
)


def upgrade() -> None:
    for table in _TABLES:
        op.add_column(
            table,
            sa.Column(
                "id",
                GUID,
                nullable=False,
                unique=True,
                server_default=sa.text("uuid_generate_v4()"),
            ),
        )


def downgrade() -> None:
    for table in _TABLES:
        op.drop_column(table, "id")
