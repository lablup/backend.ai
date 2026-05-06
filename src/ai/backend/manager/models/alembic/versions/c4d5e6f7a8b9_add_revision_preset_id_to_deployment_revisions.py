"""add revision_preset_id to deployment_revisions

Revision ID: c4d5e6f7a8b9
Revises: ba5923b1f4a7
Create Date: 2026-05-06

Persist the deployment-level preset selection on the revision row so the
preset that produced a revision can be recovered after creation. The
column is nullable because revisions created without a preset (legacy
rows and ad-hoc revisions) carry no preset reference.

A SET NULL FK is used so a preset deletion does not cascade-delete
historical revisions; revisions are retained for history but lose the
preset back-reference.

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
# Part of: 26.4.6 (main)
revision = "c4d5e6f7a8b9"
down_revision = "ba5923b1f4a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "deployment_revisions",
        sa.Column(
            "revision_preset_id",
            GUID,
            sa.ForeignKey("deployment_revision_presets.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("deployment_revisions", "revision_preset_id")
