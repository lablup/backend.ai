"""add vfolder_permissions id

Revision ID: fdb2dcdb8811
Revises: d7df3baf3779
Create Date: 2024-06-11 16:40:45.267761

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "fdb2dcdb8811"
down_revision = "d7df3baf3779"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "vfolder_permissions",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
    )
    op.create_primary_key("pk_vfolder_permissions", "vfolder_permissions", ["id"])


def downgrade():
    op.drop_constraint("pk_vfolder_permissions", "vfolder_permissions", type_="primary")
    op.drop_column("vfolder_permissions", "id")
