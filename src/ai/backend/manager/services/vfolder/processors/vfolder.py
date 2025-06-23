from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec

from ..actions.base import (
    CloneVFolderAction,
    CloneVFolderActionResult,
    CreateVFolderAction,
    CreateVFolderActionResult,
    DeleteForeverVFolderAction,
    DeleteForeverVFolderActionResult,
    ForceDeleteVFolderAction,
    ForceDeleteVFolderActionResult,
    GetTaskLogsAction,
    GetTaskLogsActionResult,
    GetVFolderAction,
    GetVFolderActionResult,
    ListVFolderAction,
    ListVFolderActionResult,
    MoveToTrashVFolderAction,
    MoveToTrashVFolderActionResult,
    RestoreVFolderFromTrashAction,
    RestoreVFolderFromTrashActionResult,
    UpdateVFolderAttributeAction,
    UpdateVFolderAttributeActionResult,
)
from ..services.vfolder import VFolderService


class VFolderProcessors(AbstractProcessorPackage):
    create_vfolder: ActionProcessor[CreateVFolderAction, CreateVFolderActionResult]
    get_vfolder: ActionProcessor[GetVFolderAction, GetVFolderActionResult]
    list_vfolder: ActionProcessor[ListVFolderAction, ListVFolderActionResult]
    update_vfolder_attribute: ActionProcessor[
        UpdateVFolderAttributeAction, UpdateVFolderAttributeActionResult
    ]
    move_to_trash_vfolder: ActionProcessor[MoveToTrashVFolderAction, MoveToTrashVFolderActionResult]
    restore_vfolder_from_trash: ActionProcessor[
        RestoreVFolderFromTrashAction, RestoreVFolderFromTrashActionResult
    ]
    delete_forever_vfolder: ActionProcessor[
        DeleteForeverVFolderAction, DeleteForeverVFolderActionResult
    ]
    force_delete_vfolder: ActionProcessor[ForceDeleteVFolderAction, ForceDeleteVFolderActionResult]
    clone_vfolder: ActionProcessor[CloneVFolderAction, CloneVFolderActionResult]
    get_task_logs: ActionProcessor[GetTaskLogsAction, GetTaskLogsActionResult]

    def __init__(self, service: VFolderService, action_monitors: list[ActionMonitor]):
        self.create_vfolder = ActionProcessor(service.create, action_monitors)
        self.get_vfolder = ActionProcessor(service.get, action_monitors)
        self.list_vfolder = ActionProcessor(service.list, action_monitors)
        self.update_vfolder_attribute = ActionProcessor(service.update_attribute, action_monitors)
        self.move_to_trash_vfolder = ActionProcessor(service.move_to_trash, action_monitors)
        self.restore_vfolder_from_trash = ActionProcessor(service.restore, action_monitors)
        self.delete_forever_vfolder = ActionProcessor(service.delete_forever, action_monitors)
        self.force_delete_vfolder = ActionProcessor(service.force_delete, action_monitors)
        self.clone_vfolder = ActionProcessor(service.clone, action_monitors)
        self.get_task_logs = ActionProcessor(service.get_task_logs, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateVFolderAction.spec(),
            GetVFolderAction.spec(),
            ListVFolderAction.spec(),
            UpdateVFolderAttributeAction.spec(),
            MoveToTrashVFolderAction.spec(),
            RestoreVFolderFromTrashAction.spec(),
            DeleteForeverVFolderAction.spec(),
            ForceDeleteVFolderAction.spec(),
            CloneVFolderAction.spec(),
            GetTaskLogsAction.spec(),
        ]
