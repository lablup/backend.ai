"""add FK to deployment_revisions.model (SET NULL)

Adds a foreign key from ``deployment_revisions.model`` to ``vfolders.id``
with ``ON DELETE SET NULL``. The column has always been nullable, but
previously no FK existed — so deleting the backing vfolder left a
dangling UUID on the revision with no DB-level signal that the model
was gone.

SET NULL mirrors the treatment of ``endpoints.model`` (migration
``589c764a18f1``) and preserves the deployment history while allowing
operators to remove the model vfolder. A revision whose ``model``
collapses to NULL cannot be redeployed and is expected to be
superseded by a new revision pointing at the replacement vfolder.

Revision ID: e9f0a1b2c3d4
Revises: d8e9f0a1b2c3
Create Date: 2026-04-19

"""

# Part of: 26.5.0

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e9f0a1b2c3d4"
down_revision = "d8e9f0a1b2c3"
branch_labels = None
depends_on = None


_FK_NAME = "fk_deployment_revisions_model_vfolders"


def upgrade() -> None:
    # Dangling UUIDs (backing vfolder already deleted) are backfilled to
    # NULL so the SET NULL FK attaches cleanly.
    op.execute(
        sa.text(
            "UPDATE deployment_revisions "
            "SET model = NULL "
            "WHERE model IS NOT NULL "
            "AND model NOT IN (SELECT id FROM vfolders)"
        )
    )
    op.create_foreign_key(
        _FK_NAME,
        source_table="deployment_revisions",
        referent_table="vfolders",
        local_cols=["model"],
        remote_cols=["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(_FK_NAME, "deployment_revisions", type_="foreignkey")
