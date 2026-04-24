"""add FK to deployment_revisions.image (SET NULL)

Adds a foreign key from ``deployment_revisions.image`` to ``images.id``
with ``ON DELETE SET NULL``, and relaxes the column to ``nullable=True``.

Rationale: revisions are operational history and may outlive the image
they originally referenced. Deleting the image must not cascade into
dropping the revision (that would erase deployment history) nor be
blocked outright (operators need to remove stale images). SET NULL lets
the image row go away while the revision survives — it simply cannot
be redeployed until a new revision with a live image is activated
(see ``EndpointLifecycle.BLOCKED``).

The column previously carried a UUID with no DB-level FK, so dangling
references were possible. Pre-existing rows whose ``image`` no longer
resolves are backfilled to NULL (SET NULL semantics applied retroactively
to the already-lost referent).

Revision ID: c7d8e9f0a1b2
Revises: b5c6d7e8f9a0
Create Date: 2026-04-19

"""

# Part of: 26.5.0

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c7d8e9f0a1b2"
down_revision = "b5c6d7e8f9a0"
branch_labels = None
depends_on = None


_FK_NAME = "fk_deployment_revisions_image_images"


def upgrade() -> None:
    # Backfill rows whose ``image`` value no longer exists in ``images``
    # to NULL so the SET NULL FK can attach cleanly. This matches the
    # post-FK semantics: a lost referent becomes NULL.
    op.execute(
        sa.text(
            "UPDATE deployment_revisions "
            "SET image = NULL "
            "WHERE image IS NOT NULL "
            "AND image NOT IN (SELECT id FROM images)"
        )
    )
    op.alter_column("deployment_revisions", "image", nullable=True)
    op.create_foreign_key(
        _FK_NAME,
        source_table="deployment_revisions",
        referent_table="images",
        local_cols=["image"],
        remote_cols=["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(_FK_NAME, "deployment_revisions", type_="foreignkey")
    # Revert to NOT NULL only if no NULL rows remain; otherwise the
    # downgrade cannot reinstate the original shape without data loss,
    # so we surface the problem to the operator.
    null_count = (
        op.get_bind()
        .execute(sa.text("SELECT COUNT(*) FROM deployment_revisions WHERE image IS NULL"))
        .scalar()
    )
    if null_count:
        raise RuntimeError(
            f"Cannot downgrade: {null_count} deployment_revisions row(s) have NULL image. "
            f"Resolve these rows (assign an image or delete the revision) before downgrading."
        )
    op.alter_column("deployment_revisions", "image", nullable=False)
