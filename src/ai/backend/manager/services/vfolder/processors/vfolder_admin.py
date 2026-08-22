from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.services.vfolder.actions.admin_search_vfolders import (
    GlobalSearchVFoldersAction,
    GlobalSearchVFoldersActionResult,
)
from ai.backend.manager.services.vfolder.services.vfolder_admin import VFolderAdminService


class VFolderAdminProcessors:
    admin_search_vfolders: GlobalActionProcessor[
        GlobalSearchVFoldersAction, GlobalSearchVFoldersActionResult
    ]

    def __init__(self, group: ProcessorGroup[VFolderData], service: VFolderAdminService) -> None:
        self.admin_search_vfolders = group.global_scope(
            GlobalSearchVFoldersAction, service.admin_search_vfolders
        )
