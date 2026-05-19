"""add FK to images.registry_id (RESTRICT)

Adds a foreign key from ``images.registry_id`` to ``container_registries.id``
with ``ON DELETE RESTRICT``.

Rationale: the column previously carried a UUID with no DB-level FK, so
deleting a container registry left dangling references on the images
table. The sokovan scheduler would later surface this as a misleading
"Image not found in database" error during session launch. RESTRICT
prevents the registry deletion at the database level, forcing callers
to ``clear_images`` (soft-delete) or ``admin_purge`` the dependent rows
first. CASCADE was rejected because it would also hard-delete image
rows referenced by historical kernels / deployment_revisions via
SET NULL, erasing audit traceability.

Pre-existing dangling rows (image rows whose ``registry_id`` no longer
resolves) are hard-deleted before the constraint is created. The column
remains ``NOT NULL``, so a SET NULL backfill is not an option, and a
sentinel re-assignment would mask the original deletion intent.

Revision ID: 045b0e0e4384
Revises: ccd5dbb99161
Create Date: 2026-05-17

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "045b0e0e4384"
down_revision = "ccd5dbb99161"
# Part of: 26.5.0
branch_labels = None
depends_on = None

_FK_NAME = "fk_images_registry_id_container_registries"


def upgrade() -> None:
    op.execute(
        sa.text("DELETE FROM images WHERE registry_id NOT IN (SELECT id FROM container_registries)")
    )
    op.create_foreign_key(
        _FK_NAME,
        source_table="images",
        referent_table="container_registries",
        local_cols=["registry_id"],
        remote_cols=["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(_FK_NAME, "images", type_="foreignkey")
