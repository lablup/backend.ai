"""drop runtime_variant_presets.ui_type column; ui_type lives in ui_option

The :class:`UIOption` Pydantic model that backs
``runtime_variant_presets.ui_option`` (a JSONB column) declares
``ui_type`` as a *required* field. The table also kept a duplicate
``ui_type`` *column*, and historical rows had the JSONB persisted
without the ``ui_type`` key — relying on the sibling column alone.
Reads of those rows fail with::

    pydantic_core._pydantic_core.ValidationError: 1 validation error for UIOption
    ui_type
      Field required

so any list/get over the affected presets returns HTTP 500.

This migration consolidates the storage by:

1. Backfilling ``ui_option.ui_type`` from the column for rows where the
   JSONB exists but lacks the key.
2. Dropping the now-redundant ``ui_type`` column.

The Pydantic model is unchanged; the JSONB becomes the single source of
truth for ``ui_type``.

Revision ID: d1c0f1e2b3a4
Revises: ce69b746304e
Create Date: 2026-04-26

"""

# Part of: 26.5.0

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "d1c0f1e2b3a4"
down_revision = "ce69b746304e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        text(
            "UPDATE runtime_variant_presets "
            "SET ui_option = jsonb_set(ui_option, '{ui_type}', to_jsonb(ui_type::text)) "
            "WHERE ui_option IS NOT NULL "
            "  AND ui_type IS NOT NULL "
            "  AND NOT (ui_option ? 'ui_type');"
        )
    )
    op.drop_column("runtime_variant_presets", "ui_type")


def downgrade() -> None:
    op.add_column(
        "runtime_variant_presets",
        sa.Column("ui_type", sa.String(length=32), nullable=True),
    )
    op.execute(
        text(
            "UPDATE runtime_variant_presets "
            "SET ui_type = ui_option->>'ui_type' "
            "WHERE ui_option IS NOT NULL "
            "  AND ui_option ? 'ui_type';"
        )
    )
