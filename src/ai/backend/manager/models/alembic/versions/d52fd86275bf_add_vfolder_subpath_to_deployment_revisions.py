"""add ``vfolder_subpath`` to ``deployment_revisions``

Add a nullable string column ``vfolder_subpath`` to the
``deployment_revisions`` table so model service revisions can persist
a per-revision subpath for the model vfolder mount (the equivalent of
``MountInfoEntry.subpath`` carried by each entry in ``extra_mounts``).

``NULL`` means the model vfolder is mounted at its root, matching the
existing extra-mount semantics where ``subpath IS NULL`` resolves to
``"."`` inside ``prepare_vfolder_mounts``.

Revision ID: d52fd86275bf
Revises: a1b2c3d4e5f7
Create Date: 2026-05-11

"""

# Part of: 26.5.0

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d52fd86275bf"
down_revision = "a1b2c3d4e5f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "deployment_revisions",
        sa.Column(
            "vfolder_subpath",
            sa.String(length=1024),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("deployment_revisions", "vfolder_subpath")
