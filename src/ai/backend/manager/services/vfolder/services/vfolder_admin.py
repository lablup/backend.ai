from ai.backend.manager.repositories.vfolder.admin_repository import VFolderAdminRepository
from ai.backend.manager.services.vfolder.actions.admin_search_vfolders import (
    AdminSearchVFoldersAction,
    AdminSearchVFoldersActionResult,
)


class VFolderAdminService:
    _vfolder_admin_repository: VFolderAdminRepository

    def __init__(
        self,
        vfolder_admin_repository: VFolderAdminRepository,
    ) -> None:
        self._vfolder_admin_repository = vfolder_admin_repository

    async def admin_search_vfolders(
        self, action: AdminSearchVFoldersAction
    ) -> AdminSearchVFoldersActionResult:
        """Search all vfolders without scope restriction (admin-only)."""
        result = await self._vfolder_admin_repository.search_vfolders(querier=action.querier)
        return AdminSearchVFoldersActionResult(
            data=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
