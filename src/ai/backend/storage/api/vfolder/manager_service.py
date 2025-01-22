from pathlib import Path, PurePath
from typing import Protocol

from ai.backend.common.types import BinarySize
from ai.backend.storage.api.vfolder.types import (
    QuotaConfigModel,
    QuotaIDModel,
    QuotaScopeInfoModel,
    VFolderCloneModel,
    VFolderIDModel,
    VFolderInfoModel,
    VFolderInfoRequestModel,
    VolumeIDModel,
    VolumeInfoListModel,
    VolumeInfoModel,
)
from ai.backend.storage.types import CapacityUsage, TreeUsage


class VFolderServiceProtocol(Protocol):
    async def get_volume(self, volume_data: VolumeIDModel) -> VolumeInfoModel:
        """by volume_id"""
        ...

    async def get_volumes(self) -> VolumeInfoListModel: ...

    async def create_quota_scope(self, quota_config_data: QuotaConfigModel) -> None: ...

    async def get_quota_scope(self, quota_data: QuotaIDModel) -> QuotaScopeInfoModel: ...

    async def update_quota_scope(self, quota_config_data: QuotaConfigModel) -> None: ...

    async def delete_quota_scope(self, quota_data: QuotaIDModel) -> None:
        """Previous: unset_quota"""
        ...

    async def create_vfolder(self, vfolder_data: VFolderIDModel) -> None: ...

    async def clone_vfolder(self, vfolder_clone_data: VFolderCloneModel) -> None: ...

    async def get_vfolder_info(self, vfolder_info: VFolderInfoRequestModel) -> VFolderInfoModel:
        # Integration: vfolder_mount, metadata, vfolder_usage, vfolder_used_bytes, vfolder_fs_usage
        ...

    async def delete_vfolder(self, vfolder_data: VFolderIDModel) -> None: ...


class VFolderService:
    async def get_volume(self, volume_data: VolumeIDModel) -> VolumeInfoModel:
        return VolumeInfoModel(
            volume_id=volume_data.volume_id,
            backend="default-backend",
            path=Path("/default/path"),
            fsprefix=PurePath("/fsprefix"),
            capabilities=["read", "write"],
            options={"option1": "value1"},
        )

    async def get_volumes(self) -> VolumeInfoListModel:
        return VolumeInfoListModel(volumes={})

    async def create_quota_scope(self, quota_config_data: QuotaConfigModel) -> None:
        return None

    async def get_quota_scope(self, quota_data: QuotaIDModel) -> QuotaScopeInfoModel:
        return QuotaScopeInfoModel(used_bytes=0, limit_bytes=0)

    async def update_quota_scope(self, quota_config_data: QuotaConfigModel) -> None:
        return None

    async def delete_quota_scope(self, quota_data: QuotaIDModel) -> None:
        return None

    async def create_vfolder(self, vfolder_data: VFolderIDModel) -> None:
        return None

    async def clone_vfolder(self, vfolder_clone_data: VFolderCloneModel) -> None:
        return None

    async def get_vfolder_info(self, vfolder_info: VFolderInfoRequestModel) -> VFolderInfoModel:
        return VFolderInfoModel(
            vfolder_mount=Path("/mount/point"),
            vfolder_metadata=b"",
            vfolder_usage=TreeUsage(file_count=0, used_bytes=0),
            vfolder_used_bytes=BinarySize(0),
            vfolder_fs_usage=CapacityUsage(used_bytes=0, capacity_bytes=0),
        )

    async def delete_vfolder(self, vfolder_data: VFolderIDModel) -> None:
        return None
