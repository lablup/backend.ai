from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.data.entity.vfolder_auto_mount import VFolderAutoMountID
from ai.backend.common.data.vfolder_auto_mount.types import VFolderAutoMountScopeType
from ai.backend.manager.data.vfolder.types import VFolderMountPermission
from ai.backend.manager.models.base import GUID, Base, StrEnumType
from ai.backend.manager.models.mixins.soft_delete import SoftDeleteMixin
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin


class VFolderAutoMountRow(SoftDeleteMixin, LifecycleTimestampsMixin, Base):
    """A vfolder mounted into every session created in a project; a vfolder and a mount
    destination each appear at most once among the project's live rows."""

    __tablename__ = "vfolder_auto_mounts"
    __table_args__ = (
        # The scope must be provisioned in the graph; a scope torn down takes its
        # auto-mounts with it.
        sa.ForeignKeyConstraint(
            ["scope_type", "scope_id"],
            ["virtual_entities.entity_type", "virtual_entities.entity_id"],
            ondelete="CASCADE",
        ),
        sa.Index(
            "uq_vfolder_auto_mounts_live_vfolder",
            "scope_type",
            "scope_id",
            "vfolder_id",
            unique=True,
            postgresql_where=sa.text("deleted_at IS NULL"),
        ),
        sa.Index(
            "uq_vfolder_auto_mounts_live_destination",
            "scope_type",
            "scope_id",
            "mount_destination",
            unique=True,
            postgresql_where=sa.text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[VFolderAutoMountID] = mapped_column(
        GUID(VFolderAutoMountID), primary_key=True, server_default=sa.text("uuid_generate_v7()")
    )
    scope_type: Mapped[VFolderAutoMountScopeType] = mapped_column(
        StrEnumType(VFolderAutoMountScopeType, length=32), nullable=False
    )
    scope_id: Mapped[UUID] = mapped_column(GUID(), nullable=False)
    vfolder_id: Mapped[VFolderUUID] = mapped_column(
        GUID(VFolderUUID),
        sa.ForeignKey("vfolders.id", ondelete="CASCADE"),
        nullable=False,
    )
    mount_destination: Mapped[str] = mapped_column(sa.Text, nullable=False)
    subpath: Mapped[str] = mapped_column(sa.Text, nullable=False, server_default=".")
    mount_permission: Mapped[VFolderMountPermission] = mapped_column(
        StrEnumType(VFolderMountPermission), nullable=False
    )
