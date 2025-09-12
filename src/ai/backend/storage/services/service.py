import asyncio
import logging
import uuid
import weakref
from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator, Optional

from aiohttp import web

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.vfolder.anycast import (
    VFolderDeletionFailureEvent,
    VFolderDeletionSuccessEvent,
)
from ai.backend.common.json import dump_json_str
from ai.backend.common.types import QuotaConfig, VFolderID, VolumeID
from ai.backend.logging.utils import BraceStyleAdapter

from ..exception import (
    ExternalStorageServiceError,
    InvalidQuotaConfig,
    InvalidQuotaScopeError,
    InvalidSubpathError,
    QuotaScopeAlreadyExists,
    QuotaScopeNotFoundError,
    VFolderNotFoundError,
)
from ..utils import log_manager_api_entry_new
from ..volumes.pool import VolumePool
from ..volumes.types import (
    QuotaScopeKey,
    QuotaScopeMeta,
    VFolderKey,
    VFolderMeta,
    VolumeMeta,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class VolumeService:
    _volume_pool: VolumePool
    _event_producer: EventProducer
    _deletion_tasks: weakref.WeakValueDictionary[VFolderID, asyncio.Task]

    def __init__(
        self,
        volume_pool: VolumePool,
        event_producer: EventProducer,
    ) -> None:
        self._volume_pool = volume_pool
        self._event_producer = event_producer
        self._deletion_tasks = weakref.WeakValueDictionary[VFolderID, asyncio.Task]()

    async def _get_capabilities(self, volume_id: VolumeID) -> list[str]:
        async with self._volume_pool.get_volume(volume_id) as volume:
            return [*await volume.get_capabilities()]

    @actxmgr
    async def _handle_external_errors(self) -> AsyncIterator[None]:
        try:
            yield
        except ExternalStorageServiceError as e:
            log.exception("An external error occurred: %s", str(e))
            # TODO: Extract exception handling to middleware
            raise web.HTTPInternalServerError(
                text=dump_json_str({
                    "msg": "An internal error has occurred.",
                }),
                content_type="application/json",
            )

    async def _delete_vfolder(
        self,
        vfolder_key: VFolderKey,
    ) -> None:
        volume_id = vfolder_key.volume_id
        vfolder_id = vfolder_key.vfolder_id

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
            await self._event_producer.anycast_event(
                VFolderDeletionFailureEvent(
                    vfid=vfolder_id,
                    message=msg,
                )
            )
        except Exception as e:
            log.exception(f"VFolder deletion task failed. (vfolder_id:{vfolder_id}, e:{str(e)})")
            await self._event_producer.anycast_event(
                VFolderDeletionFailureEvent(
                    vfid=vfolder_id,
                    message=str(e),
                )
            )
        except asyncio.CancelledError:
            log.warning(f"Vfolder deletion task cancelled. (vfolder_id:{vfolder_id})")
        else:
            log.info(f"VFolder deletion task successed. (vfolder_id:{vfolder_id})")
            await self._event_producer.anycast_event(VFolderDeletionSuccessEvent(vfolder_id))

    async def get_volume(self, volume_id: VolumeID) -> VolumeMeta:
        await log_manager_api_entry_new(log, "get_volume", volume_id)
        volume = self._volume_pool.get_volume_info(volume_id)
        return VolumeMeta(
            volume_id=volume_id,
            backend=volume.backend,
            path=volume.path,
            fsprefix=volume.fsprefix,
            capabilities=await self._get_capabilities(volume_id),
        )

    async def get_volumes(self) -> list[VolumeMeta]:
        await log_manager_api_entry_new(log, "get_volumes", params=None)
        volumes = self._volume_pool.list_volumes()
        return [
            VolumeMeta(
                volume_id=uuid.UUID(volume_id),
                backend=info.backend,
                path=info.path,
                fsprefix=info.fsprefix,
                capabilities=await self._get_capabilities(uuid.UUID(volume_id)),
            )
            for volume_id, info in volumes.items()
        ]

    async def create_quota_scope(
        self, quota_scope_key: QuotaScopeKey, options: Optional[QuotaConfig]
    ) -> None:
        quota_scope_id = quota_scope_key.quota_scope_id
        await log_manager_api_entry_new(log, "create_quota_scope", quota_scope_key)
        async with self._volume_pool.get_volume(quota_scope_key.volume_id) as volume:
            try:
                async with self._handle_external_errors():
                    await volume.quota_model.create_quota_scope(
                        quota_scope_id=quota_scope_id, options=options, extra_args=None
                    )
            except QuotaScopeAlreadyExists:
                raise web.HTTPConflict(reason="Volume already exists with given quota scope.")

    async def get_quota_scope(self, quota_scope_key: QuotaScopeKey) -> QuotaScopeMeta:
        await log_manager_api_entry_new(log, "get_quota_scope", quota_scope_key)
        async with self._volume_pool.get_volume(quota_scope_key.volume_id) as volume:
            async with self._handle_external_errors():
                quota_usage = await volume.quota_model.describe_quota_scope(
                    quota_scope_key.quota_scope_id
                )
            if not quota_usage:
                raise QuotaScopeNotFoundError
            return QuotaScopeMeta(
                used_bytes=quota_usage.used_bytes, limit_bytes=quota_usage.limit_bytes
            )

    async def update_quota_scope(
        self, quota_scope_key: QuotaScopeKey, options: Optional[QuotaConfig]
    ) -> None:
        quota_scope_id = quota_scope_key.quota_scope_id
        await log_manager_api_entry_new(log, "update_quota_scope", quota_scope_key)
        async with self._volume_pool.get_volume(quota_scope_key.volume_id) as volume:
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

    async def delete_quota_scope(self, quota_scope_key: QuotaScopeKey) -> None:
        quota_scope_id = quota_scope_key.quota_scope_id
        await log_manager_api_entry_new(log, "delete_quota_scope", quota_scope_key)
        async with self._volume_pool.get_volume(quota_scope_key.volume_id) as volume:
            async with self._handle_external_errors():
                quota_usage = await volume.quota_model.describe_quota_scope(quota_scope_id)
            if not quota_usage:
                raise QuotaScopeNotFoundError
            await volume.quota_model.unset_quota(quota_scope_id)

    async def create_vfolder(self, vfolder_key: VFolderKey) -> None:
        vfolder_id = vfolder_key.vfolder_id
        quota_scope_id = vfolder_id.quota_scope_id

        await log_manager_api_entry_new(log, "create_vfolder", vfolder_key)
        if quota_scope_id is None:
            raise InvalidQuotaScopeError("Quota scope ID is not set in the vfolder key.")
        async with self._volume_pool.get_volume(vfolder_key.volume_id) as volume:
            try:
                await volume.create_vfolder(vfolder_id)
            except QuotaScopeNotFoundError:
                await volume.quota_model.create_quota_scope(quota_scope_id)
                try:
                    await volume.create_vfolder(vfolder_id)
                except QuotaScopeNotFoundError:
                    raise ExternalStorageServiceError(
                        "Failed to create vfolder due to quota scope not found"
                    )

    async def clone_vfolder(self, vfolder_key: VFolderKey, dst_vfolder_id: VFolderID) -> None:
        await log_manager_api_entry_new(log, "clone_vfolder", vfolder_key)
        async with self._volume_pool.get_volume(vfolder_key.volume_id) as volume:
            await volume.clone_vfolder(vfolder_key.vfolder_id, dst_vfolder_id)

    async def get_vfolder_info(self, vfolder_key: VFolderKey, subpath: str) -> VFolderMeta:
        vfolder_id = vfolder_key.vfolder_id
        await log_manager_api_entry_new(log, "get_vfolder_info", vfolder_key)
        async with self._volume_pool.get_volume(vfolder_key.volume_id) as volume:
            try:
                mount_path = await volume.get_vfolder_mount(vfolder_id, subpath)
                usage = await volume.get_usage(vfolder_id)
                fs_usage = await volume.get_fs_usage()
            except VFolderNotFoundError:
                raise web.HTTPGone(reason="VFolder not found")
            except InvalidSubpathError:
                raise web.HTTPBadRequest(reason="Invalid vfolder subpath")

            return VFolderMeta(
                mount_path=mount_path,
                file_count=usage.file_count,
                used_bytes=usage.used_bytes,
                capacity_bytes=fs_usage.capacity_bytes,
                fs_used_bytes=fs_usage.used_bytes,
            )

    async def delete_vfolder(self, vfolder_key: VFolderKey) -> None:
        vfolder_id = vfolder_key.vfolder_id
        await log_manager_api_entry_new(log, "delete_vfolder", vfolder_key)
        try:
            async with self._volume_pool.get_volume(vfolder_key.volume_id) as volume:
                await volume.get_vfolder_mount(vfolder_id, ".")
        except VFolderNotFoundError:
            ongoing_task = self._deletion_tasks.get(vfolder_id)
            if ongoing_task is not None:
                ongoing_task.cancel()
            raise web.HTTPGone(reason="VFolder not found")
        else:
            ongoing_task = self._deletion_tasks.get(vfolder_id)
            if ongoing_task is not None and ongoing_task.done():
                asyncio.create_task(self._delete_vfolder(vfolder_key))
        return None
