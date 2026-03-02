from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.processor.scope import ScopeActionProcessor
from ai.backend.manager.actions.processor.single_entity import SingleEntityActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.vfolder.actions.base import (
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
    PurgeVFolderAction,
    PurgeVFolderActionResult,
    RestoreVFolderFromTrashAction,
    RestoreVFolderFromTrashActionResult,
    UpdateVFolderAttributeAction,
    UpdateVFolderAttributeActionResult,
)
from ai.backend.manager.services.vfolder.actions.storage_ops import (
    ChangeVFolderOwnershipAction,
    ChangeVFolderOwnershipActionResult,
    GetQuotaAction,
    GetQuotaActionResult,
    GetVFolderUsageAction,
    GetVFolderUsageActionResult,
    GetVFolderUsedBytesAction,
    GetVFolderUsedBytesActionResult,
    GetVolumePerfMetricAction,
    GetVolumePerfMetricActionResult,
    ListAllHostsAction,
    ListAllHostsActionResult,
    ListAllowedTypesAction,
    ListAllowedTypesActionResult,
    ListHostsAction,
    ListHostsActionResult,
    UpdateQuotaAction,
    UpdateQuotaActionResult,
)
from ai.backend.manager.services.vfolder.services.vfolder import VFolderService


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
    purge_vfolder: SingleEntityActionProcessor[PurgeVFolderAction, PurgeVFolderActionResult]
    force_delete_vfolder: SingleEntityActionProcessor[
        ForceDeleteVFolderAction, ForceDeleteVFolderActionResult
    ]
    clone_vfolder: SingleEntityActionProcessor[CloneVFolderAction, CloneVFolderActionResult]
    get_task_logs: SingleEntityActionProcessor[GetTaskLogsAction, GetTaskLogsActionResult]
    list_allowed_types: ActionProcessor[ListAllowedTypesAction, ListAllowedTypesActionResult]
    list_all_hosts: ActionProcessor[ListAllHostsAction, ListAllHostsActionResult]
    get_volume_perf_metric: ActionProcessor[
        GetVolumePerfMetricAction, GetVolumePerfMetricActionResult
    ]
    get_usage: ActionProcessor[GetVFolderUsageAction, GetVFolderUsageActionResult]
    get_used_bytes: ActionProcessor[GetVFolderUsedBytesAction, GetVFolderUsedBytesActionResult]
    list_hosts: ActionProcessor[ListHostsAction, ListHostsActionResult]
    get_quota: ActionProcessor[GetQuotaAction, GetQuotaActionResult]
    update_quota: ActionProcessor[UpdateQuotaAction, UpdateQuotaActionResult]
    change_vfolder_ownership: ActionProcessor[
        ChangeVFolderOwnershipAction, ChangeVFolderOwnershipActionResult
    ]

    def __init__(self, service: VFolderService, action_monitors: list[ActionMonitor]) -> None:
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
        self.purge_vfolder = SingleEntityActionProcessor(service.purge, action_monitors)
        self.force_delete_vfolder = SingleEntityActionProcessor(
            service.force_delete, action_monitors
        )
        self.clone_vfolder = SingleEntityActionProcessor(service.clone, action_monitors)
        self.get_task_logs = SingleEntityActionProcessor(service.get_task_logs, action_monitors)
        self.list_allowed_types = ActionProcessor(service.list_allowed_types, action_monitors)
        self.list_all_hosts = ActionProcessor(service.list_all_hosts, action_monitors)
        self.get_volume_perf_metric = ActionProcessor(
            service.get_volume_perf_metric, action_monitors
        )
        self.get_usage = ActionProcessor(service.get_usage, action_monitors)
        self.get_used_bytes = ActionProcessor(service.get_used_bytes, action_monitors)
        self.list_hosts = ActionProcessor(service.list_hosts, action_monitors)
        self.get_quota = ActionProcessor(service.get_quota, action_monitors)
        self.update_quota = ActionProcessor(service.update_quota, action_monitors)
        self.change_vfolder_ownership = ActionProcessor(
            service.change_vfolder_ownership, action_monitors
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
            PurgeVFolderAction.spec(),
            ForceDeleteVFolderAction.spec(),
            CloneVFolderAction.spec(),
            GetTaskLogsAction.spec(),
            ListAllowedTypesAction.spec(),
            ListAllHostsAction.spec(),
            GetVolumePerfMetricAction.spec(),
            GetVFolderUsageAction.spec(),
            GetVFolderUsedBytesAction.spec(),
            ListHostsAction.spec(),
            GetQuotaAction.spec(),
            UpdateQuotaAction.spec(),
            ChangeVFolderOwnershipAction.spec(),
        ]
