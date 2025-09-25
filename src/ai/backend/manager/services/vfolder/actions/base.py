import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Optional, override

from ai.backend.common.types import (
    AccessKey,
    KernelId,
    QuotaScopeID,
    VFolderUsageMode,
)
from ai.backend.manager.actions.action import BaseAction
from ai.backend.manager.actions.action.scope import BaseScopeAction, BaseScopeActionResult
from ai.backend.manager.actions.action.single_entity import (
    BaseSingleEntityAction,
    BaseSingleEntityActionResult,
)
from ai.backend.manager.data.permission.types import OperationType
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.vfolder import (
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderPermission,
)
from ai.backend.manager.types import OptionalState, PartialModifier

from ..types import VFolderBaseInfo, VFolderOwnershipInfo, VFolderUsageInfo


class VFolderAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "vfolder"


class VFolderScopeAction(BaseScopeAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "vfolder"


class VFolderScopeActionResult(BaseScopeActionResult):
    pass


class VFolderSingleEntityAction(BaseSingleEntityAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "vfolder"


class VFolderSingleEntityActionResult(BaseSingleEntityActionResult):
    pass


@dataclass
class CreateVFolderAction(VFolderScopeAction):
    name: str

    keypair_resource_policy: Mapping[str, Any]
    domain_name: str
    group_id_or_name: Optional[str | uuid.UUID]
    folder_host: Optional[str]
    unmanaged_path: Optional[str]
    mount_permission: VFolderPermission
    usage_mode: VFolderUsageMode
    cloneable: bool

    _scope_id: str
    _scope_type: str

    # User identifier
    # TODO: Distinguish between creator and owner
    user_uuid: uuid.UUID
    user_role: UserRole
    creator_email: str

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create"

    @override
    @classmethod
    def permission_operation_type(cls) -> OperationType:
        return OperationType.CREATE

    @override
    def scope_type(self) -> str:
        return self._scope_type

    @override
    def scope_id(self) -> str:
        return self._scope_id


@dataclass
class CreateVFolderActionResult(VFolderScopeActionResult):
    id: uuid.UUID
    name: str
    quota_scope_id: QuotaScopeID
    host: str
    unmanaged_path: Optional[str]
    mount_permission: VFolderPermission
    usage_mode: VFolderUsageMode
    creator_email: str
    ownership_type: VFolderOwnershipType
    user_uuid: Optional[uuid.UUID]
    group_uuid: Optional[uuid.UUID]
    cloneable: bool
    status: VFolderOperationStatus

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.id)

    @override
    def scope_type(self) -> str:
        return self.quota_scope_id.scope_type.value

    @override
    def scope_id(self) -> str:
        return str(self.quota_scope_id.scope_id)


@dataclass
class VFolderAttributeModifier(PartialModifier):
    name: OptionalState[str] = field(default_factory=OptionalState.nop)
    cloneable: OptionalState[bool] = field(default_factory=OptionalState.nop)
    mount_permission: OptionalState[VFolderPermission] = field(default_factory=OptionalState.nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.cloneable.update_dict(to_update, "cloneable")
        self.mount_permission.update_dict(to_update, "permission")
        return to_update


@dataclass
class UpdateVFolderAttributeAction(VFolderSingleEntityAction):
    user_uuid: uuid.UUID
    vfolder_uuid: uuid.UUID
    modifier: VFolderAttributeModifier = field(default_factory=VFolderAttributeModifier)

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "update"

    @override
    @classmethod
    def permission_operation_type(cls) -> OperationType:
        return OperationType.UPDATE

    @override
    def target_entity_id(self) -> str:
        return str(self.vfolder_uuid)


@dataclass
class UpdateVFolderAttributeActionResult(VFolderSingleEntityActionResult):
    vfolder_uuid: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)

    @override
    def target_entity_id(self) -> str:
        return str(self.vfolder_uuid)


@dataclass
class GetVFolderAction(VFolderSingleEntityAction):
    user_uuid: uuid.UUID
    vfolder_uuid: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get"

    @override
    @classmethod
    def permission_operation_type(cls) -> OperationType:
        return OperationType.READ

    @override
    def target_entity_id(self) -> str:
        return str(self.vfolder_uuid)


@dataclass
class GetVFolderActionResult(VFolderSingleEntityActionResult):
    user_uuid: uuid.UUID
    base_info: VFolderBaseInfo
    ownership_info: VFolderOwnershipInfo
    usage_info: VFolderUsageInfo

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.user_uuid)

    @override
    def target_entity_id(self) -> str:
        return str(self.base_info.id)


@dataclass
class ListVFolderAction(VFolderScopeAction):
    user_uuid: uuid.UUID
    _scope_type: str
    _scope_id: str

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.user_uuid)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "list"

    @override
    @classmethod
    def permission_operation_type(cls) -> OperationType:
        return OperationType.READ

    @override
    def scope_type(self) -> str:
        return self._scope_type

    @override
    def scope_id(self) -> str:
        return self._scope_id


@dataclass
class ListVFolderActionResult(VFolderScopeActionResult):
    user_uuid: uuid.UUID
    vfolders: list[tuple[VFolderBaseInfo, VFolderOwnershipInfo]]
    _scope_type: str
    _scope_id: str

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.user_uuid)

    @override
    def scope_type(self) -> str:
        return self._scope_type

    @override
    def scope_id(self) -> str:
        return str(self._scope_id)


@dataclass
class MoveToTrashVFolderAction(VFolderSingleEntityAction):
    user_uuid: uuid.UUID
    keypair_resource_policy: Mapping[str, Any]

    vfolder_uuid: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "move_to_trash"

    @override
    @classmethod
    def permission_operation_type(cls) -> OperationType:
        return OperationType.SOFT_DELETE

    @override
    def target_entity_id(self) -> str:
        return str(self.vfolder_uuid)


@dataclass
class MoveToTrashVFolderActionResult(VFolderSingleEntityActionResult):
    vfolder_uuid: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)

    @override
    def target_entity_id(self) -> str:
        return str(self.vfolder_uuid)


@dataclass
class RestoreVFolderFromTrashAction(VFolderSingleEntityAction):
    user_uuid: uuid.UUID

    vfolder_uuid: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "restore"

    @override
    @classmethod
    def permission_operation_type(cls) -> OperationType:
        return OperationType.SOFT_DELETE

    @override
    def target_entity_id(self) -> str:
        return str(self.vfolder_uuid)


@dataclass
class RestoreVFolderFromTrashActionResult(VFolderSingleEntityActionResult):
    vfolder_uuid: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)

    @override
    def target_entity_id(self) -> str:
        return str(self.vfolder_uuid)


@dataclass
class DeleteForeverVFolderAction(VFolderSingleEntityAction):
    user_uuid: uuid.UUID

    vfolder_uuid: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delete_forever"

    @override
    @classmethod
    def permission_operation_type(cls) -> OperationType:
        return OperationType.HARD_DELETE

    @override
    def target_entity_id(self) -> str:
        return str(self.vfolder_uuid)


@dataclass
class DeleteForeverVFolderActionResult(VFolderSingleEntityActionResult):
    vfolder_uuid: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)

    @override
    def target_entity_id(self) -> str:
        return str(self.vfolder_uuid)


@dataclass
class ForceDeleteVFolderAction(VFolderSingleEntityAction):
    """
    This action transits the state of vfolder from ready to delete-forever directly.
    """

    user_uuid: uuid.UUID

    vfolder_uuid: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "force_delete"

    @override
    @classmethod
    def permission_operation_type(cls) -> OperationType:
        return OperationType.HARD_DELETE

    @override
    def target_entity_id(self) -> str:
        return str(self.vfolder_uuid)


@dataclass
class ForceDeleteVFolderActionResult(VFolderSingleEntityActionResult):
    vfolder_uuid: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)

    @override
    def target_entity_id(self) -> str:
        return str(self.vfolder_uuid)


@dataclass
class CloneVFolderAction(VFolderSingleEntityAction):
    requester_user_uuid: uuid.UUID

    source_vfolder_uuid: uuid.UUID
    target_name: str
    target_host: Optional[str]
    cloneable: bool
    usage_mode: VFolderUsageMode
    mount_permission: VFolderPermission

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.source_vfolder_uuid)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "clone"

    @override
    @classmethod
    def permission_operation_type(cls) -> OperationType:
        return OperationType.READ

    @override
    def target_entity_id(self) -> str:
        return str(self.source_vfolder_uuid)


@dataclass
class CloneVFolderActionResult(VFolderSingleEntityActionResult):
    vfolder_uuid: uuid.UUID

    target_vfolder_id: uuid.UUID
    target_vfolder_name: str
    target_vfolder_host: str
    usage_mode: VFolderUsageMode
    mount_permission: VFolderPermission
    creator_email: str
    ownership_type: VFolderOwnershipType
    owner_user_uuid: Optional[uuid.UUID]
    owner_group_uuid: Optional[uuid.UUID]
    cloneable: bool
    bgtask_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)

    @override
    def target_entity_id(self) -> str:
        return str(self.vfolder_uuid)


@dataclass
class GetTaskLogsAction(VFolderSingleEntityAction):
    user_id: uuid.UUID
    domain_name: str
    user_role: UserRole
    kernel_id: KernelId
    owner_access_key: AccessKey

    # TODO: Remove this.
    request: Any

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_task_logs"

    @override
    @classmethod
    def permission_operation_type(cls) -> OperationType:
        return OperationType.READ

    @override
    def target_entity_id(self) -> str:
        return str(self.kernel_id)


@dataclass
class GetTaskLogsActionResult(VFolderSingleEntityActionResult):
    # TODO: Add proper type
    response: Any
    vfolder_data: VFolderData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_data.id)

    @override
    def target_entity_id(self) -> str:
        return str(self.vfolder_data.id)
