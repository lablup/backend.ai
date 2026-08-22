"""give keypairs an id

A keypair is a field of its user, and the v2 action layer names a field row by a
``FieldIdentifier``, which is a UUID. The table keys on ``access_key``, a
caller-facing string, so it had no id to be named by.

``id`` is added as a unique alternate key; ``access_key`` stays the primary key,
so every existing query, index and foreign key is untouched. Existing rows are
backfilled by the column default, so the column is NOT NULL from the start.

Revision ID: c8e2a5f10d47
Revises: b3d7f1c05a94
Create Date: 2026-08-19 04:35:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "c8e2a5f10d47"
down_revision = "b3d7f1c05a94"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "keypairs",
        sa.Column(
            "id",
            GUID,
            nullable=False,
            unique=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
    )


def downgrade() -> None:
    op.drop_column("keypairs", "id")
