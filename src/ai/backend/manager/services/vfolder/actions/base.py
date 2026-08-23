import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeRef
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE
from ai.backend.common.data.entity.vfolder import VFOLDER_ENTITY_TYPE, VFolderUUID
from ai.backend.common.types import (
    AccessKey,
    KernelId,
    QuotaScopeID,
    VFolderUsageMode,
)
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.lookup.base import (
    BaseLookupAction,
    BaseLookupActionResult,
    LookupKey,
)
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.vfolder import (
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderPermission,
    VFolderPermissionSetAlias,
    VFolderRow,
    VFolderStatusSet,
)
from ai.backend.manager.models.vfolder.updaters import VFolderAttributeUpdater
from ai.backend.manager.repositories.base.rbac.entity_purger import RBACEntityPurger
from ai.backend.manager.services.vfolder.types import (
    VFolderBaseInfo,
    VFolderOwnershipInfo,
    VFolderUsageInfo,
)


@dataclass
class VFolderAction(BaseSingleEntityAction):
    """Base for an operation on one vfolder.

    Files and directories are read and written through the folder holding them,
    so those operations carry its id rather than declaring a type of their own.
    """

    vfolder_uuid: VFolderUUID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.vfolder_uuid

    @override
    @classmethod
    def action_name(cls) -> str:
        return "vfolder"


@dataclass
class VFolderFileAction(VFolderAction):
    """Base for an operation on the files of one vfolder."""

    @override
    @classmethod
    def action_name(cls) -> str:
        return "vfolder_file"


@dataclass
class VFolderDirectoryAction(VFolderAction):
    """Base for an operation on the directories of one vfolder."""

    @override
    @classmethod
    def action_name(cls) -> str:
        return "vfolder_directory"


@dataclass
class VFolderGlobalAction(BaseGlobalAction):
    """Base for a vfolder operation that names none."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return VFOLDER_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "vfolder_global"


@dataclass
class VFolderScopeAction(BaseScopeAction):
    """Base for a vfolder operation bounded by a scope."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return VFOLDER_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "vfolder_scope"


@dataclass
class VFolderScopeActionResult(BaseScopeActionResult):
    """A scoped vfolder read names no entity."""

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return ()


@dataclass
class CreateVFolderAction(VFolderScopeAction):
    name: str

    keypair_resource_policy: Mapping[str, Any]
    domain_name: str
    group_id_or_name: str | uuid.UUID | None
    folder_host: str | None
    unmanaged_path: str | None
    mount_permission: VFolderPermission
    usage_mode: VFolderUsageMode
    cloneable: bool

    scope: ScopeRef

    # User identifier
    # TODO: Distinguish between creator and owner
    user_uuid: uuid.UUID
    user_role: UserRole
    creator_email: str

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (self.scope,)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_vfolder"


@dataclass
class CreateVFolderActionResult(VFolderScopeActionResult):
    id: uuid.UUID
    name: str
    quota_scope_id: QuotaScopeID
    host: str
    unmanaged_path: str | None
    mount_permission: VFolderPermission
    usage_mode: VFolderUsageMode
    creator_email: str
    ownership_type: VFolderOwnershipType
    user_uuid: uuid.UUID | None
    group_uuid: uuid.UUID | None
    cloneable: bool
    status: VFolderOperationStatus


@dataclass
class UpdateVFolderAttributeAction(VFolderAction):
    user_uuid: uuid.UUID
    updater: VFolderAttributeUpdater

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_vfolder_attribute"


@dataclass
class UpdateVFolderAttributeActionResult:
    vfolder_uuid: uuid.UUID


@dataclass
class GetVFolderAction(VFolderAction):
    user_uuid: uuid.UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_vfolder"


@dataclass
class GetVFolderActionResult:
    user_uuid: uuid.UUID
    base_info: VFolderBaseInfo
    ownership_info: VFolderOwnershipInfo
    usage_info: VFolderUsageInfo


@dataclass
class ListVFolderAction(VFolderScopeAction):
    user_uuid: uuid.UUID
    scope: ScopeRef

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (self.scope,)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "list_vfolder"


@dataclass
class ListVFolderActionResult(VFolderScopeActionResult):
    user_uuid: uuid.UUID
    vfolders: list[tuple[VFolderBaseInfo, VFolderOwnershipInfo]]


@dataclass
class MoveToTrashVFolderAction(VFolderAction):
    user_uuid: uuid.UUID
    keypair_resource_policy: Mapping[str, Any]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "move_to_trash_vfolder"


@dataclass
class MoveToTrashVFolderActionResult:
    vfolder_uuid: uuid.UUID


@dataclass
class RestoreVFolderFromTrashAction(VFolderAction):
    """Bring a folder back out of the trash.

    ``RESTORE`` rather than ``UPDATE``: an update would record the restore as an
    ordinary field write and gate it on ``UPDATE`` while the delete needs
    ``SOFT_DELETE``.
    """

    user_uuid: uuid.UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.RESTORE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "restore_vfolder_from_trash"


@dataclass
class RestoreVFolderFromTrashActionResult:
    vfolder_uuid: uuid.UUID


@dataclass
class DeleteForeverVFolderAction(VFolderAction):
    user_uuid: uuid.UUID

    cascade_model_card: bool = False

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_forever_vfolder"


@dataclass
class DeleteForeverVFolderActionResult:
    vfolder_uuid: uuid.UUID


@dataclass
class PurgeVFolderAction(VFolderAction):
    purger: RBACEntityPurger[VFolderRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_vfolder"


@dataclass
class PurgeVFolderActionResult:
    vfolder_uuid: uuid.UUID


@dataclass
class ForceDeleteVFolderAction(VFolderAction):
    """
    This action transits the state of vfolder from ready to delete-forever directly.
    """

    user_uuid: uuid.UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "force_delete_vfolder"


@dataclass
class ForceDeleteVFolderActionResult:
    vfolder_uuid: uuid.UUID


@dataclass
class CloneVFolderAction(VFolderAction):
    requester_user_uuid: uuid.UUID

    source_vfolder_uuid: uuid.UUID
    target_name: str
    target_host: str | None
    target_quota_scope_id: QuotaScopeID | None
    cloneable: bool
    usage_mode: VFolderUsageMode
    mount_permission: VFolderPermission

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "clone_vfolder"


@dataclass
class CloneVFolderActionResult:
    vfolder_uuid: uuid.UUID

    target_vfolder_id: uuid.UUID
    target_vfolder_name: str
    target_vfolder_host: str
    usage_mode: VFolderUsageMode
    mount_permission: VFolderPermission
    creator_email: str
    ownership_type: VFolderOwnershipType
    owner_user_uuid: uuid.UUID | None
    owner_group_uuid: uuid.UUID | None
    cloneable: bool
    bgtask_id: uuid.UUID


@dataclass
class GetTaskLogsAction(VFolderScopeAction):
    """Read the task log folder of one user.

    The folder is resolved from the kernel inside the service, so the caller
    names the user rather than the folder.
    """

    # TODO: Migrate to a session/kernel action once the log folder is read
    # through the session that wrote it.
    user_id: uuid.UUID
    domain_name: str
    user_role: UserRole
    kernel_id: KernelId
    owner_access_key: AccessKey

    # TODO: Remove this.
    request: Any

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=self.user_id),)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_task_logs"


@dataclass
class GetTaskLogsActionResult(VFolderScopeActionResult):
    # TODO: Add proper type
    response: Any
    vfolder_data: VFolderData


@dataclass(frozen=True)
class VFolderKey(LookupKey):
    """The id or name a legacy caller passes for a folder."""

    folder_id_or_name: str | uuid.UUID

    @override
    def kind(self) -> str:
        return "folder_id_or_name"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"folder_id_or_name": str(self.folder_id_or_name)}


@dataclass
class LookupAccessibleVFolderAction(BaseLookupAction):
    """Resolve the folder a legacy caller named, by id or by name."""

    user_uuid: uuid.UUID
    user_role: UserRole
    domain_name: str
    is_admin: bool
    perm: VFolderPermissionSetAlias | VFolderPermission
    folder_id_or_name: str | uuid.UUID
    required_status: VFolderStatusSet | None = None
    allow_privileged_access: bool = False

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return VFOLDER_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_accessible_vfolder"

    @override
    def lookup_key(self) -> VFolderKey:
        return VFolderKey(folder_id_or_name=self.folder_id_or_name)


@dataclass
class LookupAccessibleVFolderActionResult(BaseLookupActionResult):
    row: Mapping[str, Any]

    @override
    def entity_id(self) -> EntityIdentifier:
        return VFolderUUID(self.row["id"])
