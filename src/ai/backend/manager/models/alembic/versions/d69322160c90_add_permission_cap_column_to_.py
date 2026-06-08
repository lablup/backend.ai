"""add permission cap column to association_scopes_entities

Revision ID: d69322160c90
Revises: ed42bc179b91
Create Date: 2026-06-05 17:29:24.968100

"""

import sqlalchemy as sa
from alembic import op

# Part of: 26.6.0

# revision identifiers, used by Alembic.
revision = "d69322160c90"
down_revision = "ed42bc179b91"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add the permission cap column (Permission IntFlag bitmask stored as SMALLINT).
    # The NOT NULL column is created with the full-cap (31 = READ|UPDATE|SOFT_DELETE|
    # CREATE|HARD_DELETE) server default so existing rows (and any rows created before
    # write paths populate the cap) are backfilled to the full cap, matching the AUTO
    # relation default.
    op.add_column(
        "association_scopes_entities",
        sa.Column(
            "permission_cap",
            sa.SmallInteger(),
            server_default=sa.text("31"),
            nullable=False,
        ),
    )
    # Backfill from relation_type: REF edges map to a read-only cap (1 = READ); AUTO
    # edges already carry the full-cap (31) default applied above.
    op.execute(
        "UPDATE association_scopes_entities SET permission_cap = 1 WHERE relation_type = 'ref'"
    )


def downgrade() -> None:
    op.drop_column("association_scopes_entities", "permission_cap")
