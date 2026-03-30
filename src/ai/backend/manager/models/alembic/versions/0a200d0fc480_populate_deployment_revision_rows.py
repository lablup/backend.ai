"""populate deployment revision rows from endpoint data

Revision ID: 0a200d0fc480
Revises: 3727dd0927cf
Create Date: 2026-03-25

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0a200d0fc480"
down_revision = "cff56a8381dd"
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
          AND e.lifecycle_stage != 'destroyed'
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
          AND e.lifecycle_stage != 'destroyed'
        """
    )

    # Step 3: Backfill routings.revision from the endpoint's current_revision
    # for any routes that still have revision IS NULL.
    op.execute(
        """
        UPDATE routings r
        SET revision = e.current_revision
        FROM endpoints e
        WHERE r.endpoint = e.id
          AND r.revision IS NULL
          AND e.current_revision IS NOT NULL
        """
    )

    # Note: Endpoints with image IS NULL are left as-is.
    # They cannot have a revision row (deployment_revisions.image is NOT NULL),
    # so current_revision remains nullable.


def downgrade() -> None:
    # Data-only migration: downgrade is intentionally a no-op.
    # The created revision rows and current_revision pointers are harmless
    # to keep, and there is no reliable way to distinguish revisions created
    # by this migration from those created by the original 25ac68cb28ba or
    # by normal application usage.
    pass
