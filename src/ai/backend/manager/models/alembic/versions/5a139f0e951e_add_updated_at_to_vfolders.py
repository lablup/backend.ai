"""Add `updated_at` column to `vfolders`

Revision ID: 5a139f0e951e
Revises: ba5923b1f4a7
Create Date: 2026-04-07

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5a139f0e951e"
down_revision = "ba5923b1f4a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "vfolders",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute("UPDATE vfolders SET updated_at = COALESCE(last_used, created_at)")
    op.alter_column(
        "vfolders",
        "updated_at",
        nullable=False,
        server_default=sa.func.now(),
    )


def downgrade() -> None:
    op.drop_column("vfolders", "updated_at")
