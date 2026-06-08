"""add permission cap column to association_scopes_entities

Revision ID: d69322160c90
Revises: 7af18070fdef
Create Date: 2026-06-05 17:29:24.968100

"""

import sqlalchemy as sa
from alembic import op

# Part of: 26.6.0

# revision identifiers, used by Alembic.
revision = "d69322160c90"
down_revision = "7af18070fdef"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add the permission cap column (Permission IntFlag bitmask stored as SMALLINT).
    # The column is nullable with no default; a NULL cap means "no ceiling" and is
    # treated as the full cap during resolution, so existing rows need no backfill.
    op.add_column(
        "association_scopes_entities",
        sa.Column(
            "permission_cap",
            sa.SmallInteger(),
            nullable=True,
        ),
    )
    # Backfill from relation_type: REF edges map to a read-only cap (1 = READ)
    op.execute(
        "UPDATE association_scopes_entities SET permission_cap = 1 WHERE relation_type = 'ref'"
    )


def downgrade() -> None:
    op.drop_column("association_scopes_entities", "permission_cap")
