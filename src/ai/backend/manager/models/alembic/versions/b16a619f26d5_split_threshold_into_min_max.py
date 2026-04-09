"""split threshold+comparator into min_threshold+max_threshold

Revision ID: b16a619f26d5
Revises: f2a3b4c5d6e7
Create Date: 2026-04-05

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b16a619f26d5"
down_revision = "f2a3b4c5d6e7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "endpoint_auto_scaling_rules",
        sa.Column("min_threshold", sa.Text(), nullable=True),
    )
    op.add_column(
        "endpoint_auto_scaling_rules",
        sa.Column("max_threshold", sa.Text(), nullable=True),
    )

    # Migrate existing data based on comparator value
    op.execute(
        sa.text("""
            UPDATE endpoint_auto_scaling_rules
            SET max_threshold = threshold
            WHERE comparator IN ('GREATER_THAN', 'GREATER_THAN_OR_EQUAL')
        """)
    )
    op.execute(
        sa.text("""
            UPDATE endpoint_auto_scaling_rules
            SET min_threshold = threshold
            WHERE comparator IN ('LESS_THAN', 'LESS_THAN_OR_EQUAL')
        """)
    )

    op.drop_column("endpoint_auto_scaling_rules", "threshold")
    op.drop_column("endpoint_auto_scaling_rules", "comparator")


def downgrade() -> None:
    op.add_column(
        "endpoint_auto_scaling_rules",
        sa.Column("threshold", sa.Text(), nullable=True),
    )
    op.add_column(
        "endpoint_auto_scaling_rules",
        sa.Column("comparator", sa.VARCHAR(64), nullable=True),
    )

    # Reverse migration: max_threshold → GREATER_THAN, min_threshold → LESS_THAN
    op.execute(
        sa.text("""
            UPDATE endpoint_auto_scaling_rules
            SET threshold = max_threshold, comparator = 'GREATER_THAN'
            WHERE max_threshold IS NOT NULL
        """)
    )
    op.execute(
        sa.text("""
            UPDATE endpoint_auto_scaling_rules
            SET threshold = min_threshold, comparator = 'LESS_THAN'
            WHERE min_threshold IS NOT NULL AND threshold IS NULL
        """)
    )
    # Default for rows with no thresholds
    op.execute(
        sa.text("""
            UPDATE endpoint_auto_scaling_rules
            SET threshold = '0', comparator = 'GREATER_THAN'
            WHERE threshold IS NULL
        """)
    )

    op.alter_column("endpoint_auto_scaling_rules", "threshold", nullable=False)
    op.alter_column("endpoint_auto_scaling_rules", "comparator", nullable=False)

    op.drop_column("endpoint_auto_scaling_rules", "min_threshold")
    op.drop_column("endpoint_auto_scaling_rules", "max_threshold")
