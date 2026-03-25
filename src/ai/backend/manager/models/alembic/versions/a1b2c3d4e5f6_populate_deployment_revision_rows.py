"""populate deployment revision rows from endpoint data

Revision ID: a1b2c3d4e5f6
Revises: 3727dd0927cf
Create Date: 2026-03-25

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "3727dd0927cf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Create deployment revision rows for endpoints that still have
    # current_revision IS NULL but have an image (i.e., endpoints skipped by
    # the original migration 25ac68cb28ba).
    # Use a subquery to determine the next available revision_number per endpoint.
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
            COALESCE(
                (SELECT MAX(dr.revision_number) + 1
                 FROM deployment_revisions dr
                 WHERE dr.endpoint = e.id),
                1
            ),
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
            COALESCE(e.created_at, now())
        FROM endpoints e
        WHERE e.current_revision IS NULL
          AND e.image IS NOT NULL
        """
    )

    # Step 2: Point current_revision to the newly created revision rows.
    op.execute(
        """
        UPDATE endpoints e
        SET current_revision = (
            SELECT dr.id
            FROM deployment_revisions dr
            WHERE dr.endpoint = e.id
            ORDER BY dr.revision_number DESC
            LIMIT 1
        )
        WHERE e.current_revision IS NULL
          AND e.image IS NOT NULL
        """
    )

    # Step 3: Mark endpoints with no image and no current_revision as destroyed.
    # These are invalid/incomplete endpoints that cannot have a valid revision.
    op.execute(
        """
        UPDATE endpoints
        SET lifecycle_stage = 'destroyed',
            destroyed_at = COALESCE(destroyed_at, now())
        WHERE current_revision IS NULL
          AND image IS NULL
        """
    )

    # Step 4: Make current_revision non-nullable.
    op.alter_column(
        "endpoints",
        "current_revision",
        existing_type=sa.Uuid(),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "endpoints",
        "current_revision",
        existing_type=sa.Uuid(),
        nullable=True,
    )
