"""make revision-preset deployment fields not null

Revision ID: ba5923b1f4a7
Revises: aa596a09c091
Create Date: 2026-04-30

Backfill defaults for the deployment-level columns that were previously
``nullable=True`` and then enforce ``NOT NULL`` so every preset carries
the values needed to create a deployment.

Backfill choices match the system defaults that were silently applied in
``_apply_deployment_level_preset`` until now:

- ``replica_count`` -> 1
- ``deployment_strategy`` -> ``ROLLING``
- ``deployment_strategy_spec`` -> ``{}`` (empty rolling spec; the
  application validates concrete fields on read)

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql

# revision identifiers, used by Alembic.
# Part of: 26.4.5 (main)
revision = "ba5923b1f4a7"
down_revision = "aa596a09c091"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE deployment_revision_presets SET replica_count = 1 WHERE replica_count IS NULL"
        )
    )
    op.execute(
        sa.text(
            "UPDATE deployment_revision_presets SET deployment_strategy = 'ROLLING' "
            "WHERE deployment_strategy IS NULL"
        )
    )
    op.execute(
        sa.text(
            "UPDATE deployment_revision_presets "
            "SET deployment_strategy_spec = '{}'::jsonb "
            "WHERE deployment_strategy_spec IS NULL"
        )
    )

    op.alter_column(
        "deployment_revision_presets",
        "replica_count",
        existing_type=sa.Integer(),
        nullable=False,
        server_default=sa.text("1"),
    )
    op.alter_column(
        "deployment_revision_presets",
        "deployment_strategy",
        existing_type=sa.String(length=32),
        nullable=False,
        server_default=sa.text("'ROLLING'"),
    )
    op.alter_column(
        "deployment_revision_presets",
        "deployment_strategy_spec",
        existing_type=pgsql.JSONB(),
        nullable=False,
        server_default=sa.text("'{}'::jsonb"),
    )


def downgrade() -> None:
    op.alter_column(
        "deployment_revision_presets",
        "deployment_strategy_spec",
        existing_type=pgsql.JSONB(),
        nullable=True,
        server_default=None,
    )
    op.alter_column(
        "deployment_revision_presets",
        "deployment_strategy",
        existing_type=sa.String(length=32),
        nullable=True,
        server_default=None,
    )
    op.alter_column(
        "deployment_revision_presets",
        "replica_count",
        existing_type=sa.Integer(),
        nullable=True,
        server_default=None,
    )
