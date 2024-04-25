"""Migrate vfolder_permissions to vfolders

Revision ID: d5aa9a6a90a3
Revises: dddf9be580f5
Create Date: 2024-04-22 04:44:01.999156

"""

import enum
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql

from ai.backend.manager.models.base import (
    GUID,
    EnumValueType,
    IDColumn,
    QuotaScopeIDType,
    StrEnumType,
    metadata,
)
from ai.backend.manager.models.view_utils import CreateView, DropView

# revision identifiers, used by Alembic.
revision = "d5aa9a6a90a3"
down_revision = "dddf9be580f5"
branch_labels = None
depends_on = None


class VFolderOperationStatus(enum.StrEnum):
    """
    Introduce virtual folder current status for storage-proxy operations.
    """

    READY = "ready"
    PERFORMING = "performing"
    CLONING = "cloning"
    MOUNTED = "mounted"
    ERROR = "error"

    DELETE_PENDING = "delete-pending"  # vfolder is in trash bin
    DELETE_ONGOING = "delete-ongoing"  # vfolder is being deleted in storage
    DELETE_COMPLETE = "delete-complete"  # vfolder is deleted permanentyl, only DB row remains
    DELETE_ERROR = "delete-error"


class VFolderOwnershipType(enum.StrEnum):
    """
    Ownership type of virtual folder.
    """

    USER = "user"
    GROUP = "group"


class VFolderUsageMode(enum.StrEnum):
    """
    Usage mode of virtual folder.

    GENERAL: normal virtual folder
    MODEL: virtual folder which provides shared models
    DATA: virtual folder which provides shared data
    """

    GENERAL = "general"
    MODEL = "model"
    DATA = "data"


class VFolderPermission(enum.StrEnum):
    """
    Permissions for a virtual folder given to a specific access key.
    RW_DELETE includes READ_WRITE and READ_WRITE includes READ_ONLY.
    """

    READ_ONLY = "ro"
    READ_WRITE = "rw"
    RW_DELETE = "wd"
    OWNER_PERM = "wd"  # resolved as RW_DELETE


def get_vfolder_schema():
    vfolders = sa.Table(
        "vfolders",
        metadata,
        IDColumn("id"),
        sa.Column(
            "reference_id", GUID, nullable=True, index=True
        ),  # Used if the vfolder is invited/shared. null when it is not invited/shared
        # host will be '' if vFolder is unmanaged
        sa.Column("host", sa.String(length=128), nullable=False, index=True),
        sa.Column("quota_scope_id", QuotaScopeIDType, nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False, index=True),
        sa.Column(
            "usage_mode",
            EnumValueType(VFolderUsageMode),
            default=VFolderUsageMode.GENERAL,
            nullable=False,
            index=True,
        ),
        sa.Column(
            "permission", EnumValueType(VFolderPermission), default=VFolderPermission.READ_WRITE
        ),
        sa.Column("max_files", sa.Integer(), default=1000),
        sa.Column("max_size", sa.Integer(), default=None),  # in MBytes
        sa.Column("num_files", sa.Integer(), default=0),
        sa.Column("cur_size", sa.Integer(), default=0),  # in KBytes
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_used", sa.DateTime(timezone=True), nullable=True),
        # creator is always set to the user who created vfolder (regardless user/project types)
        sa.Column("creator", sa.String(length=128), nullable=True),
        # unmanaged vfolder represents the host-side absolute path instead of storage-based path.
        sa.Column("unmanaged_path", sa.String(length=512), nullable=True),
        sa.Column(
            "ownership_type",
            EnumValueType(VFolderOwnershipType),
            default=VFolderOwnershipType.USER,
            nullable=False,
            index=True,
        ),
        sa.Column(
            "user", GUID, sa.ForeignKey("users.uuid"), nullable=True
        ),  # owner if user vfolder
        sa.Column(
            "group", GUID, sa.ForeignKey("groups.id"), nullable=True
        ),  # owner if project vfolder
        sa.Column("cloneable", sa.Boolean, default=False, nullable=False),
        sa.Column(
            "status",
            StrEnumType(VFolderOperationStatus),
            default=VFolderOperationStatus.READY,
            server_default=VFolderOperationStatus.READY,
            nullable=False,
            index=True,
        ),
        # status_history records the most recent status changes for each status
        # e.g)
        # {
        #   "ready": "2022-10-22T10:22:30",
        #   "delete-pending": "2022-10-22T11:40:30",
        #   "delete-ongoing": "2022-10-25T10:22:30"
        # }
        sa.Column("status_history", pgsql.JSONB(), nullable=True, default=sa.null()),
        sa.Column("status_changed", sa.DateTime(timezone=True), nullable=True, index=True),
        sa.CheckConstraint(
            "(ownership_type = 'user' AND \"user\" IS NOT NULL) OR "
            "(ownership_type = 'group' AND \"group\" IS NOT NULL)",
            name="ownership_type_match_with_user_or_group",
        ),
        sa.CheckConstraint(
            '("user" IS NULL AND "group" IS NOT NULL) OR ("user" IS NOT NULL AND "group" IS NULL)',
            name="either_one_of_user_or_group",
        ),
        extend_existing=True,
    )
    return vfolders


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
    vfolders = get_vfolder_schema()
    vfolder_permission_records = db_connection.execute(sa.select(vfolder_permissions)).fetchall()

    op.drop_table("vfolder_permissions")
    op.add_column("vfolders", sa.Column("reference_id", GUID(), nullable=True))
    op.create_index(op.f("ix_vfolders_reference_id"), "vfolders", ["reference_id"], unique=False)
    op.drop_constraint("either_one_of_user_or_group", "vfolders", type_="check")

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

    op.execute(
        CreateView(
            "shared_vfolders_view", sa.select(vfolders).where(vfolders.c.reference_id.isnot(None))
        )
    )


def downgrade():
    db_connection = op.get_bind()
    vfolders = get_vfolder_schema()
    shared_vfolders_records = db_connection.execute(
        sa.select(vfolders).where(vfolders.c.reference_id.isnot(None))
    ).fetchall()
    db_connection.execute(sa.delete(vfolders).where(vfolders.c.reference_id.isnot(None)))
    op.execute(DropView("shared_vfolders_view"))

    op.drop_index(op.f("ix_vfolders_reference_id"), table_name="vfolders")
    op.drop_column("vfolders", "reference_id")
    op.create_check_constraint(
        "either_one_of_user_or_group",
        "vfolders",
        '("user" IS NULL AND "group" IS NOT NULL) OR ("user" IS NOT NULL AND "group" IS NULL)',
    )
    op.create_table(
        "vfolder_permissions",
        sa.Column(
            "permission",
            StrEnumType(VFolderPermission),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("vfolder", pgsql.UUID(), autoincrement=False, nullable=False),
        sa.Column("user", pgsql.UUID(), autoincrement=False, nullable=False),
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
