"""create runtime_variants table

Revision ID: 2bf0e9a716de
Revises: 979bd203db8a
Create Date: 2026-03-31

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import IDColumn

# revision identifiers, used by Alembic.
revision = "2bf0e9a716de"
down_revision = "979bd203db8a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "runtime_variants",
        IDColumn(),
        sa.Column("name", sa.String(length=128), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_runtime_variants")),
    )


def downgrade() -> None:
    op.drop_table("runtime_variants")
