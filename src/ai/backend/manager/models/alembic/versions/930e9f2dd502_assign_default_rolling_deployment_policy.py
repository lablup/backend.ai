"""assign default rolling deployment policy and add FK to endpoints

Revision ID: 930e9f2dd502
Revises: 869918e9e95a
Create Date: 2026-03-25

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "930e9f2dd502"
down_revision = "869918e9e95a"
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
            '{"max_surge": {"percent": 0.5}, "max_unavailable": {"percent": 0.0}}'::jsonb,
            NOW(),
            NOW()
        FROM endpoints e
        LEFT JOIN deployment_policies dp ON dp.endpoint = e.id
        WHERE dp.id IS NULL
        """
    )

    # Remove orphaned policies referencing non-existent endpoints
    op.execute(
        """
        DELETE FROM deployment_policies dp
        WHERE NOT EXISTS (
            SELECT 1 FROM endpoints e WHERE e.id = dp.endpoint
        )
        """
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
