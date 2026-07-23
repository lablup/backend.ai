"""add initial grace period to idle checkers

Revision ID: 39fadbbea696
Revises: b3e8f1a24c76
Create Date: 2026-07-23 15:48:21.310221

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "39fadbbea696"
down_revision = "b3e8f1a24c76"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "idle_checkers",
        sa.Column(
            "initial_grace_period_seconds",
            sa.Integer(),
            nullable=True,
        ),
    )
    op.execute(
        sa.text(
            """
            UPDATE idle_checkers
            SET initial_grace_period_seconds = 0
            """
        )
    )
    op.alter_column(
        "idle_checkers",
        "initial_grace_period_seconds",
        nullable=False,
    )
    op.create_check_constraint(
        "initial_grace_period_seconds_non_negative",
        "idle_checkers",
        "initial_grace_period_seconds >= 0",
    )


def downgrade() -> None:
    op.drop_constraint("initial_grace_period_seconds_non_negative", "idle_checkers", type_="check")
    op.drop_column("idle_checkers", "initial_grace_period_seconds")
