from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import BatchOpsResult
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.services.vfolder.actions.admin_search_vfolders import (
    GlobalSearchVFoldersAction,
)


class VFolderAdminProcessors:
    admin_search_vfolders: GlobalActionProcessor[
        GlobalSearchVFoldersAction, BatchOpsResult[VFolderData]
    ]

    def __init__(self, group: ProcessorGroup[VFolderData]) -> None:
        self.admin_search_vfolders = group.global_searcher_ops(GlobalSearchVFoldersAction)
