from http import HTTPStatus
from typing import Optional, Protocol

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam, api_handler
from ai.backend.common.dto.storage.path import QuotaScopeKeyPath, VFolderKeyPath, VolumeIDPath
from ai.backend.common.dto.storage.request import (
    CloneVFolderReq,
    GetVFolderMetaReq,
    QuotaScopeReq,
)
from ai.backend.common.dto.storage.response import (
    GetVolumeResponse,
    GetVolumesResponse,
    VFolderMetadataResponse,
)
from ai.backend.common.types import QuotaConfig, VFolderID, VolumeID

from ...volumes.types import (
    QuotaScopeKey,
    QuotaScopeMeta,
    VFolderKey,
    VFolderMeta,
    VolumeMeta,
)


class VFolderServiceProtocol(Protocol):
    async def get_volume(self, volume_id: VolumeID) -> VolumeMeta: ...

    async def get_volumes(self) -> list[VolumeMeta]: ...

    async def create_quota_scope(
        self, quota_scope_key: QuotaScopeKey, options: Optional[QuotaConfig]
    ) -> None: ...

    async def get_quota_scope(self, quota_scope_key: QuotaScopeKey) -> QuotaScopeMeta: ...

    async def update_quota_scope(
        self, quota_scope_key: QuotaScopeKey, options: Optional[QuotaConfig]
    ) -> None: ...

    async def delete_quota_scope(self, quota_scope_key: QuotaScopeKey) -> None: ...

    async def create_vfolder(self, vfolder_key: VFolderKey) -> None: ...

    async def clone_vfolder(self, vfolder_key: VFolderKey, dst_vfolder_id: VFolderID) -> None: ...

    async def get_vfolder_info(self, vfolder_key: VFolderKey, subpath: str) -> VFolderMeta: ...

    async def delete_vfolder(self, vfolder_key: VFolderKey) -> None: ...


class VFolderHandler:
    _storage_service: VFolderServiceProtocol

    def __init__(self, storage_service: VFolderServiceProtocol) -> None:
        self._storage_service = storage_service

    @api_handler
    async def get_volume(self, path: PathParam[VolumeIDPath]) -> APIResponse:
        volume_meta = await self._storage_service.get_volume(path.parsed.volume_id)
        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=GetVolumeResponse(
                item=volume_meta.to_field(),
            ),
        )

    @api_handler
    async def get_volumes(self) -> APIResponse:
        volume_meta_list = await self._storage_service.get_volumes()
        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=GetVolumesResponse(
                items=[volume.to_field() for volume in volume_meta_list],
            ),
        )

    @api_handler
    async def create_quota_scope(
        self, path: PathParam[QuotaScopeKeyPath], body: BodyParam[QuotaScopeReq]
    ) -> APIResponse:
        quota_scope_key = QuotaScopeKey.from_quota_scope_path(path.parsed)
        await self._storage_service.create_quota_scope(quota_scope_key, body.parsed.options)
        return APIResponse.no_content(status_code=HTTPStatus.NO_CONTENT)

    @api_handler
    async def get_quota_scope(self, path: PathParam[QuotaScopeKeyPath]) -> APIResponse:
        quota_scope_key = QuotaScopeKey.from_quota_scope_path(path.parsed)
        quota_scope = await self._storage_service.get_quota_scope(quota_scope_key)
        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=quota_scope.to_response(),
        )

    @api_handler
    async def update_quota_scope(
        self, path: PathParam[QuotaScopeKeyPath], body: BodyParam[QuotaScopeReq]
    ) -> APIResponse:
        quota_scope_key = QuotaScopeKey.from_quota_scope_path(path.parsed)
        await self._storage_service.update_quota_scope(quota_scope_key, body.parsed.options)
        return APIResponse.no_content(status_code=HTTPStatus.NO_CONTENT)

    @api_handler
    async def delete_quota_scope(self, path: PathParam[QuotaScopeKeyPath]) -> APIResponse:
        quota_scope_key = QuotaScopeKey.from_quota_scope_path(path.parsed)
        await self._storage_service.delete_quota_scope(quota_scope_key)
        return APIResponse.no_content(status_code=HTTPStatus.NO_CONTENT)

    @api_handler
    async def create_vfolder(self, path: PathParam[VFolderKeyPath]) -> APIResponse:
        vfolder_key = VFolderKey.from_vfolder_path(path.parsed)
        await self._storage_service.create_vfolder(vfolder_key)
        return APIResponse.no_content(status_code=HTTPStatus.NO_CONTENT)

    @api_handler
    async def clone_vfolder(
        self, path: PathParam[VFolderKeyPath], body: BodyParam[CloneVFolderReq]
    ) -> APIResponse:
        vfolder_key = VFolderKey.from_vfolder_path(path.parsed)
        await self._storage_service.clone_vfolder(vfolder_key, body.parsed.dst_vfolder_id)
        return APIResponse.no_content(status_code=HTTPStatus.NO_CONTENT)

    @api_handler
    async def get_vfolder_info(
        self, path: PathParam[VFolderKeyPath], body: BodyParam[GetVFolderMetaReq]
    ) -> APIResponse:
        vfolder_key = VFolderKey.from_vfolder_path(path.parsed)
        vfolder_meta = await self._storage_service.get_vfolder_info(
            vfolder_key, body.parsed.subpath
        )
        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=VFolderMetadataResponse(
                item=vfolder_meta.to_field(),
            ),
        )

    @api_handler
    async def delete_vfolder(self, path: PathParam[VFolderKeyPath]) -> APIResponse:
        vfolder_key = VFolderKey.from_vfolder_path(path.parsed)
        await self._storage_service.delete_vfolder(vfolder_key)
        return APIResponse.no_content(status_code=HTTPStatus.NO_CONTENT)
