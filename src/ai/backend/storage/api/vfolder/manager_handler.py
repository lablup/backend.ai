import uuid

from aiohttp import web

from ai.backend.storage.api.vfolder.manager_service import VFolderService
from ai.backend.storage.api.vfolder.types import (
    QuotaConfigModel,
    QuotaIDModel,
    VFolderCloneModel,
    VFolderIDModel,
    VFolderInfoRequestModel,
    VolumeIDModel,
)


class VFolderHandler:
    def __init__(self, storage_service: VFolderService) -> None:
        self.storage_service = storage_service

    async def get_volume(self, request: web.Request) -> web.Response:
        data = await request.json()
        data["volume_id"] = uuid.UUID(data["volume_id"])
        req = VolumeIDModel(**data)
        result = await self.storage_service.get_volume(req)
        return web.json_response(result)

    async def get_volumes(self, request: web.Request) -> web.Response:
        result = await self.storage_service.get_volumes()
        # Assume that the volume_dict is a dictionary of VolumeInfoModel objects
        volumes_dict = result.volumes
        volumes_dict = {k: v for k, v in volumes_dict.items()}
        return web.json_response(volumes_dict)

    async def create_quota_scope(self, request: web.Request) -> web.Response:
        data = await request.json()
        data["volume_id"] = uuid.UUID(data["volume_id"])
        req = QuotaConfigModel(**data)
        await self.storage_service.create_quota_scope(req)
        return web.Response(status=204)

    async def get_quota_scope(self, request: web.Request) -> web.Response:
        data = await request.json()
        data["volume_id"] = uuid.UUID(data["volume_id"])
        req = QuotaIDModel(**data)
        result = await self.storage_service.get_quota_scope(req)
        return web.json_response(result)

    async def update_quota_scope(self, request: web.Request) -> web.Response:
        data = await request.json()
        data["volume_id"] = uuid.UUID(data["volume_id"])
        req = QuotaConfigModel(**data)
        await self.storage_service.update_quota_scope(req)
        return web.Response(status=204)

    async def delete_quota_scope(self, request: web.Request) -> web.Response:
        data = await request.json()
        data["volume_id"] = uuid.UUID(data["volume_id"])
        req = QuotaIDModel(**data)
        await self.storage_service.delete_quota_scope(req)
        return web.Response(status=204)

    async def create_vfolder(self, request: web.Request) -> web.Response:
        data = await request.json()
        data["volume_id"] = uuid.UUID(data["volume_id"])
        req = VFolderIDModel(**data)
        await self.storage_service.create_vfolder(req)
        return web.Response(status=204)

    async def clone_vfolder(self, request: web.Request) -> web.Response:
        data = await request.json()
        data["volume_id"] = uuid.UUID(data["volume_id"])
        req = VFolderCloneModel(**data)
        await self.storage_service.clone_vfolder(req)
        return web.Response(status=204)

    async def get_vfolder_info(self, request: web.Request) -> web.Response:
        data = await request.json()
        data["volume_id"] = uuid.UUID(data["volume_id"])
        req = VFolderInfoRequestModel(**data)
        result = await self.storage_service.get_vfolder_info(req)
        return web.json_response(result)

    async def delete_vfolder(self, request: web.Request) -> web.Response:
        data = await request.json()
        data["volume_id"] = uuid.UUID(data["volume_id"])
        req = VFolderIDModel(**data)
        await self.storage_service.delete_vfolder(req)
        return web.Response(status=202)
