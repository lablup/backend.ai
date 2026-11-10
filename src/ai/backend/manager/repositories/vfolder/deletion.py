"""Legacy: vfolder deletion routine relocated from models/vfolder/row.py.

This module hosts the procedural deletion flow until it is folded into the
proper repository/service layers. Prefer not to extend it.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

import aiotools
import sqlalchemy as sa

from ai.backend.common.types import VFolderID
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.data.vfolder.types import VFolderOperationStatus, VFolderStorageTarget
from ai.backend.manager.defs import is_unmanaged
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.storage import VFolderGone, VFolderOperationFailed
from ai.backend.manager.models.utils import (
    ExtendedAsyncSAEngine,
    execute_with_retry,
    sql_json_merge,
)
from ai.backend.manager.models.vfolder.row import (
    VFolderRow,
    vfolders,
)
from ai.backend.manager.repositories.vfolder.purge_guards import get_sessions_by_mounted_folder

log = StructuredLogger(logging.getLogger(__spec__.name))


async def update_vfolder_status(
    engine: ExtendedAsyncSAEngine,
    vfolder_ids: Sequence[uuid.UUID],
    update_status: VFolderOperationStatus,
    do_log: bool = True,
    force: bool = False,
) -> None:
    vfolder_info_len = len(vfolder_ids)
    cond: sa.ColumnElement[bool] = vfolders.c.id.in_(vfolder_ids)
    if vfolder_info_len == 0:
        return
    if vfolder_info_len == 1:
        cond = vfolders.c.id == vfolder_ids[0]

    now = datetime.now(UTC)

    if update_status.is_deletable(force):
        select_stmt = sa.select(VFolderRow).where(VFolderRow.id.in_(vfolder_ids))
        async with engine.begin_readonly_session() as db_session:
            for vf_row in await db_session.scalars(select_stmt):
                mount_sessions = await get_sessions_by_mounted_folder(
                    db_session, VFolderID.from_row(vf_row)
                )
                if mount_sessions:
                    session_ids = [str(s) for s in mount_sessions]
                    raise InvalidAPIParameters(
                        f"Cannot delete the vfolder. The vfolder(id: {vf_row.id}) is mounted on sessions(ids: {session_ids})"
                    )

    if update_status == VFolderOperationStatus.DELETE_ERROR:
        folder_ids: list[uuid.UUID] = []
        select_stmt = sa.select(VFolderRow).where(VFolderRow.id.in_(vfolder_ids))
        async with engine.begin_readonly_session() as db_session:
            for vf_row in await db_session.scalars(select_stmt):
                if vf_row.status == VFolderOperationStatus.DELETE_PENDING:
                    folder_ids.append(vf_row.id)
        cond = VFolderRow.id.in_(folder_ids)

    async def _update() -> None:
        async with engine.begin_session() as db_session:
            values = {
                "status": update_status,
                "status_changed": now,
                "status_history": sql_json_merge(
                    vfolders.c.status_history,
                    (),
                    {
                        update_status.name: now.isoformat(),
                    },
                ),
            }
            if update_status == VFolderOperationStatus.DELETE_ONGOING:
                values["name"] = VFolderRow.name + f"_deleted_{now.strftime('%Y-%m-%dT%H%M%S%z')}"
            query = sa.update(vfolders).values(**values).where(cond)
            await db_session.execute(query)

    await execute_with_retry(_update)
    if do_log:
        log.debug(
            "vfolder status updated",
            vfolder_ids=", ".join(str(x) for x in vfolder_ids),
            vfolder_status=update_status,
        )


async def initiate_vfolder_deletion(
    db_engine: ExtendedAsyncSAEngine,
    requested_vfolders: Sequence[VFolderStorageTarget],
    storage_manager: StorageSessionManager,
    _storage_ptask_group: aiotools.PersistentTaskGroup | None = None,
    *,
    force: bool = False,
) -> int:
    """Purges VFolder content from storage host.

    Legacy routine moved out of the models layer; kept as-is pending a proper
    repository/service refactor.
    """
    vfolder_info_len = len(requested_vfolders)
    vfolder_ids = tuple(info.vfolder_id.folder_id for info in requested_vfolders)
    if vfolder_info_len == 0:
        return 0

    await update_vfolder_status(
        db_engine,
        vfolder_ids,
        VFolderOperationStatus.DELETE_ONGOING,
        do_log=False,
        force=force,
    )

    already_deleted: list[VFolderStorageTarget] = []

    for vfolder_info in requested_vfolders:
        folder_id = vfolder_info.vfolder_id
        host_name = vfolder_info.host
        unmanaged_path = vfolder_info.unmanaged_path
        proxy_name, volume_name = storage_manager.get_proxy_and_volume(
            host_name, is_unmanaged(unmanaged_path)
        )
        try:
            manager_client = storage_manager.get_manager_facing_client(proxy_name)
            await manager_client.delete_folder(volume_name, str(folder_id))
        except (VFolderOperationFailed, InvalidAPIParameters) as e:
            if e.status == 410:
                already_deleted.append(vfolder_info)
        except VFolderGone:
            already_deleted.append(vfolder_info)
    if already_deleted:
        vfolder_ids = tuple(info.vfolder_id.folder_id for info in already_deleted)

        await update_vfolder_status(
            db_engine, vfolder_ids, VFolderOperationStatus.DELETE_COMPLETE, do_log=False
        )
        log.trace("vfolders already deleted", vfolder_ids=", ".join(str(x) for x in vfolder_ids))

    log.trace("vfolder purge started", vfolder_ids=", ".join(str(x) for x in vfolder_ids))

    return vfolder_info_len
