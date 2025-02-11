import asyncio
import json
import logging
import uuid
import weakref
from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator

from aiohttp import web

from ai.backend.common.dto.identifiers import VolumeID
from ai.backend.common.events import VFolderDeletionFailureEvent, VFolderDeletionSuccessEvent
from ai.backend.common.types import VFolderID
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.storage.exception import (
    ExternalError,
    InvalidQuotaConfig,
    InvalidSubpathError,
    QuotaScopeAlreadyExists,
    QuotaScopeNotFoundError,
    VFolderNotFoundError,
)
from ai.backend.storage.utils import log_manager_api_entry
from ai.backend.storage.volumes.pool import VolumePool
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

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class VolumeService:
    _volume_pool: VolumePool
    _deletion_tasks: weakref.WeakValueDictionary[VFolderID, asyncio.Task]

    def __init__(
        self,
        volume_pool: VolumePool,
    ) -> None:
        self._volume_pool = volume_pool
        self._deletion_tasks = weakref.WeakValueDictionary[VFolderID, asyncio.Task]()

    async def _get_capabilities(self, volume_id: VolumeID) -> list[str]:
        async with self._volume_pool.get_volume(volume_id) as volume:
            return [*await volume.get_capabilities()]

    @actxmgr
    async def _handle_external_errors(self) -> AsyncIterator[None]:
        try:
            yield
        except ExternalError as e:
            log.exception("An external error occurred: %s", str(e))
            raise web.HTTPInternalServerError(
                body=json.dumps({
                    "msg": "An internal error has occurred.",
                }),
                content_type="application/json",
            )

    async def _delete_vfolder(
        self,
        vfolder_data: VFolderKeyData,
    ) -> None:
        volume_id = vfolder_data.volume_id
        vfolder_id = vfolder_data.vfolder_id

        current_task = asyncio.current_task()
        assert current_task is not None
        self._deletion_tasks[vfolder_id] = current_task

        try:
            async with self._volume_pool.get_volume(volume_id) as volume:
                await volume.delete_vfolder(vfolder_id)
        except OSError as e:
            msg = str(e) if e.strerror is None else e.strerror
            msg = f"{msg} (errno:{e.errno})"
            log.exception(f"VFolder deletion task failed. (vfolder_id:{vfolder_id}, e:{msg})")
            await self._volume_pool._event_producer.produce_event(
                VFolderDeletionFailureEvent(
                    vfid=vfolder_id,
                    message=msg,
                )
            )
        except Exception as e:
            log.exception(f"VFolder deletion task failed. (vfolder_id:{vfolder_id}, e:{str(e)})")
            await self._volume_pool._event_producer.produce_event(
                VFolderDeletionFailureEvent(
                    vfid=vfolder_id,
                    message=str(e),
                )
            )
        except asyncio.CancelledError:
            log.warning(f"Vfolder deletion task cancelled. (vfolder_id:{vfolder_id})")
        else:
            log.info(f"VFolder deletion task successed. (vfolder_id:{vfolder_id})")
            await self._volume_pool._event_producer.produce_event(
                VFolderDeletionSuccessEvent(vfolder_id)
            )

    async def get_volume(self, volume_data: VolumeKeyData) -> VolumeMetadata:
        volume_id = volume_data.volume_id
        await log_manager_api_entry(log, "get_volume", volume_id)
        volume = self._volume_pool.get_volume_info(volume_id)
        return VolumeMetadata(
            volume_id=volume_id,
            backend=volume.backend,
            path=volume.path,
            fsprefix=volume.fsprefix,
            capabilities=await self._get_capabilities(volume_id),
        )

    async def get_volumes(self) -> VolumeMetadataList:
        await log_manager_api_entry(log, "get_volumes", params=None)
        volumes = self._volume_pool.list_volumes()
        return VolumeMetadataList(
            volumes=[
                VolumeMetadata(
                    volume_id=uuid.UUID(volume_id),
                    backend=info.backend,
                    path=info.path,
                    fsprefix=info.fsprefix,
                    capabilities=await self._get_capabilities(uuid.UUID(volume_id)),
                )
                for volume_id, info in volumes.items()
            ]
        )

    async def create_quota_scope(self, quota_data: QuotaScopeKeyData) -> NewQuotaScopeCreated:
        volume_id = quota_data.volume_id
        quota_scope_id = quota_data.quota_scope_id
        options = quota_data.options

        await log_manager_api_entry(log, "create_quota_scope", quota_data)
        async with self._volume_pool.get_volume(volume_id) as volume:
            try:
                async with self._handle_external_errors():
                    await volume.quota_model.create_quota_scope(
                        quota_scope_id=quota_scope_id, options=options, extra_args=None
                    )
            except QuotaScopeAlreadyExists:
                raise web.HTTPConflict(reason="Volume already exists with given quota scope.")
            return NewQuotaScopeCreated(
                quota_scope_id=quota_scope_id,
                quota_scope_path=volume.quota_model.mangle_qspath(quota_scope_id),
            )

    async def get_quota_scope(self, quota_data: QuotaScopeKeyData) -> QuotaScopeMetadata:
        volume_id = quota_data.volume_id
        quota_scope_id = quota_data.quota_scope_id

        await log_manager_api_entry(log, "get_quota_scope", quota_data)
        async with self._volume_pool.get_volume(volume_id) as volume:
            async with self._handle_external_errors():
                quota_usage = await volume.quota_model.describe_quota_scope(quota_scope_id)
            if not quota_usage:
                raise QuotaScopeNotFoundError
            return QuotaScopeMetadata(
                used_bytes=quota_usage.used_bytes, limit_bytes=quota_usage.limit_bytes
            )

    async def update_quota_scope(self, quota_data: QuotaScopeKeyData) -> None:
        volume_id = quota_data.volume_id
        quota_scope_id = quota_data.quota_scope_id
        options = quota_data.options

        await log_manager_api_entry(log, "update_quota_scope", quota_data)
        async with self._volume_pool.get_volume(volume_id) as volume:
            async with self._handle_external_errors():
                quota_usage = await volume.quota_model.describe_quota_scope(quota_scope_id)
                if not quota_usage:
                    await volume.quota_model.create_quota_scope(
                        quota_scope_id=quota_scope_id, options=options, extra_args=None
                    )
                else:
                    assert options is not None
                    try:
                        await volume.quota_model.update_quota_scope(
                            quota_scope_id=quota_scope_id,
                            config=options,
                        )
                    except InvalidQuotaConfig:
                        raise web.HTTPBadRequest(reason="Invalid quota config option")
            return None

    async def delete_quota_scope(self, quota_data: QuotaScopeKeyData) -> None:
        volume_id = quota_data.volume_id
        quota_scope_id = quota_data.quota_scope_id

        await log_manager_api_entry(log, "delete_quota_scope", quota_data)
        async with self._volume_pool.get_volume(volume_id) as volume:
            async with self._handle_external_errors():
                quota_usage = await volume.quota_model.describe_quota_scope(quota_scope_id)
            if not quota_usage:
                raise QuotaScopeNotFoundError
            await volume.quota_model.unset_quota(quota_scope_id)
            return None

    async def create_vfolder(self, vfolder_data: VFolderKeyData) -> NewVFolderCreated:
        volume_id = vfolder_data.volume_id
        vfolder_id = vfolder_data.vfolder_id
        quota_scope_id = vfolder_id.quota_scope_id

        await log_manager_api_entry(log, "create_vfolder", vfolder_data)
        assert quota_scope_id is not None
        async with self._volume_pool.get_volume(volume_id) as volume:
            try:
                await volume.create_vfolder(vfolder_id)
            except QuotaScopeNotFoundError:
                assert quota_scope_id
                await volume.quota_model.create_quota_scope(quota_scope_id)
                try:
                    await volume.create_vfolder(vfolder_id)
                except QuotaScopeNotFoundError:
                    raise ExternalError("Failed to create vfolder due to quota scope not found")
            return NewVFolderCreated(
                vfolder_id=vfolder_id,
                quota_scope_path=volume.quota_model.mangle_qspath(quota_scope_id),
                vfolder_path=await volume.get_vfolder_mount(vfolder_id, "."),
            )

    async def clone_vfolder(self, vfolder_data: VFolderKeyData) -> NewVFolderCreated:
        volume_id = vfolder_data.volume_id
        src_vfolder_id = vfolder_data.vfolder_id
        dst_vfolder_id = vfolder_data.dst_vfolder_id

        if dst_vfolder_id is None:
            raise ValueError("Destination vfolder ID cannot be None")
        await log_manager_api_entry(log, "clone_vfolder", vfolder_data)
        async with self._volume_pool.get_volume(volume_id) as volume:
            await volume.clone_vfolder(src_vfolder_id, dst_vfolder_id)
        return NewVFolderCreated(
            vfolder_id=dst_vfolder_id,
            quota_scope_path=volume.quota_model.mangle_qspath(dst_vfolder_id),
            vfolder_path=await volume.get_vfolder_mount(dst_vfolder_id, "."),
        )

    async def get_vfolder_info(self, vfolder_data: VFolderKeyData) -> VFolderMetadata:
        volume_id = vfolder_data.volume_id
        vfolder_id = vfolder_data.vfolder_id
        subpath = vfolder_data.subpath

        await log_manager_api_entry(log, "get_vfolder_info", vfolder_data)
        async with self._volume_pool.get_volume(volume_id) as volume:
            try:
                mount_path = await volume.get_vfolder_mount(vfolder_id, str(subpath))
                usage = await volume.get_usage(vfolder_id)
                fs_usage = await volume.get_fs_usage()
            except VFolderNotFoundError:
                raise web.HTTPGone(reason="VFolder not found")
            except InvalidSubpathError:
                raise web.HTTPBadRequest(reason="Invalid vfolder subpath")

            return VFolderMetadata(
                mount_path=mount_path,
                file_count=usage.file_count,
                used_bytes=usage.used_bytes,
                capacity_bytes=fs_usage.capacity_bytes,
                fs_used_bytes=fs_usage.used_bytes,
            )

    async def delete_vfolder(self, vfolder_data: VFolderKeyData) -> None:
        volume_id = vfolder_data.volume_id
        vfolder_id = vfolder_data.vfolder_id

        await log_manager_api_entry(log, "delete_vfolder", vfolder_data)
        try:
            async with self._volume_pool.get_volume(volume_id) as volume:
                await volume.get_vfolder_mount(vfolder_id, ".")
        except VFolderNotFoundError:
            ongoing_task = self._deletion_tasks.get(vfolder_id)
            if ongoing_task is not None:
                ongoing_task.cancel()
            raise web.HTTPGone(reason="VFolder not found")
        else:
            ongoing_task = self._deletion_tasks.get(vfolder_id)
            if ongoing_task is not None and ongoing_task.done():
                asyncio.create_task(self._delete_vfolder(vfolder_data))
        return None
