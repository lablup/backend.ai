"""The kernel group's resolved vfolder mounts, one row per mount destination."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.kernel_group import KernelGroupID
from ai.backend.common.data.entity.kernel_group_vfolder_mount import KernelGroupVFolderMountID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.types import MountPermission
from ai.backend.manager.models.base import GUID, Base, StrEnumType

__all__ = ("KernelGroupVFolderMountRow",)


class KernelGroupVFolderMountRow(Base):
    """Per-group vfolder mount, unique on (kernel_group_id, mount_destination)."""

    __tablename__ = "kernel_group_vfolder_mounts"
    __table_args__ = (sa.UniqueConstraint("kernel_group_id", "mount_destination"),)

    id: Mapped[KernelGroupVFolderMountID] = mapped_column(
        "id",
        GUID(KernelGroupVFolderMountID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    kernel_group_id: Mapped[KernelGroupID] = mapped_column(
        "kernel_group_id",
        GUID(KernelGroupID),
        sa.ForeignKey("kernel_groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    # `use_alter` keeps the FK out of the CREATE TABLE so table subsets that omit
    # ``vfolders`` still build.
    vfolder_id: Mapped[VFolderUUID] = mapped_column(
        "vfolder_id",
        GUID(VFolderUUID),
        sa.ForeignKey(
            "vfolders.id",
            ondelete="CASCADE",
            use_alter=True,
            name="fk_kernel_group_vfolder_mounts_vfolder_id_vfolders",
        ),
        nullable=False,
        index=True,
    )
    vfsubpath: Mapped[str] = mapped_column("vfsubpath", sa.Text, nullable=False)
    mount_destination: Mapped[str] = mapped_column("mount_destination", sa.Text, nullable=False)
    mount_perm: Mapped[MountPermission] = mapped_column(
        "mount_perm", StrEnumType(MountPermission), nullable=False
    )
