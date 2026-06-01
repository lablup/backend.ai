"""add reads_vfolder_config_files to runtime_variants

Revision ID: 7ea9f3c1b2d5
Revises: ad7acfe8aa1c
Create Date: 2026-04-18

"""

# Part of: 26.5.0

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "7ea9f3c1b2d5"
down_revision = "ad7acfe8aa1c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "runtime_variants",
        sa.Column(
            "reads_vfolder_config_files",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.execute(
        sa.text(
            "UPDATE runtime_variants SET reads_vfolder_config_files = TRUE WHERE name = 'custom'"
        )
    )


def downgrade() -> None:
    op.drop_column("runtime_variants", "reads_vfolder_config_files")
