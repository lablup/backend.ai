"""add deployment options to scaling group and endpoint

Introduces per-deployment operational options keyed by handler name so
the coordinator can look up timeouts (and future options) from the
endpoint row instead of a hardcoded module constant.

Upgrade steps:

1. Add ``scaling_groups.default_deployment_options`` (jsonb, NOT NULL)
   — default values (``{"timeouts":{"default":null,"by_handler":{...}}}``)
   are snapshot onto each deployment at create time, so later changes
   do not propagate to existing deployments.
2. Add ``endpoints.options`` (jsonb, NOT NULL). Existing rows are
   backfilled with the same opt-in default (deploying / rolling-back /
   scaling handlers get 3600s; every other handler has no timeout).

Downgrade drops both columns.

Revision ID: b1a2c3d4e5f6
Revises: f0b1c2d3e4a5
Create Date: 2026-04-20

"""

# Part of: 26.5.0

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql

# revision identifiers, used by Alembic.
revision = "b1a2c3d4e5f6"
down_revision = "f0b1c2d3e4a5"
branch_labels = None
depends_on = None


_DEFAULT_DEPLOYMENT_OPTIONS_JSON = (
    '{"timeouts":{"default":null,"by_handler":'
    '{"deploying-provisioning":3600,'
    '"deploying-rolling-back":3600,'
    '"scaling-deployments":3600}}}'
)


def _add_column_with_json_default(table: str, column: str) -> None:
    """Add a JSONB column with the baseline ``DeploymentOptions``
    default.

    ALTER TABLE ... SET DEFAULT cannot accept bind parameters, and
    SQLAlchemy's ``text()`` scans the rendered SQL for ``:name``
    placeholders even inside quoted literals. Each ``:`` in the JSON
    payload and the ``::jsonb`` cast is therefore escaped with ``\\:``
    so SQLAlchemy emits a literal colon.
    """
    op.add_column(table, sa.Column(column, pgsql.JSONB(), nullable=True))
    op.execute(
        sa.text(f"UPDATE {table} SET {column} = CAST(:val AS JSONB)").bindparams(
            val=_DEFAULT_DEPLOYMENT_OPTIONS_JSON
        )
    )
    op.alter_column(table, column, nullable=False)
    escaped_json = _DEFAULT_DEPLOYMENT_OPTIONS_JSON.replace(":", r"\:")
    op.execute(
        sa.text(
            f"ALTER TABLE {table} ALTER COLUMN {column} SET DEFAULT '{escaped_json}'\\:\\:jsonb"
        )
    )


def upgrade() -> None:
    _add_column_with_json_default("scaling_groups", "default_deployment_options")
    _add_column_with_json_default("endpoints", "options")


def downgrade() -> None:
    op.drop_column("endpoints", "options")
    op.drop_column("scaling_groups", "default_deployment_options")
