from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.vfolder.actions.admin_search_vfolders import (
    AdminSearchVFoldersAction,
    AdminSearchVFoldersActionResult,
)
from ai.backend.manager.services.vfolder.services.vfolder_admin import VFolderAdminService


class VFolderAdminProcessors(AbstractProcessorPackage):
    admin_search_vfolders: ActionProcessor[
        AdminSearchVFoldersAction, AdminSearchVFoldersActionResult
    ]

    def __init__(
        self,
        service: VFolderAdminService,
        action_monitors: list[ActionMonitor],
    ) -> None:
        self.admin_search_vfolders = ActionProcessor(service.admin_search_vfolders, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            AdminSearchVFoldersAction.spec(),
        ]
