"""add required to runtime_variant_presets

Revision ID: a3f1c7e2b9d4
Revises: d69322160c90
Create Date: 2026-06-09

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a3f1c7e2b9d4"
down_revision = "d69322160c90"
# Part of: 26.6.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("runtime_variant_presets")]
    if "required" not in columns:
        op.add_column(
            "runtime_variant_presets",
            sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.false()),
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("runtime_variant_presets")]
    if "required" in columns:
        op.drop_column("runtime_variant_presets", "required")
