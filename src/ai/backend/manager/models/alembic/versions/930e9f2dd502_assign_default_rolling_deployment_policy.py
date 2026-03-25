"""assign default rolling deployment policy and add FK to endpoints

Revision ID: 930e9f2dd502
Revises: 3727dd0927cf
Create Date: 2026-03-25

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "930e9f2dd502"
down_revision = "3727dd0927cf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create default rolling policies for all endpoints without one.
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
        """
    )

    # Add nullable column
    op.add_column(
        "endpoints",
        sa.Column("deployment_policy_id", GUID(), nullable=True),
    )

    # Backfill from deployment_policies
    op.execute(
        """
        UPDATE endpoints e
        SET deployment_policy_id = dp.id
        FROM deployment_policies dp
        WHERE dp.endpoint = e.id
        """
    )

    # Set NOT NULL
    op.alter_column("endpoints", "deployment_policy_id", nullable=False)

    # Add DEFERRABLE FK constraint
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

    # Unique constraint (1:1 relationship)
    op.create_unique_constraint(
        "uq_endpoints_deployment_policy_id",
        "endpoints",
        ["deployment_policy_id"],
    )

    # Index
    op.create_index(
        "ix_endpoints_deployment_policy_id",
        "endpoints",
        ["deployment_policy_id"],
    )

    # Add CASCADE FK from deployment_policies.endpoint → endpoints.id
    # so that deleting an endpoint automatically deletes its policy.
    op.create_foreign_key(
        "fk_deployment_policies_endpoint",
        "deployment_policies",
        "endpoints",
        ["endpoint"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_deployment_policies_endpoint", "deployment_policies", type_="foreignkey")
    op.drop_index("ix_endpoints_deployment_policy_id", table_name="endpoints")
    op.drop_constraint("uq_endpoints_deployment_policy_id", "endpoints", type_="unique")
    op.drop_constraint("fk_endpoints_deployment_policy_id", "endpoints", type_="foreignkey")
    op.drop_column("endpoints", "deployment_policy_id")
