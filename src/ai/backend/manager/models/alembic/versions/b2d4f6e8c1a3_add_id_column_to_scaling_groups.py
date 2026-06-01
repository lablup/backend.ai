"""add ``id`` UUID column to ``scaling_groups``

Adds a UUID ``id`` column to the ``scaling_groups`` table as a UNIQUE
alternate key. The existing ``name`` column remains the primary key in
this migration; the PK swap is deferred to the FK migration step so it
can land atomically with the FK column transition (``scaling_group`` /
``resource_group`` → ``scaling_group_id``).

Revision ID: b2d4f6e8c1a3
Revises: a1c3e5d7b9f2
Create Date: 2026-05-15

"""

# Part of: 26.5.0

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "b2d4f6e8c1a3"
down_revision = "a1c3e5d7b9f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "scaling_groups",
        sa.Column(
            "id",
            GUID(),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
    )
    op.create_unique_constraint("uq_scaling_groups_id", "scaling_groups", ["id"])


def downgrade() -> None:
    op.drop_constraint("uq_scaling_groups_id", "scaling_groups", type_="unique")
    op.drop_column("scaling_groups", "id")
