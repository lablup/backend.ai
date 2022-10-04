"""fix invalid vfolderstatus enum

Revision ID: 537cf8c348a4
Revises: 360af8f33d4e
Create Date: 2022-10-04 14:51:51.285128

"""
import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import EnumValueType
from ai.backend.manager.models.vfolder import VFolderOperationStatus

# revision identifiers, used by Alembic.
revision = "537cf8c348a4"
down_revision = "360af8f33d4e"
branch_labels = None
depends_on = None

vfolderstatus_choices = [v.value for v in VFolderOperationStatus]


def upgrade():
    op.alter_column(
        "vfolders",
        "status",
        type_=EnumValueType(VFolderOperationStatus, name="vfolderstatus"),
    )


def downgrade():
    op.alter_column(
        "vfolders",
        "status",
        type_=sa.Enum(*vfolderstatus_choices, name="vfolderstatus"),
    )
