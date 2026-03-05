"""make_deployment_revision_model_not_null

Revision ID: c4602c3d4f1d
Revises: 3f5c20f7bb07
Create Date: 2026-03-05 08:08:11.357370

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c4602c3d4f1d"
down_revision = "3f5c20f7bb07"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Delete revisions with NULL model (vfolder_id) as they are invalid data.
    # A deployment revision without a model vfolder reference cannot function.
    op.execute("DELETE FROM deployment_revisions WHERE model IS NULL")
    op.alter_column(
        "deployment_revisions",
        "model",
        existing_type=sa.dialects.postgresql.UUID(),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "deployment_revisions",
        "model",
        existing_type=sa.dialects.postgresql.UUID(),
        nullable=True,
    )
