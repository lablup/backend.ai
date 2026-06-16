"""add ``model_mount_perm`` to ``deployment_revisions``

Add a nullable string column ``model_mount_perm`` to the
``deployment_revisions`` table so each revision persists the resolved
permission of its model vfolder mount (READ_ONLY for vfolder/model-card
deploy, the requester's own effective permission for deployment create /
revision add).

``NULL`` represents rows written before this column existed; the
deployment draft builder falls back to ``READ_ONLY`` for those, matching
the previous hard-coded behavior.

Revision ID: f3a8c2d51b94
Revises: c6648c039bd4
Create Date: 2026-06-16

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f3a8c2d51b94"
down_revision = "c6648c039bd4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "deployment_revisions",
        sa.Column(
            "model_mount_perm",
            sa.String(length=64),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("deployment_revisions", "model_mount_perm")
