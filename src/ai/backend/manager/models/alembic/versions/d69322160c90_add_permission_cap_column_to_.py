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


def downgrade() -> None:
    op.drop_column("association_scopes_entities", "permission_cap")
