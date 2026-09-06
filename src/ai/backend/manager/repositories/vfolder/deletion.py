"""Legacy: vfolder deletion routine relocated from models/vfolder/row.py.

This module hosts the procedural deletion flow until it is folded into the
proper repository/service layers. Prefer not to extend it.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

import aiotools

from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.data.vfolder.types import VFolderOperationStatus
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.storage import VFolderGone, VFolderOperationFailed
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.purgers import (
    VFolderInvitationBatchPurger,
    VFolderPermissionBatchPurger,
)
from ai.backend.manager.models.vfolder.row import (
    VFolderDeletionInfo,
    is_unmanaged,
    update_vfolder_status,
)
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


async def initiate_vfolder_deletion(
    db_engine: ExtendedAsyncSAEngine,
    v2_ops_provider: V2DBOpsProvider,
    requested_vfolders: Sequence[VFolderDeletionInfo],
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
    vfolder_ids = tuple(vf_id.folder_id for vf_id, _, _ in requested_vfolders)
    if vfolder_info_len == 0:
        return 0

    async with v2_ops_provider.write_ops() as w:
        await w.batch_purge_entities_in_global(
            VFolderInvitationBatchPurger(vfolder_ids=vfolder_ids)
        )
        for vfolder_id in vfolder_ids:
            await w.batch_purge_field_entities(
                VFolderUUID(vfolder_id), VFolderPermissionBatchPurger()
            )
    await update_vfolder_status(
        db_engine,
        vfolder_ids,
        VFolderOperationStatus.DELETE_ONGOING,
        do_log=False,
        force=force,
    )

    already_deleted: list[VFolderDeletionInfo] = []

    for vfolder_info in requested_vfolders:
        folder_id, host_name, unmanaged_path = vfolder_info
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
        vfolder_ids = tuple(vf_id.folder_id for vf_id, _, _ in already_deleted)

        await update_vfolder_status(
            db_engine, vfolder_ids, VFolderOperationStatus.DELETE_COMPLETE, do_log=False
        )
        log.info("vfolders already deleted {}", [str(x) for x in vfolder_ids])

    log.info("Started purging vfolders {}", [str(x) for x in vfolder_ids])

    return vfolder_info_len
