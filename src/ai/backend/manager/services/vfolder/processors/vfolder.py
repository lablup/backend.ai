from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor.scope import ScopeActionProcessor
from ai.backend.manager.actions.processor.single_entity import SingleEntityActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validator.args import ValidatorArgs

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

    def __init__(
        self,
        service: VFolderService,
        action_monitors: list[ActionMonitor],
        action_validators: ValidatorArgs,
    ) -> None:
        self.create_vfolder = ScopeActionProcessor(
            service.create, action_monitors, action_validators.scope
        )
        self.get_vfolder = SingleEntityActionProcessor(
            service.get, action_monitors, action_validators.single_entity
        )
        self.list_vfolder = ScopeActionProcessor(
            service.list, action_monitors, action_validators.scope
        )
        self.update_vfolder_attribute = SingleEntityActionProcessor(
            service.update_attribute, action_monitors, action_validators.single_entity
        )
        self.move_to_trash_vfolder = SingleEntityActionProcessor(
            service.move_to_trash, action_monitors, action_validators.single_entity
        )
        self.restore_vfolder_from_trash = SingleEntityActionProcessor(
            service.restore, action_monitors, action_validators.single_entity
        )
        self.delete_forever_vfolder = SingleEntityActionProcessor(
            service.delete_forever, action_monitors, action_validators.single_entity
        )
        self.force_delete_vfolder = SingleEntityActionProcessor(
            service.force_delete, action_monitors, action_validators.single_entity
        )
        self.clone_vfolder = SingleEntityActionProcessor(
            service.clone, action_monitors, action_validators.single_entity
        )
        self.get_task_logs = SingleEntityActionProcessor(
            service.get_task_logs, action_monitors, action_validators.single_entity
        )

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
