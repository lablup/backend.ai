"""Add digest to artifact_revisions

Revision ID: 5a5142f6d251
Revises: d811b103dbfc
Create Date: 2025-10-31 03:54:59.846269

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5a5142f6d251"
down_revision = "d811b103dbfc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("artifact_revisions", sa.Column("digest", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("artifact_revisions", "digest")
