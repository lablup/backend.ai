from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE, PROJECT_SCOPE_TYPE
from ai.backend.common.data.entity.types import EntityType, ScopeRef
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE, USER_SCOPE_TYPE
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.user import UserRole

from .base import (
    VFolderAction,
    VFolderGlobalAction,
    VFolderScopeAction,
    VFolderScopeActionResult,
)


@dataclass
class GlobalListAllowedTypesAction(VFolderGlobalAction):
    """Query allowed vfolder types from etcd config."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_list_allowed_types"


@dataclass
class GlobalListAllowedTypesActionResult:
    allowed_types: list[str]


@dataclass
class GlobalListAllHostsAction(VFolderGlobalAction):
    """List all storage hosts/volumes with default host info."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_list_all_hosts"


@dataclass
class GlobalListAllHostsActionResult:
    default: str | None
    allowed: list[str]


@dataclass
class GlobalGetVolumePerfMetricAction(VFolderGlobalAction):
    """Get performance metrics for a specific storage volume."""

    folder_host: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_get_volume_perf_metric"


@dataclass
class GlobalGetVolumePerfMetricActionResult:
    data: dict[str, Any]


@dataclass
class GetVFolderUsageLegacyAction(VFolderAction):
    """Get usage statistics for a specific vfolder from storage proxy.

    Legacy v1 action: the caller supplies ``folder_host`` / ``unmanaged_path``
    from a pre-resolved row, and access control is performed separately at the
    handler layer. New code should use ``GetVFolderUsageAction``, which
    takes only the vfolder UUID and enforces RBAC at the processor level.
    """

    folder_host: str
    # The quota-scope-qualified path key the storage proxy addresses.
    vfid: str
    unmanaged_path: str | None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_vfolder_usage_legacy"


@dataclass
class GetVFolderUsageLegacyActionResult:
    data: dict[str, Any]


@dataclass
class GetVFolderUsedBytesAction(VFolderAction):
    """Get used bytes for a specific vfolder from storage proxy."""

    folder_host: str
    # The quota-scope-qualified path key the storage proxy addresses.
    vfid: str
    unmanaged_path: str | None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_vfolder_used_bytes"


@dataclass
class GetVFolderUsedBytesActionResult:
    data: dict[str, Any]


@dataclass
class SearchHostsAction(VFolderScopeAction):
    """List allowed storage hosts with permission filtering and volume info."""

    user_uuid: uuid.UUID
    domain_name: str
    group_id: uuid.UUID | None
    resource_policy: Mapping[str, Any]

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        """A project folder is bounded by the project, a user folder by its owner."""
        if self.group_id is not None:
            return (ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=self.group_id),)
        return (ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=self.user_uuid),)

    @override
    @classmethod
    def available_scope_types(cls) -> Sequence[EntityType]:
        return (PROJECT_ENTITY_TYPE, USER_ENTITY_TYPE)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_hosts"


@dataclass
class SearchHostsActionResult(VFolderScopeActionResult):
    default: str | None
    allowed: list[str]
    volume_info: dict[str, Any]


@dataclass
class GetQuotaAction(VFolderAction):
    """Get quota for a specific vfolder from storage proxy."""

    folder_host: str
    # The quota-scope-qualified path key the storage proxy addresses.
    vfid: str
    unmanaged_path: str | None
    user_role: UserRole
    user_uuid: uuid.UUID
    domain_name: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_vfolder_quota"


@dataclass
class GetQuotaActionResult:
    data: dict[str, Any]


@dataclass
class UpdateQuotaAction(VFolderAction):
    """Update quota for a specific vfolder."""

    folder_host: str
    # The quota-scope-qualified path key the storage proxy addresses.
    vfid: str
    unmanaged_path: str | None
    user_role: UserRole
    user_uuid: uuid.UUID
    domain_name: str
    resource_policy: Mapping[str, Any]
    size_bytes: int

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_vfolder_quota"


@dataclass
class UpdateQuotaActionResult:
    size_bytes: int


@dataclass
class ChangeVFolderOwnershipAction(VFolderAction):
    """Change ownership of a user vfolder to another user."""

    user_email: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "change_vfolder_ownership"


@dataclass
class ChangeVFolderOwnershipActionResult:
    pass


# ------------------------------------------------------------------
# Mount operations (superadmin-only, agent watcher orchestration)
# ------------------------------------------------------------------


@dataclass
class MountResultData:
    """Result from a single mount/umount operation on a manager or agent."""

    success: bool
    mounts: list[Any] | None = None
    message: str = ""


@dataclass
class GlobalListMountsAction(VFolderGlobalAction):
    """List mount points from manager, storage proxy, and agents."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_list_mounts"


@dataclass
class GlobalListMountsActionResult:
    manager: MountResultData
    storage_proxy: MountResultData
    agents: dict[str, MountResultData] = field(default_factory=dict)


@dataclass
class GlobalMountHostAction(VFolderGlobalAction):
    """Mount a filesystem on agents via agent watchers."""

    name: str
    fs_location: str
    fs_type: str | None = None
    options: str | None = None
    resource_group: str | None = None
    fstab_path: str | None = None
    edit_fstab: bool = False

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_mount_host"


@dataclass
class GlobalMountHostActionResult:
    manager: MountResultData
    agents: dict[str, MountResultData] = field(default_factory=dict)


@dataclass
class GlobalUmountHostAction(VFolderGlobalAction):
    """Unmount a filesystem from agents via agent watchers."""

    name: str
    resource_group: str | None = None
    fstab_path: str | None = None
    edit_fstab: bool = False

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_umount_host"


@dataclass
class GlobalUmountHostActionResult:
    manager: MountResultData
    agents: dict[str, MountResultData] = field(default_factory=dict)


@dataclass
class GlobalGetFstabContentsAction(VFolderGlobalAction):
    """Get fstab contents from an agent watcher or return a manager stub."""

    agent_id: str | None
    fstab_path: str | None = None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_get_fstab_contents"


@dataclass
class GlobalGetFstabContentsActionResult:
    content: str
    node: str
    node_id: str
