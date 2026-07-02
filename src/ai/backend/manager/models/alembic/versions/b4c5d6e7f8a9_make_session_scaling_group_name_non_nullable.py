"""make session scaling_group_name non-nullable

Revision ID: b4c5d6e7f8a9
Revises: e3b8d2a1c5f7
Create Date: 2026-07-01

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b4c5d6e7f8a9"
down_revision = "e3b8d2a1c5f7"
# Part of: 26.7.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text("""
        WITH session_scaling_groups AS (
          SELECT DISTINCT kernels.session_id, kernels.scaling_group
          FROM kernels
          WHERE kernels.scaling_group IS NOT NULL
            AND NOT EXISTS (
              SELECT 1
              FROM kernels AS other_kernels
              WHERE other_kernels.session_id = kernels.session_id
                AND other_kernels.scaling_group IS NOT NULL
                AND other_kernels.scaling_group <> kernels.scaling_group
            )
        )
        UPDATE sessions
        SET scaling_group_name = session_scaling_groups.scaling_group
        FROM session_scaling_groups
        WHERE sessions.id = session_scaling_groups.session_id
          AND sessions.scaling_group_name IS NULL
        """)
    )
    op.alter_column(
        "sessions",
        "scaling_group_name",
        existing_type=sa.String(length=64),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "sessions",
        "scaling_group_name",
        existing_type=sa.String(length=64),
        nullable=True,
    )
