"""add_fair_share_spec_to_scaling_groups

Revision ID: 5bbce2f389e4
Revises: 81f2dd702d93
Create Date: 2026-01-19 14:53:27.942594

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "5bbce2f389e4"
down_revision = "81f2dd702d93"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "scaling_groups",
        sa.Column("fair_share_spec", postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("scaling_groups", "fair_share_spec")
