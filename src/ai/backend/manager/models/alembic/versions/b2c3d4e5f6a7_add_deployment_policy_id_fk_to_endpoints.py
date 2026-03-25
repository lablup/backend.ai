"""add deployment_policy_id FK to endpoints

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-25

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Add nullable column first
    op.add_column(
        "endpoints",
        sa.Column("deployment_policy_id", GUID(), nullable=True),
    )

    # Step 2: Backfill from existing deployment_policies rows
    op.execute(
        """
        UPDATE endpoints e
        SET deployment_policy_id = dp.id
        FROM deployment_policies dp
        WHERE dp.endpoint = e.id
        """
    )

    # Step 3: Safety net — create default policies for any remaining endpoints
    # without a policy (should not exist after the previous migration, but be safe)
    op.execute(
        """
        INSERT INTO deployment_policies (
            id, endpoint, strategy, strategy_spec, created_at, updated_at
        )
        SELECT
            uuid_generate_v4(),
            e.id,
            'ROLLING',
            '{"max_surge": 1, "max_unavailable": 0}'::jsonb,
            NOW(),
            NOW()
        FROM endpoints e
        LEFT JOIN deployment_policies dp ON dp.endpoint = e.id
        WHERE dp.id IS NULL
          AND e.lifecycle_stage != 'destroyed'
        """
    )

    # Step 4: Backfill any newly created policies
    op.execute(
        """
        UPDATE endpoints e
        SET deployment_policy_id = dp.id
        FROM deployment_policies dp
        WHERE dp.endpoint = e.id
          AND e.deployment_policy_id IS NULL
        """
    )

    # Step 5: Set NOT NULL constraint
    op.alter_column("endpoints", "deployment_policy_id", nullable=False)

    # Step 6: Add DEFERRABLE FK constraint
    op.create_foreign_key(
        "fk_endpoints_deployment_policy_id",
        "endpoints",
        "deployment_policies",
        ["deployment_policy_id"],
        ["id"],
        ondelete="RESTRICT",
        deferrable=True,
        initially="DEFERRED",
    )

    # Step 7: Add unique constraint (1:1 relationship)
    op.create_unique_constraint(
        "uq_endpoints_deployment_policy_id",
        "endpoints",
        ["deployment_policy_id"],
    )

    # Step 8: Add index
    op.create_index(
        "ix_endpoints_deployment_policy_id",
        "endpoints",
        ["deployment_policy_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_endpoints_deployment_policy_id", table_name="endpoints")
    op.drop_constraint("uq_endpoints_deployment_policy_id", "endpoints", type_="unique")
    op.drop_constraint("fk_endpoints_deployment_policy_id", "endpoints", type_="foreignkey")
    op.drop_column("endpoints", "deployment_policy_id")
