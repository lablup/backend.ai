"""create deployment_auto_scaling_policies table

Revision ID: 3a8f1c2d4e5b
Revises: 25ac68cb28ba
Create Date: 2025-12-17

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID, DecimalType, IDColumn

# revision identifiers, used by Alembic.
revision = "3a8f1c2d4e5b"
down_revision = "25ac68cb28ba"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create deployment_auto_scaling_policies table
    op.create_table(
        "deployment_auto_scaling_policies",
        IDColumn(),
        sa.Column("endpoint", GUID(), nullable=False),
        # Replica bounds
        sa.Column("min_replicas", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("max_replicas", sa.Integer(), nullable=False, server_default="10"),
        # Metric configuration
        sa.Column("metric_source", sa.Text(), nullable=True),
        sa.Column("metric_name", sa.Text(), nullable=True),
        sa.Column("comparator", sa.Text(), nullable=True),
        # Dual thresholds for hysteresis
        sa.Column("scale_up_threshold", DecimalType(), nullable=True),
        sa.Column("scale_down_threshold", DecimalType(), nullable=True),
        # Step sizes
        sa.Column("scale_up_step_size", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("scale_down_step_size", sa.Integer(), nullable=False, server_default="1"),
        # Cooldown
        sa.Column("cooldown_seconds", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("last_scaled_at", sa.DateTime(timezone=True), nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("id", name=op.f("pk_deployment_auto_scaling_policies")),
        sa.UniqueConstraint("endpoint", name="uq_deployment_auto_scaling_policies_endpoint"),
    )
    op.create_index(
        "ix_deployment_auto_scaling_policies_endpoint",
        "deployment_auto_scaling_policies",
        ["endpoint"],
        unique=False,
    )

    # Migrate existing endpoint_auto_scaling_rules to deployment_auto_scaling_policies
    # For each endpoint, take the most recently created rule and convert it to a policy
    # Note: Existing endpoint_auto_scaling_rules table is kept for backward compatibility
    op.execute(
        """
        INSERT INTO deployment_auto_scaling_policies (
            id, endpoint, min_replicas, max_replicas,
            metric_source, metric_name, comparator,
            scale_up_threshold, scale_down_threshold,
            scale_up_step_size, scale_down_step_size,
            cooldown_seconds, last_scaled_at, created_at
        )
        SELECT DISTINCT ON (endpoint)
            uuid_generate_v4(),
            endpoint,
            COALESCE(min_replicas, 1),
            COALESCE(max_replicas, 10),
            metric_source,
            metric_name,
            comparator,
            threshold,  -- Use existing threshold as scale_up_threshold
            NULL,       -- No scale_down_threshold in legacy data
            COALESCE(step_size, 1),  -- scale_up_step_size
            COALESCE(step_size, 1),  -- scale_down_step_size (same as up for legacy)
            COALESCE(cooldown_seconds, 300),
            last_triggered_at,
            created_at
        FROM endpoint_auto_scaling_rules
        ORDER BY endpoint, created_at DESC
        """
    )


def downgrade() -> None:
    # Drop deployment_auto_scaling_policies table
    op.drop_index(
        "ix_deployment_auto_scaling_policies_endpoint",
        table_name="deployment_auto_scaling_policies",
    )
    op.drop_table("deployment_auto_scaling_policies")
