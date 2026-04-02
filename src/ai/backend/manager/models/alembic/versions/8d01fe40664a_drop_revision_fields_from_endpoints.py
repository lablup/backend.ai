"""drop revision fields from endpoints and resource_group from deployment_revisions

Revision ID: 8d01fe40664a
Revises: af1b9ec86adb
Create Date: 2026-04-01

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql

# revision identifiers, used by Alembic.
revision = "8d01fe40664a"
down_revision = "af1b9ec86adb"
branch_labels = None
depends_on = None

# Columns to drop from the endpoints table.
# These revision-level fields now live exclusively in deployment_revisions.
_ENDPOINT_COLUMNS_TO_DROP = [
    "image",
    "model",
    "model_mount_destination",
    "model_definition_path",
    "resource_slots",
    "resource_opts",
    "cluster_mode",
    "cluster_size",
    "startup_command",
    "bootstrap_script",
    "environ",
    "callback_url",
    "runtime_variant",
    "extra_mounts",
]


def upgrade() -> None:
    # Drop the CHECK constraint that references the image column.
    op.execute("ALTER TABLE endpoints DROP CONSTRAINT IF EXISTS ck_image_required_unless_destroyed")

    # Drop the FK constraint on endpoints.model → vfolders.id.
    # The constraint name follows the SQLAlchemy auto-naming convention.
    op.execute("ALTER TABLE endpoints DROP CONSTRAINT IF EXISTS endpoints_model_fkey")

    # Drop revision columns from endpoints.
    for col in _ENDPOINT_COLUMNS_TO_DROP:
        op.execute(f"ALTER TABLE endpoints DROP COLUMN IF EXISTS {col}")


def downgrade() -> None:
    # Re-add columns to endpoints.
    op.add_column("endpoints", sa.Column("image", sa.UUID(), nullable=True))
    op.add_column(
        "endpoints",
        sa.Column(
            "model",
            sa.UUID(),
            sa.ForeignKey("vfolders.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
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
        "endpoints",
        sa.Column("model_definition_path", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "endpoints",
        sa.Column("resource_slots", pgsql.JSONB(), nullable=True),
    )
    op.add_column(
        "endpoints",
        sa.Column("resource_opts", pgsql.JSONB(), nullable=True, server_default="{}"),
    )
    op.add_column(
        "endpoints",
        sa.Column(
            "cluster_mode",
            sa.String(length=16),
            nullable=False,
            server_default="SINGLE_NODE",
        ),
    )
    op.add_column(
        "endpoints",
        sa.Column("cluster_size", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "endpoints",
        sa.Column("startup_command", sa.Text(), nullable=True),
    )
    op.add_column(
        "endpoints",
        sa.Column("bootstrap_script", sa.String(length=16384), nullable=True),
    )
    op.add_column(
        "endpoints",
        sa.Column("environ", pgsql.JSONB(), nullable=True, server_default="{}"),
    )
    op.add_column(
        "endpoints",
        sa.Column("callback_url", sa.String(), nullable=True),
    )
    op.add_column(
        "endpoints",
        sa.Column(
            "runtime_variant",
            sa.String(length=64),
            nullable=False,
            server_default="CUSTOM",
        ),
    )
    op.add_column(
        "endpoints",
        sa.Column("extra_mounts", pgsql.JSONB(), nullable=False, server_default="[]"),
    )

    # Backfill endpoints columns from current_revision's deployment_revision.
    op.execute("""
        UPDATE endpoints e
        SET
            image = dr.image,
            model = dr.model,
            model_mount_destination = dr.model_mount_destination,
            model_definition_path = dr.model_definition_path,
            resource_slots = dr.resource_slots,
            resource_opts = dr.resource_opts,
            cluster_mode = dr.cluster_mode,
            cluster_size = dr.cluster_size,
            startup_command = dr.startup_command,
            bootstrap_script = dr.bootstrap_script,
            environ = dr.environ,
            callback_url = dr.callback_url,
            runtime_variant = dr.runtime_variant,
            extra_mounts = dr.extra_mounts
        FROM deployment_revisions dr
        WHERE e.current_revision = dr.id
    """)

    # Re-add the CHECK constraint.
    op.execute("""
        ALTER TABLE endpoints
        ADD CONSTRAINT ck_image_required_unless_destroyed
        CHECK (lifecycle_stage = 'destroyed' OR image IS NOT NULL)
    """)
