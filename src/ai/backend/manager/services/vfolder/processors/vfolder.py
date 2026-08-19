from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.vfolder.types import VFolderData
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
    LookupAccessibleVFolderAction,
    LookupAccessibleVFolderActionResult,
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
    GlobalBatchLoadVFoldersAction,
    GlobalBatchLoadVFoldersActionResult,
)
from ai.backend.manager.services.vfolder.actions.create_v2 import (
    CreateVFolderV2Action,
    CreateVFolderV2ActionResult,
)
from ai.backend.manager.services.vfolder.actions.file_v2 import (
    CloneVFolderV2Action,
    CloneVFolderV2ActionResult,
)
from ai.backend.manager.services.vfolder.actions.get_row import (
    GetVFolderLegacyRowAction,
    GetVFolderLegacyRowActionResult,
)
from ai.backend.manager.services.vfolder.actions.get_usage import (
    GetVFolderUsageAction,
    GetVFolderUsageActionResult,
)
from ai.backend.manager.services.vfolder.actions.get_v2 import (
    GetVFolderV2Action,
    GetVFolderV2ActionResult,
)
from ai.backend.manager.services.vfolder.actions.lookup import (
    LookupVFolderAction,
    LookupVFolderActionResult,
)
from ai.backend.manager.services.vfolder.actions.search_in_project import (
    SearchVFoldersInProjectAction,
    SearchVFoldersInProjectActionResult,
)
from ai.backend.manager.services.vfolder.actions.search_storage_host_permissions import (
    SearchStorageHostPermissionsAction,
    SearchStorageHostPermissionsActionResult,
)
from ai.backend.manager.services.vfolder.actions.search_user_vfolders import (
    SearchUserVFoldersAction,
    SearchUserVFoldersActionResult,
)
from ai.backend.manager.services.vfolder.actions.storage_ops import (
    ChangeVFolderOwnershipAction,
    ChangeVFolderOwnershipActionResult,
    GetQuotaAction,
    GetQuotaActionResult,
    GetVFolderUsageLegacyAction,
    GetVFolderUsageLegacyActionResult,
    GetVFolderUsedBytesAction,
    GetVFolderUsedBytesActionResult,
    GlobalGetFstabContentsAction,
    GlobalGetFstabContentsActionResult,
    GlobalGetVolumePerfMetricAction,
    GlobalGetVolumePerfMetricActionResult,
    GlobalListAllHostsAction,
    GlobalListAllHostsActionResult,
    GlobalListAllowedTypesAction,
    GlobalListAllowedTypesActionResult,
    GlobalListMountsAction,
    GlobalListMountsActionResult,
    GlobalMountHostAction,
    GlobalMountHostActionResult,
    GlobalUmountHostAction,
    GlobalUmountHostActionResult,
    SearchHostsAction,
    SearchHostsActionResult,
    UpdateQuotaAction,
    UpdateQuotaActionResult,
)
from ai.backend.manager.services.vfolder.actions.upload_session_v2 import (
    CreateUploadSessionV2Action,
    CreateUploadSessionV2ActionResult,
)
from ai.backend.manager.services.vfolder.actions.vfolder_in_project import (
    CreateVFolderInProjectAction,
    CreateVFolderInProjectActionResult,
)
from ai.backend.manager.services.vfolder.actions.vfolder_v2 import (
    DeleteVFolderV2Action,
    DeleteVFolderV2ActionResult,
    PurgeVFolderV2Action,
    PurgeVFolderV2ActionResult,
)
from ai.backend.manager.services.vfolder.services.vfolder import VFolderService


class VFolderProcessors:
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
    get_task_logs: ScopeActionProcessor[GetTaskLogsAction, GetTaskLogsActionResult]
    list_allowed_types: GlobalActionProcessor[
        GlobalListAllowedTypesAction, GlobalListAllowedTypesActionResult
    ]
    list_all_hosts: GlobalActionProcessor[GlobalListAllHostsAction, GlobalListAllHostsActionResult]
    get_volume_perf_metric: GlobalActionProcessor[
        GlobalGetVolumePerfMetricAction, GlobalGetVolumePerfMetricActionResult
    ]
    get_usage_legacy: SingleEntityActionProcessor[
        GetVFolderUsageLegacyAction, GetVFolderUsageLegacyActionResult
    ]
    get_used_bytes: SingleEntityActionProcessor[
        GetVFolderUsedBytesAction, GetVFolderUsedBytesActionResult
    ]
    list_hosts: ScopeActionProcessor[SearchHostsAction, SearchHostsActionResult]
    search_storage_host_permissions: ScopeActionProcessor[
        SearchStorageHostPermissionsAction, SearchStorageHostPermissionsActionResult
    ]
    get_quota: SingleEntityActionProcessor[GetQuotaAction, GetQuotaActionResult]
    update_quota: SingleEntityActionProcessor[UpdateQuotaAction, UpdateQuotaActionResult]
    change_vfolder_ownership: SingleEntityActionProcessor[
        ChangeVFolderOwnershipAction, ChangeVFolderOwnershipActionResult
    ]
    list_mounts: GlobalActionProcessor[GlobalListMountsAction, GlobalListMountsActionResult]
    mount_host: GlobalActionProcessor[GlobalMountHostAction, GlobalMountHostActionResult]
    umount_host: GlobalActionProcessor[GlobalUmountHostAction, GlobalUmountHostActionResult]
    get_fstab_contents: GlobalActionProcessor[
        GlobalGetFstabContentsAction, GlobalGetFstabContentsActionResult
    ]
    get_accessible_vfolder: LookupActionProcessor[
        LookupAccessibleVFolderAction, LookupAccessibleVFolderActionResult
    ]
    get_vfolder_row: SingleEntityActionProcessor[
        GetVFolderLegacyRowAction, GetVFolderLegacyRowActionResult
    ]
    batch_load_vfolders_by_ids: GlobalActionProcessor[
        GlobalBatchLoadVFoldersAction, GlobalBatchLoadVFoldersActionResult
    ]
    lookup: LookupActionProcessor[LookupVFolderAction, LookupVFolderActionResult]
    get_v2: SingleEntityActionProcessor[GetVFolderV2Action, GetVFolderV2ActionResult]
    get_folder_usage: SingleEntityActionProcessor[
        GetVFolderUsageAction, GetVFolderUsageActionResult
    ]
    create_vfolder_v2: ScopeActionProcessor[CreateVFolderV2Action, CreateVFolderV2ActionResult]
    create_upload_session_v2: SingleEntityActionProcessor[
        CreateUploadSessionV2Action, CreateUploadSessionV2ActionResult
    ]
    delete_v2: SingleEntityActionProcessor[DeleteVFolderV2Action, DeleteVFolderV2ActionResult]
    purge_v2: SingleEntityActionProcessor[PurgeVFolderV2Action, PurgeVFolderV2ActionResult]
    clone_v2: SingleEntityActionProcessor[CloneVFolderV2Action, CloneVFolderV2ActionResult]
    create_vfolder_in_project: ScopeActionProcessor[
        CreateVFolderInProjectAction, CreateVFolderInProjectActionResult
    ]

    def __init__(self, group: ProcessorGroup[VFolderData], service: VFolderService) -> None:
        # Scope actions with RBAC validation
        # NOTE: RBAC validation is temporarily disabled for create_vfolder
        # because the project member role does not yet grant vfolder:create.
        # The service layer still enforces the legacy admin-only check for
        # group-owned folders.
        self.create_vfolder = group.scope(CreateVFolderAction, service.create)
        self.list_vfolder = group.scope(ListVFolderAction, service.list)
        self.search_vfolders_in_project = group.scope(
            SearchVFoldersInProjectAction, service.search_in_project
        )
        self.search_user_vfolders = group.scope(
            SearchUserVFoldersAction, service.search_user_vfolders
        )

        # Single entity actions with RBAC validation
        self.get_vfolder = group.single_entity(GetVFolderAction, service.get)
        self.update_vfolder_attribute = group.single_entity(
            UpdateVFolderAttributeAction, service.update_attribute
        )
        self.move_to_trash_vfolder = group.single_entity(
            MoveToTrashVFolderAction, service.move_to_trash
        )
        self.restore_vfolder_from_trash = group.single_entity(
            RestoreVFolderFromTrashAction, service.restore
        )
        self.delete_forever_vfolder = group.single_entity(
            DeleteForeverVFolderAction, service.delete_forever
        )
        self.purge_vfolder = group.single_entity(PurgeVFolderAction, service.purge)
        self.force_delete_vfolder = group.single_entity(
            ForceDeleteVFolderAction, service.force_delete
        )
        self.clone_vfolder = group.single_entity(CloneVFolderAction, service.clone)

        # Actions without RBAC validation (internal/legacy/storage ops)
        self.get_task_logs = group.scope(GetTaskLogsAction, service.get_task_logs)
        self.list_allowed_types = group.global_scope(
            GlobalListAllowedTypesAction, service.list_allowed_types
        )
        self.list_all_hosts = group.global_scope(GlobalListAllHostsAction, service.list_all_hosts)
        self.get_volume_perf_metric = group.global_scope(
            GlobalGetVolumePerfMetricAction, service.get_volume_perf_metric
        )
        self.get_usage_legacy = group.single_entity(
            GetVFolderUsageLegacyAction, service.get_usage_legacy
        )
        self.get_used_bytes = group.single_entity(GetVFolderUsedBytesAction, service.get_used_bytes)
        self.list_hosts = group.scope(SearchHostsAction, service.list_hosts)
        self.search_storage_host_permissions = group.scope(
            SearchStorageHostPermissionsAction, service.search_storage_host_permissions
        )
        self.get_quota = group.single_entity(GetQuotaAction, service.get_quota)
        self.update_quota = group.single_entity(UpdateQuotaAction, service.update_quota)
        self.change_vfolder_ownership = group.single_entity(
            ChangeVFolderOwnershipAction, service.change_vfolder_ownership
        )
        self.list_mounts = group.global_scope(GlobalListMountsAction, service.list_mounts)
        self.mount_host = group.global_scope(GlobalMountHostAction, service.mount_host)
        self.umount_host = group.global_scope(GlobalUmountHostAction, service.umount_host)
        self.get_fstab_contents = group.global_scope(
            GlobalGetFstabContentsAction, service.get_fstab_contents
        )
        self.get_accessible_vfolder = group.lookup(
            LookupAccessibleVFolderAction, service.get_accessible_vfolder
        )
        self.get_vfolder_row = group.single_entity(
            GetVFolderLegacyRowAction, service.get_vfolder_row
        )

        # Cross-entity loaders (no RBAC validation; caller has parent access)
        self.batch_load_vfolders_by_ids = group.global_scope(
            GlobalBatchLoadVFoldersAction, service.batch_load_by_ids
        )
        self.lookup = group.lookup(LookupVFolderAction, service.lookup_vfolder)

        # V2 actions
        self.get_v2 = group.single_entity(GetVFolderV2Action, service.get_v2)
        self.get_folder_usage = group.single_entity(GetVFolderUsageAction, service.get_folder_usage)
        self.create_vfolder_v2 = group.scope(CreateVFolderV2Action, service.create_v2)
        self.create_upload_session_v2 = group.single_entity(
            CreateUploadSessionV2Action, service.create_upload_session_v2
        )
        self.delete_v2 = group.single_entity(DeleteVFolderV2Action, service.delete_v2)
        self.purge_v2 = group.single_entity(PurgeVFolderV2Action, service.purge_v2)
        self.clone_v2 = group.single_entity(CloneVFolderV2Action, service.clone_v2)
        self.create_vfolder_in_project = group.scope(
            CreateVFolderInProjectAction, service.create_in_project
        )
