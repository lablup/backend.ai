"""assign default rolling deployment policy to existing deployments

Revision ID: a1b2c3d4e5f6
Revises: 19e48e70b86a
Create Date: 2026-03-25

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "19e48e70b86a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create a tracking table to record which policies were auto-created
    # by this migration, enabling a clean downgrade.
    op.create_table(
        "_migration_a1b2c3d4e5f6_created_policies",
        sa.Column("endpoint_id", GUID(), nullable=False, primary_key=True),
    )

    # Record endpoints that currently lack a deployment policy.
    op.execute(
        """
        INSERT INTO _migration_a1b2c3d4e5f6_created_policies (endpoint_id)
        SELECT e.id
        FROM endpoints e
        LEFT JOIN deployment_policies dp ON dp.endpoint = e.id
        WHERE dp.id IS NULL
          AND e.lifecycle_stage != 'destroyed'
        """
    )

    # Insert a default rolling deployment policy for those endpoints.
    op.execute(
        """
        INSERT INTO deployment_policies (
            id, endpoint, strategy, strategy_spec, created_at, updated_at
        )
        SELECT
            uuid_generate_v4(),
            endpoint_id,
            'ROLLING',
            '{"max_surge": 1, "max_unavailable": 0}'::jsonb,
            NOW(),
            NOW()
        FROM _migration_a1b2c3d4e5f6_created_policies
        """
    )


def downgrade() -> None:
    # Remove only the deployment policies that were created by this migration.
    op.execute(
        """
        DELETE FROM deployment_policies
        WHERE endpoint IN (
            SELECT endpoint_id
            FROM _migration_a1b2c3d4e5f6_created_policies
        )
        """
    )

    op.drop_table("_migration_a1b2c3d4e5f6_created_policies")
