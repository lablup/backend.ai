from __future__ import annotations

import posixpath

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.vfolder.types import verify_mount_destination
from ai.backend.manager.data.vfolder_auto_mount.types import VFolderAutoMountData
from ai.backend.manager.errors.vfolder_auto_mount import (
    VFolderAutoMountDestinationReserved,
    VFolderAutoMountSubpathOutsideVFolder,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.vfolder_auto_mount.repository import (
    VFolderAutoMountRepository,
)
from ai.backend.manager.services.vfolder_auto_mount.actions.create import (
    CreateVFolderAutoMountAction,
    CreateVFolderAutoMountActionResult,
)
from ai.backend.manager.services.vfolder_auto_mount.actions.update import (
    UpdateVFolderAutoMountAction,
    UpdateVFolderAutoMountActionResult,
)

__all__ = ("VFolderAutoMountService",)


class VFolderAutoMountService:
    _repository: VFolderAutoMountRepository
    _ops_repository: OpsRepository[VFolderAutoMountData]

    def __init__(
        self,
        repository: VFolderAutoMountRepository,
        ops_repository: OpsRepository[VFolderAutoMountData],
    ) -> None:
        self._repository = repository
        self._ops_repository = ops_repository

    async def create(
        self, action: CreateVFolderAutoMountAction
    ) -> CreateVFolderAutoMountActionResult:
        spec = action.creator.spec
        self._reject_unmountable_destination_or_subpath(
            spec.mount_destination, spec.subpath, ActionOperationType.CREATE
        )
        data = await self._repository.create(action.creator)
        return CreateVFolderAutoMountActionResult(data=data)

    async def update(
        self, action: UpdateVFolderAutoMountAction
    ) -> UpdateVFolderAutoMountActionResult:
        updater = action.updater
        self._reject_unmountable_destination_or_subpath(
            updater.mount_destination.optional_value(),
            updater.subpath.optional_value(),
            ActionOperationType.UPDATE,
        )
        data = await self._ops_repository.update(updater)
        return UpdateVFolderAutoMountActionResult(data=data)

    def _reject_unmountable_destination_or_subpath(
        self,
        mount_destination: str | None,
        subpath: str | None,
        operation: ActionOperationType,
    ) -> None:
        if mount_destination is not None and not verify_mount_destination(mount_destination):
            raise VFolderAutoMountDestinationReserved(operation=operation)
        if subpath is not None:
            normalized_subpath = posixpath.normpath(subpath)
            if (
                normalized_subpath == ".."
                or normalized_subpath.startswith("../")
                or posixpath.isabs(normalized_subpath)
            ):
                raise VFolderAutoMountSubpathOutsideVFolder(operation=operation)
