"""add last_used_at to images

Revision ID: cf3290640ea8
Revises: 3549e469dfee
Create Date: 2026-03-23 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "cf3290640ea8"
down_revision = "3549e469dfee"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Add column as nullable to allow population
    op.add_column(
        "images",
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Step 2: Populate from kernels table (MAX created_at per image canonical name)
    conn = op.get_bind()
    conn.exec_driver_sql("""
        UPDATE images i
        SET last_used_at = (
            SELECT MAX(k.created_at)
            FROM kernels k
            WHERE k.image = i.name
        )
        WHERE last_used_at IS NULL
    """)

    # Step 3: Fallback to created_at for images with no kernel history
    conn.exec_driver_sql("""
        UPDATE images
        SET last_used_at = COALESCE(created_at, NOW())
        WHERE last_used_at IS NULL
    """)

    # Step 4: Set NOT NULL constraint
    op.alter_column("images", "last_used_at", nullable=False)


def downgrade() -> None:
    op.drop_column("images", "last_used_at")
