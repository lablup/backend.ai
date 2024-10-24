"""Add extra column to container_registries

Revision ID: e9e574a6e22d
Revises: 7c8501cec07b
Create Date: 2024-10-23 20:56:36.513421

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = "e9e574a6e22d"
down_revision = "7c8501cec07b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [col["name"] for col in inspector.get_columns("container_registries")]

    # Prevent error in case the extra column was created using a previously modified migration script.
    if "extra" not in columns:
        op.add_column(
            "container_registries",
            sa.Column("extra", sa.JSON, default=None, nullable=True),
        )


def downgrade() -> None:
    op.drop_column("container_registries", "extra")
