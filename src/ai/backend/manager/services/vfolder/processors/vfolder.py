from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor.scope import ScopeActionProcessor
from ai.backend.manager.actions.processor.single_entity import SingleEntityActionProcessor
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
    create_vfolder: ScopeActionProcessor[CreateVFolderAction, CreateVFolderActionResult]
    get_vfolder: SingleEntityActionProcessor[GetVFolderAction, GetVFolderActionResult]
    list_vfolder: ScopeActionProcessor[ListVFolderAction, ListVFolderActionResult]
    update_vfolder_attribute: SingleEntityActionProcessor[
        UpdateVFolderAttributeAction, UpdateVFolderAttributeActionResult
    ]
    move_to_trash_vfolder: SingleEntityActionProcessor[
        MoveToTrashVFolderAction, MoveToTrashVFolderActionResult
    ]
    restore_vfolder_from_trash: SingleEntityActionProcessor[
        RestoreVFolderFromTrashAction, RestoreVFolderFromTrashActionResult
    ]
    delete_forever_vfolder: SingleEntityActionProcessor[
        DeleteForeverVFolderAction, DeleteForeverVFolderActionResult
    ]
    force_delete_vfolder: SingleEntityActionProcessor[
        ForceDeleteVFolderAction, ForceDeleteVFolderActionResult
    ]
    clone_vfolder: SingleEntityActionProcessor[CloneVFolderAction, CloneVFolderActionResult]
    get_task_logs: SingleEntityActionProcessor[GetTaskLogsAction, GetTaskLogsActionResult]

    def __init__(self, service: VFolderService, action_monitors: list[ActionMonitor]):
        self.create_vfolder = ScopeActionProcessor(service.create, action_monitors)
        self.get_vfolder = SingleEntityActionProcessor(service.get, action_monitors)
        self.list_vfolder = ScopeActionProcessor(service.list, action_monitors)
        self.update_vfolder_attribute = SingleEntityActionProcessor(
            service.update_attribute, action_monitors
        )
        self.move_to_trash_vfolder = SingleEntityActionProcessor(
            service.move_to_trash, action_monitors
        )
        self.restore_vfolder_from_trash = SingleEntityActionProcessor(
            service.restore, action_monitors
        )
        self.delete_forever_vfolder = SingleEntityActionProcessor(
            service.delete_forever, action_monitors
        )
        self.force_delete_vfolder = SingleEntityActionProcessor(
            service.force_delete, action_monitors
        )
        self.clone_vfolder = SingleEntityActionProcessor(service.clone, action_monitors)
        self.get_task_logs = SingleEntityActionProcessor(service.get_task_logs, action_monitors)

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
