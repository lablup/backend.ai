"""seed reads_vfolder_config_files for custom runtime variant

The original seed migration (``9229f72fa447``) inserted runtime variants
with only ``name`` / ``description``, so ``reads_vfolder_config_files``
took its server default of ``false`` for every row. The install fixture
sets the flag to ``true`` for the ``custom`` variant, but
``populate_fixture`` uses ``ON CONFLICT DO NOTHING`` and therefore never
overwrites the already-seeded row. Backfill the intended value here so
``custom`` actually triggers the vfolder ``model-definition.yaml`` scan
at revision-creation time.

Revision ID: 0b10b2c6a972
Revises: ba42cb865efe
Create Date: 2026-05-18

"""

# Part of: 26.5.0

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0b10b2c6a972"
down_revision = "ba42cb865efe"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE runtime_variants "
            "SET reads_vfolder_config_files = true "
            "WHERE name = 'custom'"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE runtime_variants "
            "SET reads_vfolder_config_files = false "
            "WHERE name = 'custom'"
        )
    )
