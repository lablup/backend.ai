"""drop health_check_enabled from deployment_revisions

Revision ID: 19159046a2a4
Revises: d1afd38a32ee
Create Date: 2026-05-12

The denormalized boolean is no longer read: route handlers gate on the
in-memory ``RouteData.health_check_config`` (projected from
``deployment_revisions.model_definition``), and the read stack (GQL /
DTO / adapter) no longer exposes the flag. Drop the column.

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
# Part of: 26.5.0 (main)
revision = "19159046a2a4"
down_revision = "d1afd38a32ee"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("deployment_revisions", "health_check_enabled")


def downgrade() -> None:
    op.add_column(
        "deployment_revisions",
        sa.Column(
            "health_check_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    # Re-backfill from the JSONB ``model_definition`` so a downgrade
    # leaves the column populated for any rollback to a manager that
    # reads it. Mirrors the original add migration's backfill.
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
