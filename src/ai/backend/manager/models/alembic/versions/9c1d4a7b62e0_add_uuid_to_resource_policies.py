"""give the three resource policies a uuid identity

The policies key on ``name``, which is what ``keypairs`` / ``users`` / ``groups``
reference, so the primary key stays where it is. What they lacked is an
``EntityID``: the v2 action layer identifies every entity by a UUID, and a name
cannot serve as one. ``uuid`` is added as a unique alternate key alongside the
name, the same shape ``resource_slot_types`` already carries.

Existing rows are backfilled by the column default, so the column is NOT NULL
from the start and no reader handles a missing id.

Revision ID: 9c1d4a7b62e0
Revises: f1a7c3e9b482
Create Date: 2026-08-10 06:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "9c1d4a7b62e0"
down_revision = "f1a7c3e9b482"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_TABLES = (
    "keypair_resource_policies",
    "user_resource_policies",
    "project_resource_policies",
)


def upgrade() -> None:
    for table in _TABLES:
        op.add_column(
            table,
            sa.Column(
                "uuid",
                GUID,
                nullable=False,
                unique=True,
                server_default=sa.text("uuid_generate_v4()"),
            ),
        )


def downgrade() -> None:
    for table in _TABLES:
        op.drop_column(table, "uuid")
