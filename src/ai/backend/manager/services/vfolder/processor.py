from typing import Optional

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
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
from ai.backend.manager.services.vfolder.service import VFolderService


class VFolderCreateHandler:
    pass


class VfolderDeleteHandler:
    pass


class VFolderProcessors:
    create_vfolder: ActionProcessor[VFolderCreateAction, VFolderCreateActionResult]
    delete_vfolder: ActionProcessor[VFolderDeleteAction, VFolderDeleteActionResult]
    rename_vfolder: ActionProcessor[VFolderRenameAction, VFolderRenameActionResult]
    list_vfolders: ActionProcessor[VFolderListAction, VFolderListActionResult]
    get_vfolder: ActionProcessor[VFolderGetAction, VFolderGetActionResult]

    def __init__(self, service: VFolderService, monitors: Optional[list[ActionMonitor]] = None):
        self.create_vfolder = ActionProcessor[VFolderCreateAction, VFolderCreateActionResult](
            service.create_vfolder, monitors
        )
        self.delete_vfolder = ActionProcessor[VFolderDeleteAction, VFolderDeleteActionResult](
            service.delete_vfolder, monitors
        )
        self.rename_vfolder = ActionProcessor[VFolderRenameAction, VFolderRenameActionResult](
            service.rename_vfolder, monitors
        )
        self.list_vfolders = ActionProcessor[VFolderListAction, VFolderListActionResult](
            service.list_vfolders, monitors
        )
        self.get_vfolder = ActionProcessor[VFolderGetAction, VFolderGetActionResult](
            service.get_vfolder, monitors
        )
