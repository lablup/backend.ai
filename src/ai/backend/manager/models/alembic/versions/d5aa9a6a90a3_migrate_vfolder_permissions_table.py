"""Migrate vfolder_permissions to vfolders

Revision ID: d5aa9a6a90a3
Revises: 857b763b8618
Create Date: 2024-04-22 04:44:01.999156

"""

import enum
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from ai.backend.manager.models.base import GUID, EnumValueType, StrEnumType, metadata
from ai.backend.manager.models.vfolder import vfolders

# revision identifiers, used by Alembic.
revision = "d5aa9a6a90a3"
down_revision = "857b763b8618"
branch_labels = None
depends_on = None


class VFolderPermission(enum.StrEnum):
    """
    Permissions for a virtual folder given to a specific access key.
    RW_DELETE includes READ_WRITE and READ_WRITE includes READ_ONLY.
    """

    READ_ONLY = "ro"
    READ_WRITE = "rw"
    RW_DELETE = "wd"
    OWNER_PERM = "wd"  # resolved as RW_DELETE


def get_vfolder_permissions_schema():
    vfolder_permissions = sa.Table(
        "vfolder_permissions",
        metadata,
        sa.Column(
            "permission", EnumValueType(VFolderPermission), default=VFolderPermission.READ_WRITE
        ),
        sa.Column(
            "vfolder",
            GUID,
            sa.ForeignKey("vfolders.id", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user", GUID, sa.ForeignKey("users.uuid"), nullable=False),
        extend_existing=True,
    )
    return vfolder_permissions


def upgrade():
    db_connection = op.get_bind()
    vfolder_permissions = get_vfolder_permissions_schema()
    vfolder_permission_records = db_connection.execute(sa.select(vfolder_permissions)).fetchall()

    op.drop_table("vfolder_permissions")
    op.add_column("vfolders", sa.Column("reference_id", GUID(), nullable=True))
    op.create_index(op.f("ix_vfolders_reference_id"), "vfolders", ["reference_id"], unique=False)

    for vfolder_permission_record in vfolder_permission_records:
        original_vfolder = db_connection.execute(
            sa.select(vfolders).where(vfolders.c.id == vfolder_permission_record["vfolder"])
        ).fetchone()
        shared_vfolder = {k: v for k, v in dict(original_vfolder).items() if v is not None}
        shared_vfolder.update({
            "id": uuid.uuid4().hex,
            "reference_id": vfolder_permission_record["vfolder"],
            "permission": vfolder_permission_record["permission"],
            "user": vfolder_permission_record["user"],
        })

        db_connection.execute(sa.insert(vfolders, shared_vfolder))


def downgrade():
    db_connection = op.get_bind()
    shared_vfolders_records = db_connection.execute(
        sa.select(vfolders).where(vfolders.c.reference_id.isnot(None))
    ).fetchall()
    db_connection.execute(sa.delete(vfolders).where(vfolders.c.reference_id.isnot(None)))

    op.drop_index(op.f("ix_vfolders_reference_id"), table_name="vfolders")

    op.drop_column("vfolders", "reference_id")
    op.create_table(
        "vfolder_permissions",
        sa.Column(
            "permission",
            StrEnumType(VFolderPermission),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("vfolder", postgresql.UUID(), autoincrement=False, nullable=False),
        sa.Column("user", postgresql.UUID(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(["user"], ["users.uuid"], name="fk_vfolder_permissions_user_users"),
        sa.ForeignKeyConstraint(
            ["vfolder"],
            ["vfolders.id"],
            name="fk_vfolder_permissions_vfolder_vfolders",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
    )

    for shared_vfolder in shared_vfolders_records:
        vfolder_perm = {
            "vfolder": shared_vfolder["reference_id"],
            "permission": shared_vfolder["permission"],
            "user": shared_vfolder["user"],
        }

        vfolder_permissions = get_vfolder_permissions_schema()
        db_connection.execute(sa.insert(vfolder_permissions, vfolder_perm))
