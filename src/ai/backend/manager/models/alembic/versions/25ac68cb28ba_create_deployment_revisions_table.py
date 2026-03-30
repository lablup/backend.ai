"""create deployment_revisions table

Revision ID: 25ac68cb28ba
Revises: b6a20822c683
Create Date: 2025-12-17

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql

from ai.backend.manager.models.base import GUID, IDColumn, ResourceSlotColumn, URLColumn

# revision identifiers, used by Alembic.
revision = "25ac68cb28ba"
down_revision = "b6a20822c683"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create deployment_revisions table
    op.create_table(
        "deployment_revisions",
        IDColumn(),
        sa.Column("endpoint", GUID(), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        # Image configuration
        sa.Column("image", GUID(), nullable=False),
        # Model configuration
        sa.Column("model", GUID(), nullable=True),
        sa.Column(
            "model_mount_destination",
            sa.String(length=1024),
            nullable=False,
            server_default="/models",
        ),
        sa.Column("model_definition_path", sa.String(length=128), nullable=True),
        sa.Column("model_definition", pgsql.JSONB(), nullable=True),
        # Resource configuration
        sa.Column("resource_group", sa.String(length=64), nullable=False),
        sa.Column("resource_slots", ResourceSlotColumn(), nullable=False),
        sa.Column("resource_opts", pgsql.JSONB(), nullable=False, server_default="{}"),
        # Cluster configuration
        sa.Column(
            "cluster_mode",
            sa.String(length=16),
            nullable=False,
            server_default="SINGLE_NODE",
        ),
        sa.Column("cluster_size", sa.Integer(), nullable=False, server_default="1"),
        # Execution configuration
        sa.Column("startup_command", sa.Text(), nullable=True),
        sa.Column("bootstrap_script", sa.String(length=16 * 1024), nullable=True),
        sa.Column("environ", pgsql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("callback_url", URLColumn(), nullable=True),
        sa.Column(
            "runtime_variant",
            sa.String(length=64),
            nullable=False,
            server_default="CUSTOM",
        ),
        # Mount configuration
        sa.Column("extra_mounts", pgsql.JSONB(), nullable=False, server_default="[]"),
        # Metadata
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        # Constraints
        sa.PrimaryKeyConstraint("id", name=op.f("pk_deployment_revisions")),
        sa.UniqueConstraint(
            "endpoint",
            "revision_number",
            name="uq_deployment_revisions_endpoint_revision_number",
        ),
    )
    op.create_index(
        "ix_deployment_revisions_endpoint",
        "deployment_revisions",
        ["endpoint"],
        unique=False,
    )

    # Add revision columns to endpoints table
    op.add_column(
        "endpoints",
        sa.Column("current_revision", GUID(), nullable=True),
    )
    op.add_column(
        "endpoints",
        sa.Column("deploying_revision", GUID(), nullable=True),
    )

    # Migrate existing endpoints to deployment_revisions
    # Create a revision for each non-destroyed endpoint that has an image
    op.execute(
        """
        INSERT INTO deployment_revisions (
            id, endpoint, revision_number, image, model, model_mount_destination,
            model_definition_path, model_definition, resource_group, resource_slots,
            resource_opts, cluster_mode, cluster_size, startup_command, bootstrap_script,
            environ, callback_url, runtime_variant, extra_mounts, created_at
        )
        SELECT
            uuid_generate_v4(),
            e.id,
            1,
            e.image,
            e.model,
            e.model_mount_destination,
            e.model_definition_path,
            NULL,
            e.resource_group,
            e.resource_slots,
            COALESCE(e.resource_opts, '{}'),
            e.cluster_mode,
            e.cluster_size,
            e.startup_command,
            e.bootstrap_script,
            COALESCE(e.environ, '{}'),
            e.callback_url,
            e.runtime_variant,
            COALESCE(e.extra_mounts, '[]'),
            e.created_at
        FROM endpoints e
        WHERE e.lifecycle_stage != 'destroyed' AND e.image IS NOT NULL
        """
    )

    # Update endpoints.current_revision to point to the newly created revisions
    op.execute(
        """
        UPDATE endpoints e
        SET current_revision = r.id
        FROM deployment_revisions r
        WHERE r.endpoint = e.id AND r.revision_number = 1
        """
    )


def downgrade() -> None:
    # Remove revision columns from endpoints table
    op.drop_column("endpoints", "deploying_revision")
    op.drop_column("endpoints", "current_revision")

    # Drop deployment_revisions table
    op.drop_index("ix_deployment_revisions_endpoint", table_name="deployment_revisions")
    op.drop_table("deployment_revisions")
