"""Add auto_assign_to_owner to role presets

A personal project's owner is mapped to the role of a preset carrying this flag. The
project_admin preset carries it, as its seed file states.

Revision ID: c7d14e2a9f60
Revises: 9ee2d3b5a945
Create Date: 2026-10-31

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c7d14e2a9f60"  # Part of: NEXT_RELEASE_VERSION
down_revision = "9ee2d3b5a945"
branch_labels = None
depends_on = None


_PROJECT_ADMIN_PRESET_ID: Final[str] = "22c4db03-24aa-5ff8-b5a9-64b2a2182413"


def upgrade() -> None:
    op.add_column(
        "role_presets",
        sa.Column("auto_assign_to_owner", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.get_bind().execute(
        sa.text(
            "UPDATE role_presets SET auto_assign_to_owner = TRUE"
            " WHERE id = CAST(:preset_id AS uuid)"
        ).bindparams(preset_id=_PROJECT_ADMIN_PRESET_ID)
    )


def downgrade() -> None:
    op.drop_column("role_presets", "auto_assign_to_owner")
