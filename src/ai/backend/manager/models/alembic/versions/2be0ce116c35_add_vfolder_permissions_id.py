"""add_id_to_vfolder_permissions

Revision ID: 2be0ce116c35
Revises: 37410c773b8c
Create Date: 2024-05-11 00:53:28.387238

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "2be0ce116c35"
down_revision = "37410c773b8c"
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
