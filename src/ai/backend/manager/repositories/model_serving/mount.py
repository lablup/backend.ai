from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from ai.backend.common.types import (
    VFolderMount,
    VFolderMountOptions,
    VFolderMountRequest,
    VFolderUsageMode,
)
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.repositories.vfolder.mount import prepare_vfolder_mounts
from ai.backend.manager.types import MountOptionModel, UserScope

__all__: Sequence[str] = ("check_extra_mounts",)


async def check_extra_mounts(
    conn: AsyncConnection,
    allowed_vfolder_types: Sequence[str],
    storage_manager: StorageSessionManager,
    model_id: UUID,
    model_mount_destination: str,
    extra_mounts: dict[UUID, MountOptionModel],
    user_scope: UserScope,
    resource_policy: dict[str, Any],
) -> Sequence[VFolderMount]:
    """
    check if user is allowed to access every folders eagering to mount (other than model VFolder)
    on general session creation lifecycle this check will be completed by `enqueue_session()` function,
    which is not covered by the validation procedure (`create_session(dry_run=True)` call at the bottom part of `create()` API)
    so we have to manually cover this part here.
    """
    if model_id in extra_mounts:
        raise InvalidAPIParameters(
            "Same VFolder appears on both model specification and VFolder mount"
        )

    mount_requests = [
        VFolderMountRequest(
            ref=folder_id,
            dst_path=options.mount_destination,
            options=VFolderMountOptions(
                permission=options.permission,
                subpath=options.subpath,
            ),
        )
        for folder_id, options in extra_mounts.items()
    ]
    vfolder_mounts = await prepare_vfolder_mounts(
        conn,
        storage_manager,
        allowed_vfolder_types,
        user_scope,
        resource_policy,
        mount_requests,
    )

    for vfolder in vfolder_mounts:
        if str(vfolder.kernel_path) == model_mount_destination:
            raise InvalidAPIParameters(
                "extra_mounts.mount_destination conflicts with model_mount_destination config. Make sure not to shadow value defined at model_mount_destination as a mount destination of extra VFolders."
            )
        if vfolder.usage_mode == VFolderUsageMode.MODEL:
            raise InvalidAPIParameters(
                "MODEL type VFolders cannot be added as a part of extra_mounts folder"
            )

    return vfolder_mounts
