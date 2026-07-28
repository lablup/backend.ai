"""derive idle checker type from spec

Revision ID: 71cb16a7a9c5
Revises: 8f3c1d5a2b47
Create Date: 2026-07-28

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "71cb16a7a9c5"
down_revision = "8f3c1d5a2b47"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("idle_checkers", "checker_type")
    op.add_column(
        "idle_checkers",
        sa.Column(
            "checker_type",
            sa.String(length=64),
            sa.Computed("spec ->> 'type'", persisted=True),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("idle_checkers", "checker_type")
    op.add_column(
        "idle_checkers",
        sa.Column("checker_type", sa.String(length=64), nullable=True),
    )
    op.execute(sa.text("UPDATE idle_checkers SET checker_type = spec ->> 'type'"))
    op.alter_column(
        "idle_checkers",
        "checker_type",
        existing_type=sa.String(length=64),
        nullable=False,
    )
