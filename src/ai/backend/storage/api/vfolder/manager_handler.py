from typing import Protocol

from aiohttp import web

from ai.backend.storage.api.vfolder.response_model import (
    GetVolumeResponseModel,
    NoContentResponseModel,
    ProcessingResponseModel,
    QuotaScopeResponseModel,
    VFolderMetadataResponseModel,
    VolumeMetadataResponseModel,
)
from ai.backend.storage.api.vfolder.types import (
    QuotaScopeIDModel,
    QuotaScopeMetadataModel,
    VFolderIDModel,
    VFolderMetadataModel,
    VolumeIDModel,
    VolumeMetadataListModel,
)


class VFolderServiceProtocol(Protocol):
    async def get_volume(self, volume_data: VolumeIDModel) -> VolumeMetadataListModel:
        """by volume_id"""
        ...

    async def get_volumes(self) -> VolumeMetadataListModel: ...

    async def create_quota_scope(self, quota_data: QuotaScopeIDModel) -> None: ...

    async def get_quota_scope(self, quota_data: QuotaScopeIDModel) -> QuotaScopeMetadataModel: ...

    async def update_quota_scope(self, quota_data: QuotaScopeIDModel) -> None: ...

    async def delete_quota_scope(self, quota_data: QuotaScopeIDModel) -> None:
        """Previous: unset_quota"""
        ...

    async def create_vfolder(self, vfolder_data: VFolderIDModel) -> VFolderIDModel: ...

    async def clone_vfolder(self, vfolder_data: VFolderIDModel) -> None: ...

    async def get_vfolder_info(self, vfolder_data: VFolderIDModel) -> VFolderMetadataModel:
        # Integration: vfolder_mount, metadata, vfolder_usage, vfolder_used_bytes, vfolder_fs_usage
        ...

    async def delete_vfolder(self, vfolder_data: VFolderIDModel) -> VFolderIDModel: ...


class VFolderHandler:
    def __init__(self, storage_service: VFolderServiceProtocol) -> None:
        self.storage_service = storage_service

    async def get_volume(self, request: web.Request) -> GetVolumeResponseModel:
        data = await request.json()
        params = VolumeIDModel(volume_id=data["volume_id"])
        volume_data = await self.storage_service.get_volume(params)
        return GetVolumeResponseModel(
            volumes=[
                VolumeMetadataResponseModel(
                    volume_id=str(volume.volume_id),
                    backend=str(volume.backend),
                    path=str(volume.path),
                    fsprefix=str(volume.fsprefix) if volume.fsprefix else None,
                    capabilities=[str(cap) for cap in volume.capabilities],
                )
                for volume in volume_data.volumes
            ]
        )

    async def get_volumes(self, request: web.Request) -> GetVolumeResponseModel:
        volumes_data = await self.storage_service.get_volumes()
        return GetVolumeResponseModel(
            volumes=[
                VolumeMetadataResponseModel(
                    volume_id=str(volume.volume_id),
                    backend=str(volume.backend),
                    path=str(volume.path),
                    fsprefix=str(volume.fsprefix) if volume.fsprefix else None,
                    capabilities=[str(cap) for cap in volume.capabilities],
                )
                for volume in volumes_data.volumes
            ]
        )

    async def create_quota_scope(self, request: web.Request) -> NoContentResponseModel:
        data = await request.json()
        params = QuotaScopeIDModel(
            volume_id=data["volume_id"],
            quota_scope_id=data["quota_scope_id"],
            options=data.get("options"),
        )
        await self.storage_service.create_quota_scope(params)
        return NoContentResponseModel()

    async def get_quota_scope(self, request: web.Request) -> QuotaScopeResponseModel:
        data = await request.json()
        params = QuotaScopeIDModel(
            volume_id=data["volume_id"], quota_scope_id=data["quota_scope_id"]
        )
        quota_scope = await self.storage_service.get_quota_scope(params)
        return QuotaScopeResponseModel(
            used_bytes=quota_scope.used_bytes, limit_bytes=quota_scope.limit_bytes
        )

    async def update_quota_scope(self, request: web.Request) -> NoContentResponseModel:
        data = await request.json()
        params = QuotaScopeIDModel(
            volume_id=data["volume_id"],
            quota_scope_id=data["quota_scope_id"],
            options=data.get("options"),
        )
        await self.storage_service.update_quota_scope(params)
        return NoContentResponseModel()

    async def delete_quota_scope(self, request: web.Request) -> NoContentResponseModel:
        data = await request.json()
        params = QuotaScopeIDModel(
            volume_id=data["volume_id"], quota_scope_id=data["quota_scope_id"]
        )
        await self.storage_service.delete_quota_scope(params)
        return NoContentResponseModel()

    async def create_vfolder(self, request: web.Request) -> NoContentResponseModel:
        data = await request.json()
        params = VFolderIDModel(volume_id=data["volume_id"], vfolder_id=data["vfolder_id"])
        await self.storage_service.create_vfolder(params)
        return NoContentResponseModel()

    async def clone_vfolder(self, request: web.Request) -> NoContentResponseModel:
        data = await request.json()
        params = VFolderIDModel(
            volume_id=data["volume_id"],
            vfolder_id=data["vfolder_id"],
            dst_vfolder_id=data["dst_vfolder_id"],
        )
        await self.storage_service.clone_vfolder(params)
        return NoContentResponseModel()

    async def get_vfolder_info(self, request: web.Request) -> VFolderMetadataResponseModel:
        data = await request.json()
        params = VFolderIDModel(**data)
        metadata = await self.storage_service.get_vfolder_info(params)
        return VFolderMetadataResponseModel(
            mount_path=str(metadata.mount_path),
            file_count=metadata.file_count,
            capacity_bytes=metadata.capacity_bytes,
            used_bytes=metadata.used_bytes,
        )

    async def delete_vfolder(self, request: web.Request) -> ProcessingResponseModel:
        data = await request.json()
        params = VFolderIDModel(volume_id=data["volume_id"], vfolder_id=data["vfolder_id"])
        await self.storage_service.delete_vfolder(params)
        return ProcessingResponseModel()
