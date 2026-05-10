"""add health_check_enabled to deployment_revisions

Revision ID: d1afd38a32ee
Revises: fc249eccd0b2
Create Date: 2026-05-09

Denormalized boolean of whether the revision's ``model_definition``
declares a ``service.health_check`` block. Backfilled by scanning
existing JSONB rows.

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
# Part of: 26.5.0 (main)
revision = "d1afd38a32ee"
down_revision = "fc249eccd0b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "deployment_revisions",
        sa.Column(
            "health_check_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    # ``->`` returns SQL NULL only when the key is absent; an explicit
    # JSON ``null`` (which ``PydanticColumn.process_bind_param`` produces
    # for ``health_check=None``) is a JSONB 'null' value, not SQL NULL.
    # Filter both forms with ``jsonb_typeof(...) != 'null'``.
    op.execute(
        sa.text(
            """
            UPDATE deployment_revisions
            SET health_check_enabled = TRUE
            WHERE model_definition IS NOT NULL
              AND EXISTS (
                SELECT 1
                FROM jsonb_array_elements(
                    COALESCE(model_definition->'models', '[]'::jsonb)
                ) AS m
                WHERE m->'service'->'health_check' IS NOT NULL
                  AND jsonb_typeof(m->'service'->'health_check') != 'null'
              )
            """
        )
    )


def downgrade() -> None:
    op.drop_column("deployment_revisions", "health_check_enabled")
