"""Add created_at to bootstrap scripts."""

import sqlalchemy as sa
from alembic import op

revision = "51d33226c0a5"
down_revision = "3b8e1d6c9a47"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "bootstrap_scripts",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_column("bootstrap_scripts", "created_at")
