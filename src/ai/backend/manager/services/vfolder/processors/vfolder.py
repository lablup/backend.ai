from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.processor.scope import ScopeActionProcessor
from ai.backend.manager.actions.processor.single_entity import SingleEntityActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.services.vfolder.actions.base import (
    CloneVFolderAction,
    CloneVFolderActionResult,
    CreateVFolderAction,
    CreateVFolderActionResult,
    DeleteForeverVFolderAction,
    DeleteForeverVFolderActionResult,
    ForceDeleteVFolderAction,
    ForceDeleteVFolderActionResult,
    GetAccessibleVFolderAction,
    GetAccessibleVFolderActionResult,
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
from ai.backend.manager.services.vfolder.actions.batch_load_by_ids import (
    BatchLoadVFoldersByIdsAction,
    BatchLoadVFoldersByIdsActionResult,
)
from ai.backend.manager.services.vfolder.actions.create_v2 import (
    CreateVFolderV2Action,
    CreateVFolderV2ActionResult,
)
from ai.backend.manager.services.vfolder.actions.file_v2 import (
    CloneVFolderV2Action,
    CloneVFolderV2ActionResult,
)
from ai.backend.manager.services.vfolder.actions.get_my_storage_host_permissions import (
    GetMyStorageHostPermissionsAction,
    GetMyStorageHostPermissionsActionResult,
)
from ai.backend.manager.services.vfolder.actions.search_in_project import (
    SearchVFoldersInProjectAction,
    SearchVFoldersInProjectActionResult,
)
from ai.backend.manager.services.vfolder.actions.search_user_vfolders import (
    SearchUserVFoldersAction,
    SearchUserVFoldersActionResult,
)
from ai.backend.manager.services.vfolder.actions.storage_ops import (
    ChangeVFolderOwnershipAction,
    ChangeVFolderOwnershipActionResult,
    GetFstabContentsAction,
    GetFstabContentsActionResult,
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
    ListMountsAction,
    ListMountsActionResult,
    MountHostAction,
    MountHostActionResult,
    UmountHostAction,
    UmountHostActionResult,
    UpdateQuotaAction,
    UpdateQuotaActionResult,
)
from ai.backend.manager.services.vfolder.actions.upload_session_v2 import (
    CreateUploadSessionV2Action,
    CreateUploadSessionV2ActionResult,
)
from ai.backend.manager.services.vfolder.actions.vfolder_v2 import (
    DeleteVFolderV2Action,
    DeleteVFolderV2ActionResult,
    PurgeVFolderV2Action,
    PurgeVFolderV2ActionResult,
)
from ai.backend.manager.services.vfolder.services.vfolder import VFolderService


class VFolderProcessors(AbstractProcessorPackage):
    create_vfolder: ScopeActionProcessor[CreateVFolderAction, CreateVFolderActionResult]
    get_vfolder: SingleEntityActionProcessor[GetVFolderAction, GetVFolderActionResult]
    list_vfolder: ScopeActionProcessor[ListVFolderAction, ListVFolderActionResult]
    search_vfolders_in_project: ScopeActionProcessor[
        SearchVFoldersInProjectAction, SearchVFoldersInProjectActionResult
    ]
    search_user_vfolders: ScopeActionProcessor[
        SearchUserVFoldersAction, SearchUserVFoldersActionResult
    ]
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
    get_my_storage_host_permissions: ActionProcessor[
        GetMyStorageHostPermissionsAction, GetMyStorageHostPermissionsActionResult
    ]
    get_quota: ActionProcessor[GetQuotaAction, GetQuotaActionResult]
    update_quota: ActionProcessor[UpdateQuotaAction, UpdateQuotaActionResult]
    change_vfolder_ownership: ActionProcessor[
        ChangeVFolderOwnershipAction, ChangeVFolderOwnershipActionResult
    ]
    list_mounts: ActionProcessor[ListMountsAction, ListMountsActionResult]
    mount_host: ActionProcessor[MountHostAction, MountHostActionResult]
    umount_host: ActionProcessor[UmountHostAction, UmountHostActionResult]
    get_fstab_contents: ActionProcessor[GetFstabContentsAction, GetFstabContentsActionResult]
    get_accessible_vfolder: ActionProcessor[
        GetAccessibleVFolderAction, GetAccessibleVFolderActionResult
    ]
    batch_load_vfolders_by_ids: ActionProcessor[
        BatchLoadVFoldersByIdsAction, BatchLoadVFoldersByIdsActionResult
    ]
    create_vfolder_v2: ActionProcessor[CreateVFolderV2Action, CreateVFolderV2ActionResult]
    create_upload_session_v2: ActionProcessor[
        CreateUploadSessionV2Action, CreateUploadSessionV2ActionResult
    ]
    delete_v2: ActionProcessor[DeleteVFolderV2Action, DeleteVFolderV2ActionResult]
    purge_v2: ActionProcessor[PurgeVFolderV2Action, PurgeVFolderV2ActionResult]
    clone_v2: ActionProcessor[CloneVFolderV2Action, CloneVFolderV2ActionResult]

    def __init__(
        self,
        service: VFolderService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        scope_rbac_validators = [validators.rbac.scope]
        single_entity_rbac_validators = [validators.rbac.single_entity]

        # Scope actions with RBAC validation
        self.create_vfolder = ScopeActionProcessor(
            service.create, action_monitors, validators=scope_rbac_validators
        )
        self.list_vfolder = ScopeActionProcessor(
            service.list, action_monitors, validators=scope_rbac_validators
        )
        self.search_vfolders_in_project = ScopeActionProcessor(
            service.search_in_project, action_monitors, validators=scope_rbac_validators
        )
        self.search_user_vfolders = ScopeActionProcessor(
            service.search_user_vfolders, action_monitors, validators=scope_rbac_validators
        )

        # Single entity actions with RBAC validation
        self.get_vfolder = SingleEntityActionProcessor(
            service.get, action_monitors, validators=single_entity_rbac_validators
        )
        self.update_vfolder_attribute = SingleEntityActionProcessor(
            service.update_attribute, action_monitors, validators=single_entity_rbac_validators
        )
        self.move_to_trash_vfolder = SingleEntityActionProcessor(
            service.move_to_trash, action_monitors, validators=single_entity_rbac_validators
        )
        self.restore_vfolder_from_trash = SingleEntityActionProcessor(
            service.restore, action_monitors, validators=single_entity_rbac_validators
        )
        self.delete_forever_vfolder = SingleEntityActionProcessor(
            service.delete_forever, action_monitors, validators=single_entity_rbac_validators
        )
        self.purge_vfolder = SingleEntityActionProcessor(
            service.purge, action_monitors, validators=single_entity_rbac_validators
        )
        self.force_delete_vfolder = SingleEntityActionProcessor(
            service.force_delete, action_monitors, validators=single_entity_rbac_validators
        )
        self.clone_vfolder = SingleEntityActionProcessor(
            service.clone, action_monitors, validators=single_entity_rbac_validators
        )

        # Actions without RBAC validation (internal/legacy/storage ops)
        self.get_task_logs = SingleEntityActionProcessor(service.get_task_logs, action_monitors)
        self.list_allowed_types = ActionProcessor(service.list_allowed_types, action_monitors)
        self.list_all_hosts = ActionProcessor(service.list_all_hosts, action_monitors)
        self.get_volume_perf_metric = ActionProcessor(
            service.get_volume_perf_metric, action_monitors
        )
        self.get_usage = ActionProcessor(service.get_usage, action_monitors)
        self.get_used_bytes = ActionProcessor(service.get_used_bytes, action_monitors)
        self.list_hosts = ActionProcessor(service.list_hosts, action_monitors)
        self.get_my_storage_host_permissions = ActionProcessor(
            service.get_my_storage_host_permissions, action_monitors
        )
        self.get_quota = ActionProcessor(service.get_quota, action_monitors)
        self.update_quota = ActionProcessor(service.update_quota, action_monitors)
        self.change_vfolder_ownership = ActionProcessor(
            service.change_vfolder_ownership, action_monitors
        )
        self.list_mounts = ActionProcessor(service.list_mounts, action_monitors)
        self.mount_host = ActionProcessor(service.mount_host, action_monitors)
        self.umount_host = ActionProcessor(service.umount_host, action_monitors)
        self.get_fstab_contents = ActionProcessor(service.get_fstab_contents, action_monitors)
        self.get_accessible_vfolder = ActionProcessor(
            service.get_accessible_vfolder, action_monitors
        )

        # Cross-entity loaders (no RBAC validation; caller has parent access)
        self.batch_load_vfolders_by_ids = ActionProcessor(
            service.batch_load_by_ids, action_monitors
        )

        # V2 actions
        self.create_vfolder_v2 = ActionProcessor(service.create_v2, action_monitors)
        self.create_upload_session_v2 = ActionProcessor(
            service.create_upload_session_v2, action_monitors
        )
        self.delete_v2 = ActionProcessor(service.delete_v2, action_monitors)
        self.purge_v2 = ActionProcessor(service.purge_v2, action_monitors)
        self.clone_v2 = ActionProcessor(service.clone_v2, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateVFolderAction.spec(),
            GetVFolderAction.spec(),
            ListVFolderAction.spec(),
            SearchVFoldersInProjectAction.spec(),
            SearchUserVFoldersAction.spec(),
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
            GetMyStorageHostPermissionsAction.spec(),
            GetQuotaAction.spec(),
            UpdateQuotaAction.spec(),
            ChangeVFolderOwnershipAction.spec(),
            ListMountsAction.spec(),
            MountHostAction.spec(),
            UmountHostAction.spec(),
            GetFstabContentsAction.spec(),
            GetAccessibleVFolderAction.spec(),
            BatchLoadVFoldersByIdsAction.spec(),
            CreateVFolderV2Action.spec(),
            CreateUploadSessionV2Action.spec(),
            DeleteVFolderV2Action.spec(),
            PurgeVFolderV2Action.spec(),
            CloneVFolderV2Action.spec(),
        ]
