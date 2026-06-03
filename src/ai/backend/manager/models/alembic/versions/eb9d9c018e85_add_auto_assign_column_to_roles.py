"""add auto_assign column to roles

Revision ID: eb9d9c018e85
Revises: 1a2b3c4d5e6f
Create Date: 2026-06-02 19:03:39.764771

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "eb9d9c018e85"
down_revision = "1a2b3c4d5e6f"
# Part of: 26.6.0
branch_labels = None
depends_on = None

SYSTEM_ROLE_SOURCE = "system"


def upgrade() -> None:
    op.add_column(
        "roles",
        sa.Column(
            "auto_assign",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    # Backfill: system-sourced roles are auto-assigned when a user joins the
    # owning scope.
    op.execute(
        sa.text("UPDATE roles SET auto_assign = true WHERE source = :source").bindparams(
            source=SYSTEM_ROLE_SOURCE
        )
    )


def downgrade() -> None:
    op.drop_column("roles", "auto_assign")
