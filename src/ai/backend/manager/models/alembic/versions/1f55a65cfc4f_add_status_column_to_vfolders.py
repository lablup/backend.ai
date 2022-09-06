"""empty message

Revision ID: 1f55a65cfc4f
Revises: 35923972eddb
Create Date: 2022-09-06 11:25:26.192685

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "1f55a65cfc4f"
down_revision = "35923972eddb"
branch_labels = None
depends_on = None


vfolderstatus = postgresql.ENUM(
    "READY", "PREPARED", "CLONING", "DELETING", "MOUNTED", name="vfolderstatus"
)


def upgrade():
    vfolderstatus.create(op.get_bind())
    op.add_column(
        "vfolders",
        sa.Column(
            "status",
            EnumValueType(VFolderOperationStatus),
            default=VFolderOperationStatus.READY,
            nullable=False,
        ),
    )


def downgrade():
    op.drop_column("vfolders", "status")
    vfolderstatus.drop(op.get_bind())
