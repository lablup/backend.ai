from typing import Protocol

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam, api_handler
from ai.backend.common.dto.storage.request import (
    QuotaScopeKeyDataParams,
    VFolderKeyDataParams,
    VolumeKeyDataParams,
)
from ai.backend.common.dto.storage.response import (
    GetVolumeResponse,
    QuotaScopeResponse,
    VFolderFSUsageResponse,
    VFolderMetadataResponse,
    VFolderMountResponse,
    VFolderUsageResponse,
    VFolderUsedBytesResponse,
    VolumeMetadataResponse,
)
from ai.backend.storage.volumes.types import (
    NewQuotaScopeCreated,
    NewVFolderCreated,
    QuotaScopeKeyData,
    QuotaScopeMetadata,
    VFolderKeyData,
    VFolderMetadata,
    VolumeKeyData,
    VolumeMetadata,
    VolumeMetadataList,
)


class VFolderServiceProtocol(Protocol):
    async def get_volume(self, volume_data: VolumeKeyData) -> VolumeMetadata: ...

    async def get_volumes(self) -> VolumeMetadataList: ...

    async def create_quota_scope(self, quota_data: QuotaScopeKeyData) -> NewQuotaScopeCreated: ...

    async def get_quota_scope(self, quota_data: QuotaScopeKeyData) -> QuotaScopeMetadata: ...

    async def update_quota_scope(self, quota_data: QuotaScopeKeyData) -> None: ...

    async def delete_quota_scope(self, quota_data: QuotaScopeKeyData) -> None: ...

    async def create_vfolder(self, vfolder_data: VFolderKeyData) -> NewVFolderCreated: ...

    async def clone_vfolder(self, vfolder_data: VFolderKeyData) -> NewVFolderCreated: ...

    async def get_vfolder_info(self, vfolder_data: VFolderKeyData) -> VFolderMetadata: ...

    async def delete_vfolder(self, vfolder_data: VFolderKeyData) -> None: ...


class VFolderHandler:
    def __init__(self, storage_service: VFolderServiceProtocol) -> None:
        self.storage_service = storage_service

    @api_handler
    async def get_volume(self, body: PathParam[VolumeKeyDataParams]) -> APIResponse:
        volume_parsed = body.parsed
        volume_params = VolumeKeyData(volume_id=volume_parsed.volume_id)
        volume_data = await self.storage_service.get_volume(volume_params)
        return APIResponse.build(
            status_code=200,
            response_model=VolumeMetadataResponse(
                volume_id=str(volume_data.volume_id),
                backend=volume_data.backend,
                path=str(volume_data.path),
                fsprefix=str(volume_data.fsprefix) if volume_data.fsprefix else None,
                capabilities=[cap for cap in volume_data.capabilities],
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
                        backend=volume.backend,
                        path=str(volume.path),
                        fsprefix=str(volume.fsprefix) if volume.fsprefix else None,
                        capabilities=[cap for cap in volume.capabilities],
                    )
                    for volume in volumes_data.volumes
                ]
            ),
        )

    @api_handler
    async def create_quota_scope(self, body: BodyParam[QuotaScopeKeyDataParams]) -> APIResponse:
        quota_parsed = body.parsed
        quota_params = QuotaScopeKeyData(
            volume_id=quota_parsed.volume_id,
            quota_scope_id=quota_parsed.quota_scope_id,
            options=quota_parsed.options,
        )
        await self.storage_service.create_quota_scope(quota_params)
        return APIResponse.no_content(status_code=201)

    @api_handler
    async def get_quota_scope(self, body: PathParam[QuotaScopeKeyDataParams]) -> APIResponse:
        quota_parsed = body.parsed
        quota_params = QuotaScopeKeyData(
            volume_id=quota_parsed.volume_id,
            quota_scope_id=quota_parsed.quota_scope_id,
        )
        quota_scope = await self.storage_service.get_quota_scope(quota_params)
        return APIResponse.build(
            status_code=200,
            response_model=QuotaScopeResponse(
                used_bytes=quota_scope.used_bytes, limit_bytes=quota_scope.limit_bytes
            ),
        )

    @api_handler
    async def update_quota_scope(self, body: BodyParam[QuotaScopeKeyDataParams]) -> APIResponse:
        quota_parsed = body.parsed
        quota_params = QuotaScopeKeyData(
            volume_id=quota_parsed.volume_id,
            quota_scope_id=quota_parsed.quota_scope_id,
            options=quota_parsed.options,
        )
        await self.storage_service.update_quota_scope(quota_params)
        return APIResponse.no_content(status_code=204)

    @api_handler
    async def delete_quota_scope(self, body: PathParam[QuotaScopeKeyDataParams]) -> APIResponse:
        quota_parsed = body.parsed
        quota_params = QuotaScopeKeyData(
            volume_id=quota_parsed.volume_id,
            quota_scope_id=quota_parsed.quota_scope_id,
        )
        await self.storage_service.delete_quota_scope(quota_params)
        return APIResponse.no_content(status_code=204)

    @api_handler
    async def create_vfolder(self, body: BodyParam[VFolderKeyDataParams]) -> APIResponse:
        vfolder_parsed = body.parsed
        vfolder_params = VFolderKeyData(
            volume_id=vfolder_parsed.volume_id,
            vfolder_id=vfolder_parsed.vfolder_id,
        )
        await self.storage_service.create_vfolder(vfolder_params)
        return APIResponse.no_content(status_code=201)

    @api_handler
    async def clone_vfolder(self, body: BodyParam[VFolderKeyDataParams]) -> APIResponse:
        vfolder_parsed = body.parsed
        vfolder_params = VFolderKeyData(
            volume_id=vfolder_parsed.volume_id,
            vfolder_id=vfolder_parsed.vfolder_id,
            dst_vfolder_id=vfolder_parsed.dst_vfolder_id,
        )
        await self.storage_service.clone_vfolder(vfolder_params)
        return APIResponse.no_content(status_code=201)

    @api_handler
    async def get_vfolder_info(self, body: PathParam[VFolderKeyDataParams]) -> APIResponse:
        vfolder_parsed = body.parsed
        vfolder_params = VFolderKeyData(
            volume_id=vfolder_parsed.volume_id,
            vfolder_id=vfolder_parsed.vfolder_id,
            subpath=vfolder_parsed.subpath,
        )
        metadata = await self.storage_service.get_vfolder_info(vfolder_params)
        return APIResponse.build(
            status_code=200,
            response_model=VFolderMetadataResponse(
                mount_path=str(metadata.mount_path),
                file_count=metadata.file_count,
                used_bytes=metadata.used_bytes,
                capacity_bytes=metadata.capacity_bytes,
                fs_used_bytes=metadata.fs_used_bytes,
            ),
        )

    @api_handler
    async def get_vfolder_mount(self, body: PathParam[VFolderKeyDataParams]) -> APIResponse:
        vfolder_parsed = body.parsed
        vfolder_params = VFolderKeyData(
            volume_id=vfolder_parsed.volume_id,
            vfolder_id=vfolder_parsed.vfolder_id,
            subpath=vfolder_parsed.subpath,
        )
        metadata = await self.storage_service.get_vfolder_info(vfolder_params)
        return APIResponse.build(
            status_code=200,
            response_model=VFolderMountResponse(mount_path=str(metadata.mount_path)),
        )

    @api_handler
    async def get_vfolder_usage(self, body: PathParam[VFolderKeyDataParams]) -> APIResponse:
        vfolder_parsed = body.parsed
        vfolder_params = VFolderKeyData(
            volume_id=vfolder_parsed.volume_id,
            vfolder_id=vfolder_parsed.vfolder_id,
        )
        metadata = await self.storage_service.get_vfolder_info(vfolder_params)
        return APIResponse.build(
            status_code=200,
            response_model=VFolderUsageResponse(
                file_count=metadata.file_count, used_bytes=metadata.used_bytes
            ),
        )

    @api_handler
    async def get_vfolder_used_bytes(self, body: PathParam[VFolderKeyDataParams]) -> APIResponse:
        vfolder_parsed = body.parsed
        vfolder_params = VFolderKeyData(
            volume_id=vfolder_parsed.volume_id,
            vfolder_id=vfolder_parsed.vfolder_id,
        )
        metadata = await self.storage_service.get_vfolder_info(vfolder_params)
        return APIResponse.build(
            status_code=200,
            response_model=VFolderUsedBytesResponse(used_bytes=metadata.used_bytes),
        )

    @api_handler
    async def get_vfolder_fs_usage(self, body: PathParam[VFolderKeyDataParams]) -> APIResponse:
        vfolder_parsed = body.parsed
        vfolder_params = VFolderKeyData(
            volume_id=vfolder_parsed.volume_id,
            vfolder_id=vfolder_parsed.vfolder_id,
        )
        metadata = await self.storage_service.get_vfolder_info(vfolder_params)
        return APIResponse.build(
            status_code=200,
            response_model=VFolderFSUsageResponse(
                capacity_bytes=metadata.capacity_bytes,
                fs_used_bytes=metadata.fs_used_bytes,
            ),
        )

    @api_handler
    async def delete_vfolder(self, body: PathParam[VFolderKeyDataParams]) -> APIResponse:
        vfolder_parsed = body.parsed
        vfolder_params = VFolderKeyData(
            volume_id=vfolder_parsed.volume_id,
            vfolder_id=vfolder_parsed.vfolder_id,
        )
        await self.storage_service.delete_vfolder(vfolder_params)
        return APIResponse.no_content(status_code=202)
