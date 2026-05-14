"""add ``id`` UUID column to ``domains``

Adds a UUID ``id`` column to the ``domains`` table as a UNIQUE alternate
key. The existing ``name`` column remains the primary key in this
migration; the PK swap is deferred to the FK migration step so it can
land atomically with the FK column transition (``domain_name`` →
``domain_id``).

Revision ID: a1c3e5d7b9f2
Revises: b2c3d4e5f6a7
Create Date: 2026-05-15

"""

# Part of: 26.5.0

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "a1c3e5d7b9f2"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "domains",
        sa.Column(
            "id",
            GUID(),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
    )
    op.create_unique_constraint("uq_domains_id", "domains", ["id"])


def downgrade() -> None:
    op.drop_constraint("uq_domains_id", "domains", type_="unique")
    op.drop_column("domains", "id")
