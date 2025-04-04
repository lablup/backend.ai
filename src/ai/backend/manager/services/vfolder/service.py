import logging
from pathlib import PurePosixPath

import aiohttp
from aiohttp import hdrs, web

from ai.backend.common.types import VFolderID
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.api.exceptions import ObjectNotFound, StorageProxyError
from ai.backend.manager.config import DEFAULT_CHUNK_SIZE
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import is_unmanaged, query_accessible_vfolders, vfolders
from ai.backend.manager.services.vfolder.actions.get_task_logs import (
    GetTaskLogsAction,
    GetTaskLogsActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


class VFolderService:
    _db: ExtendedAsyncSAEngine
    _storage_manager: StorageSessionManager

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        storage_manager: StorageSessionManager,
    ) -> None:
        self._db = db
        self._storage_manager = storage_manager

    async def get_task_logs(self, action: GetTaskLogsAction) -> GetTaskLogsActionResult:
        user_uuid = action.user_id
        user_role = action.user_role
        domain_name = action.domain_name
        kernel_id_str = action.kernel_id
        request = action.request

        async with self._db.begin_readonly() as conn:
            matched_vfolders = await query_accessible_vfolders(
                conn,
                user_uuid,
                user_role=user_role,
                domain_name=domain_name,
                allowed_vfolder_types=["user"],
                extra_vf_conds=(vfolders.c.name == ".logs"),
            )
            if not matched_vfolders:
                raise ObjectNotFound(
                    extra_data={"vfolder_name": ".logs"},
                    object_name="vfolder",
                )
            log_vfolder = matched_vfolders[0]

        _proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(
            log_vfolder["host"], is_unmanaged(log_vfolder["unmanaged_path"])
        )
        response = web.StreamResponse(status=200)
        response.headers[hdrs.CONTENT_TYPE] = "text/plain"
        prepared = False

        try:
            async with self._storage_manager.request(
                log_vfolder["host"],
                "POST",
                "folder/file/fetch",
                json={
                    "volume": volume_name,
                    "vfid": str(VFolderID.from_row(log_vfolder)),
                    "relpath": str(
                        PurePosixPath("task")
                        / kernel_id_str[:2]
                        / kernel_id_str[2:4]
                        / f"{kernel_id_str[4:]}.log",
                    ),
                },
                raise_for_status=True,
            ) as (_, storage_resp):
                while True:
                    chunk = await storage_resp.content.read(DEFAULT_CHUNK_SIZE)
                    if not chunk:
                        break
                    if not prepared:
                        await response.prepare(request)
                        prepared = True
                    await response.write(chunk)
        except aiohttp.ClientResponseError as e:
            raise StorageProxyError(status=e.status, extra_msg=e.message)
        finally:
            if prepared:
                await response.write_eof()
        # TODO: log_vfolder is not a VFolderRow, but a dict, fix this.
        return GetTaskLogsActionResult(response=response, vfolder_row=log_vfolder)
