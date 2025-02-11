from typing import Protocol

from ai.backend.common.api_handlers import APIResponse, BodyParam, api_handler
from ai.backend.storage.api.vfolder.response_model import (
    GetVolumeResponse,
    QuotaScopeResponse,
    VFolderMetadataResponse,
    VolumeMetadataResponse,
)
from ai.backend.storage.api.vfolder.types import (
    QuotaScopeIdData,
    QuotaScopeMetadata,
    VFolderIdData,
    VFolderMetadata,
    VolumeIdData,
    VolumeMetadataList,
)


class VFolderServiceProtocol(Protocol):
    async def get_volume(self, volume_data: VolumeIdData) -> VolumeMetadataList: ...

    async def get_volumes(self) -> VolumeMetadataList: ...

    async def create_quota_scope(self, quota_data: QuotaScopeIdData) -> None: ...

    async def get_quota_scope(self, quota_data: QuotaScopeIdData) -> QuotaScopeMetadata: ...

    async def update_quota_scope(self, quota_data: QuotaScopeIdData) -> None: ...

    async def delete_quota_scope(self, quota_data: QuotaScopeIdData) -> None: ...

    async def create_vfolder(self, vfolder_data: VFolderIdData) -> VFolderIdData: ...

    async def clone_vfolder(self, vfolder_data: VFolderIdData) -> None: ...

    async def get_vfolder_info(self, vfolder_data: VFolderIdData) -> VFolderMetadata: ...

    async def delete_vfolder(self, vfolder_data: VFolderIdData) -> VFolderIdData: ...


class VFolderHandler:
    def __init__(self, storage_service: VFolderServiceProtocol) -> None:
        self.storage_service = storage_service

    @api_handler
    async def get_volume(self, body: BodyParam[VolumeIdData]) -> APIResponse:
        volume_params = body.parsed
        volume_data = await self.storage_service.get_volume(volume_params)
        return APIResponse.build(
            status_code=200,
            response_model=GetVolumeResponse(
                volumes=[
                    VolumeMetadataResponse(
                        volume_id=str(volume.volume_id),
                        backend=str(volume.backend),
                        path=str(volume.path),
                        fsprefix=str(volume.fsprefix) if volume.fsprefix else None,
                        capabilities=[str(cap) for cap in volume.capabilities],
                    )
                    for volume in volume_data.volumes
                ]
            ),
        )

    @api_handler
    async def get_volumes(self) -> APIResponse:
        volumes_data = await self.storage_service.get_volumes()
        return APIResponse.build(
            status_code=200,
            response_model=GetVolumeResponse(
                volumes=[
                    VolumeMetadataResponse(
                        volume_id=str(volume.volume_id),
                        backend=str(volume.backend),
                        path=str(volume.path),
                        fsprefix=str(volume.fsprefix) if volume.fsprefix else None,
                        capabilities=[str(cap) for cap in volume.capabilities],
                    )
                    for volume in volumes_data.volumes
                ]
            ),
        )

    @api_handler
    async def create_quota_scope(self, body: BodyParam[QuotaScopeIdData]) -> APIResponse:
        quota_params = body.parsed
        await self.storage_service.create_quota_scope(quota_params)
        return APIResponse.no_content(status_code=201)

    @api_handler
    async def get_quota_scope(self, body: BodyParam[QuotaScopeIdData]) -> APIResponse:
        quota_params = body.parsed
        quota_scope = await self.storage_service.get_quota_scope(quota_params)
        return APIResponse.build(
            status_code=204,
            response_model=QuotaScopeResponse(
                used_bytes=quota_scope.used_bytes, limit_bytes=quota_scope.limit_bytes
            ),
        )

    @api_handler
    async def update_quota_scope(self, body: BodyParam[QuotaScopeIdData]) -> APIResponse:
        quota_params = body.parsed
        await self.storage_service.update_quota_scope(quota_params)
        return APIResponse.no_content(status_code=204)

    @api_handler
    async def delete_quota_scope(self, body: BodyParam[QuotaScopeIdData]) -> APIResponse:
        quota_params = body.parsed
        await self.storage_service.delete_quota_scope(quota_params)
        return APIResponse.no_content(status_code=204)

    @api_handler
    async def create_vfolder(self, body: BodyParam[VFolderIdData]) -> APIResponse:
        vfolder_params = body.parsed
        await self.storage_service.create_vfolder(vfolder_params)
        return APIResponse.no_content(status_code=201)

    @api_handler
    async def clone_vfolder(self, body: BodyParam[VFolderIdData]) -> APIResponse:
        vfolder_params = body.parsed
        await self.storage_service.clone_vfolder(vfolder_params)
        return APIResponse.no_content(status_code=204)

    @api_handler
    async def get_vfolder_info(self, body: BodyParam[VFolderIdData]) -> APIResponse:
        vfolder_params = body.parsed
        metadata = await self.storage_service.get_vfolder_info(vfolder_params)
        return APIResponse.build(
            status_code=200,
            response_model=VFolderMetadataResponse(
                mount_path=str(metadata.mount_path),
                file_count=metadata.file_count,
                capacity_bytes=metadata.capacity_bytes,
                used_bytes=metadata.used_bytes,
            ),
        )

    @api_handler
    async def delete_vfolder(self, body: BodyParam[VFolderIdData]) -> APIResponse:
        vfolder_params = body.parsed
        await self.storage_service.delete_vfolder(vfolder_params)
        return APIResponse.no_content(status_code=202)
