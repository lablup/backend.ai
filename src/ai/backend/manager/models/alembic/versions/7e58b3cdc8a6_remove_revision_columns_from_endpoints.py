"""remove revision columns from endpoints table

Revision ID: 7e58b3cdc8a6
Revises: 979bd203db8a
Create Date: 2026-03-31

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql

# revision identifiers, used by Alembic.
revision = "7e58b3cdc8a6"
down_revision = "979bd203db8a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove check constraint (use raw SQL because alembic auto-prefixes constraint names)
    op.execute(
        "ALTER TABLE endpoints DROP CONSTRAINT IF EXISTS ck_endpoints_ck_image_required_unless_destroyed"
    )

    # Remove foreign key constraints
    op.drop_constraint(
        "fk_endpoints_resource_group_scaling_groups", "endpoints", type_="foreignkey"
    )
    op.drop_constraint("fk_endpoints_model_vfolders", "endpoints", type_="foreignkey")

    # Remove index on resource_group
    op.drop_index("ix_endpoints_resource_group", table_name="endpoints")

    # Remove revision-related columns from endpoints table
    op.drop_column("endpoints", "image")
    op.drop_column("endpoints", "model")
    op.drop_column("endpoints", "model_mount_destination")
    op.drop_column("endpoints", "model_definition_path")
    op.drop_column("endpoints", "resource_group")
    op.drop_column("endpoints", "resource_slots")
    op.drop_column("endpoints", "resource_opts")
    op.drop_column("endpoints", "cluster_mode")
    op.drop_column("endpoints", "cluster_size")
    op.drop_column("endpoints", "startup_command")
    op.drop_column("endpoints", "bootstrap_script")
    op.drop_column("endpoints", "callback_url")
    op.drop_column("endpoints", "environ")
    op.drop_column("endpoints", "runtime_variant")
    op.drop_column("endpoints", "extra_mounts")


def downgrade() -> None:
    # Re-add revision-related columns (nullable to allow endpoints without revision)
    op.add_column("endpoints", sa.Column("image", pgsql.UUID(), nullable=True))
    op.add_column("endpoints", sa.Column("model", pgsql.UUID(), nullable=True))
    op.add_column(
        "endpoints",
        sa.Column(
            "model_mount_destination",
            sa.String(length=1024),
            nullable=False,
            server_default="/models",
        ),
    )
    op.add_column(
        "endpoints", sa.Column("model_definition_path", sa.String(length=128), nullable=True)
    )
    op.add_column("endpoints", sa.Column("resource_group", sa.String(), nullable=True))
    op.add_column("endpoints", sa.Column("resource_slots", pgsql.JSONB(), nullable=True))
    op.add_column(
        "endpoints", sa.Column("resource_opts", pgsql.JSONB(), nullable=True, server_default="{}")
    )
    op.add_column(
        "endpoints",
        sa.Column(
            "cluster_mode", sa.String(length=16), nullable=False, server_default="SINGLE_NODE"
        ),
    )
    op.add_column(
        "endpoints", sa.Column("cluster_size", sa.Integer(), nullable=False, server_default="1")
    )
    op.add_column("endpoints", sa.Column("startup_command", sa.Text(), nullable=True))
    op.add_column(
        "endpoints", sa.Column("bootstrap_script", sa.String(length=16384), nullable=True)
    )
    op.add_column("endpoints", sa.Column("callback_url", sa.String(), nullable=True))
    op.add_column(
        "endpoints", sa.Column("environ", pgsql.JSONB(), nullable=True, server_default="{}")
    )
    op.add_column(
        "endpoints",
        sa.Column("runtime_variant", sa.String(length=64), nullable=False, server_default="CUSTOM"),
    )
    op.add_column(
        "endpoints", sa.Column("extra_mounts", pgsql.JSONB(), nullable=False, server_default="[]")
    )

    # Repopulate from deployment_revisions (only for endpoints that have a current_revision)
    op.execute("""
        UPDATE endpoints e
        SET
            image = dr.image,
            model = dr.model,
            model_mount_destination = dr.model_mount_destination,
            model_definition_path = dr.model_definition_path,
            resource_group = dr.resource_group,
            resource_slots = dr.resource_slots,
            resource_opts = dr.resource_opts,
            cluster_mode = dr.cluster_mode,
            cluster_size = dr.cluster_size,
            startup_command = dr.startup_command,
            bootstrap_script = dr.bootstrap_script,
            callback_url = dr.callback_url,
            environ = dr.environ,
            runtime_variant = dr.runtime_variant,
            extra_mounts = dr.extra_mounts
        FROM deployment_revisions dr
        WHERE e.current_revision = dr.id
    """)

    # Re-create foreign key constraints
    op.create_foreign_key(
        "fk_endpoints_model_vfolders",
        "endpoints",
        "vfolders",
        ["model"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_endpoints_resource_group_scaling_groups",
        "endpoints",
        "scaling_groups",
        ["resource_group"],
        ["name"],
        ondelete="RESTRICT",
    )

    # Re-create index
    op.create_index("ix_endpoints_resource_group", "endpoints", ["resource_group"])

    # Re-add check constraint (only applies to endpoints that have revision data)
    op.execute("""
        ALTER TABLE endpoints
        ADD CONSTRAINT ck_endpoints_ck_image_required_unless_destroyed
        CHECK (lifecycle_stage = 'destroyed' OR current_revision IS NULL OR image IS NOT NULL)
    """)
