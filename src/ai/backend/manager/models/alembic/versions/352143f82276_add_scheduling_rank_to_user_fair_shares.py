"""add_scheduling_rank_to_user_fair_shares

Revision ID: 352143f82276
Revises: 5bbce2f389e4
Create Date: 2026-01-20 10:29:05.603026

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '352143f82276'
down_revision = '5bbce2f389e4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_fair_shares",
        sa.Column(
            "scheduling_rank",
            sa.Integer(),
            nullable=True,
            comment="Computed scheduling priority rank. "
            "Lower value = higher priority (1 = highest). "
            "NULL means rank calculation has not been performed yet.",
        ),
    )


def downgrade() -> None:
    op.drop_column("user_fair_shares", "scheduling_rank")
