"""create deployment_policies table

Revision ID: 4c9e2f3a5b6d
Revises: 3a8f1c2d4e5b
Create Date: 2025-12-17

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql

from ai.backend.manager.models.base import GUID, IDColumn

# revision identifiers, used by Alembic.
revision = "4c9e2f3a5b6d"
down_revision = "3a8f1c2d4e5b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create deployment_policies table
    op.create_table(
        "deployment_policies",
        IDColumn(),
        sa.Column("endpoint", GUID(), nullable=False),
        # Deployment strategy
        sa.Column("strategy", sa.Text(), nullable=False, server_default="ROLLING"),
        # Strategy-specific specification stored as JSONB
        sa.Column("strategy_spec", pgsql.JSONB(), nullable=False, server_default="{}"),
        # Whether to rollback on deployment failure
        sa.Column("rollback_on_failure", sa.Boolean(), nullable=False, server_default="false"),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        # Constraints
        sa.PrimaryKeyConstraint("id", name=op.f("pk_deployment_policies")),
        sa.UniqueConstraint("endpoint", name="uq_deployment_policies_endpoint"),
    )
    op.create_index(
        "ix_deployment_policies_endpoint",
        "deployment_policies",
        ["endpoint"],
        unique=False,
    )

    # Create default rolling update policy for all existing endpoints
    op.execute(
        """
        INSERT INTO deployment_policies (
            id, endpoint, strategy, strategy_spec, rollback_on_failure, created_at, updated_at
        )
        SELECT
            uuid_generate_v4(),
            id,
            'ROLLING',
            '{"max_surge": 1, "max_unavailable": 0}'::jsonb,
            false,
            NOW(),
            NOW()
        FROM endpoints
        WHERE lifecycle_stage != 'destroyed'
        """
    )


def downgrade() -> None:
    # Drop deployment_policies table
    op.drop_index(
        "ix_deployment_policies_endpoint",
        table_name="deployment_policies",
    )
    op.drop_table("deployment_policies")
