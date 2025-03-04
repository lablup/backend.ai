from ai.backend.manager.repositories.vfolder.repository import VFolderRepository
from ai.backend.manager.services.vfolder.actions.create import (
    VFolderCreateAction,
    VFolderCreateActionResult,
)
from ai.backend.manager.services.vfolder.actions.delete import (
    VFolderDeleteAction,
    VFolderDeleteActionResult,
)
from ai.backend.manager.services.vfolder.actions.get import VFolderGetAction, VFolderGetActionResult
from ai.backend.manager.services.vfolder.actions.list import (
    VFolderListAction,
    VFolderListActionResult,
)
from ai.backend.manager.services.vfolder.actions.rename import (
    VFolderRenameAction,
    VFolderRenameActionResult,
)


class VFolderService:
    _repository: VFolderRepository

    def __init__(self, repository: VFolderRepository):
        self._repository = repository

    async def create_vfolder(
        self,
        action: VFolderCreateAction,
    ) -> VFolderCreateActionResult:
        raise NotImplementedError

    async def delete_vfolder(
        self,
        action: VFolderDeleteAction,
    ) -> VFolderDeleteActionResult:
        raise NotImplementedError

    async def rename_vfolder(
        self,
        action: VFolderRenameAction,
    ) -> VFolderRenameActionResult:
        raise NotImplementedError

    async def list_vfolders(
        self,
        action: VFolderListAction,
    ) -> VFolderListActionResult:
        raise NotImplementedError

    async def get_vfolder(
        self,
        action: VFolderGetAction,
    ) -> VFolderGetActionResult:
        raise NotImplementedError
