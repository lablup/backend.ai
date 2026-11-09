from __future__ import annotations

from ai.backend.manager.repositories.vfolder_auto_mount.repository import (
    VFolderAutoMountRepository,
)
from ai.backend.manager.services.vfolder_auto_mount.actions.create import (
    CreateVFolderAutoMountAction,
    CreateVFolderAutoMountActionResult,
)

__all__ = ("VFolderAutoMountService",)


class VFolderAutoMountService:
    _repository: VFolderAutoMountRepository

    def __init__(self, repository: VFolderAutoMountRepository) -> None:
        self._repository = repository

    async def create(
        self, action: CreateVFolderAutoMountAction
    ) -> CreateVFolderAutoMountActionResult:
        data = await self._repository.create(action.creator)
        return CreateVFolderAutoMountActionResult(data=data)
