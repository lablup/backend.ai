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
from ai.backend.manager.actions.action import BaseAction, BaseActionResult
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.vfolder import (
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderPermission,
)
from ai.backend.manager.types import OptionalState, PartialModifier

from ..types import VFolderBaseInfo, VFolderOwnershipInfo, VFolderUsageInfo


class VFolderAction(BaseAction):
    def entity_type(self):
        return "vfolder"


@dataclass
class CreateVFolderAction(VFolderAction):
    name: str

    keypair_resource_policy: Mapping[str, Any]
    domain_name: str
    group_id_or_name: Optional[str | uuid.UUID]
    folder_host: Optional[str]
    unmanaged_path: Optional[str]
    mount_permission: VFolderPermission
    usage_mode: VFolderUsageMode
    cloneable: bool

    # User identifier
    # TODO: Distinguish between creator and owner
    user_uuid: uuid.UUID
    user_role: UserRole
    creator_email: str

    def entity_id(self) -> Optional[str]:
        return None

    def operation_type(self) -> str:
        return "create"


@dataclass
class CreateVFolderActionResult(BaseActionResult):
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

    def entity_id(self) -> Optional[str]:
        return str(self.id)


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
class UpdateVFolderAttributeAction(VFolderAction):
    user_uuid: uuid.UUID
    vfolder_uuid: uuid.UUID
    modifier: VFolderAttributeModifier = field(default_factory=VFolderAttributeModifier)

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)

    @override
    def operation_type(self):
        return "update"


@dataclass
class UpdateVFolderAttributeActionResult(BaseActionResult):
    vfolder_uuid: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)


@dataclass
class GetVFolderAction(VFolderAction):
    user_uuid: uuid.UUID
    vfolder_uuid: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)

    @override
    def operation_type(self):
        return "get"


@dataclass
class GetVFolderActionResult(BaseActionResult):
    user_uuid: uuid.UUID
    base_info: VFolderBaseInfo
    ownership_info: VFolderOwnershipInfo
    usage_info: VFolderUsageInfo

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.user_uuid)


@dataclass
class ListVFolderAction(VFolderAction):
    user_uuid: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.user_uuid)

    @override
    def operation_type(self):
        return "list"


@dataclass
class ListVFolderActionResult(BaseActionResult):
    user_uuid: uuid.UUID
    vfolders: list[tuple[VFolderBaseInfo, VFolderOwnershipInfo]]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.user_uuid)


@dataclass
class MoveToTrashVFolderAction(VFolderAction):
    user_uuid: uuid.UUID
    keypair_resource_policy: Mapping[str, Any]

    vfolder_uuid: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)

    @override
    def operation_type(self):
        return "move_to_trash"


@dataclass
class MoveToTrashVFolderActionResult(BaseActionResult):
    vfolder_uuid: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)


@dataclass
class RestoreVFolderFromTrashAction(VFolderAction):
    user_uuid: uuid.UUID

    vfolder_uuid: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)

    @override
    def operation_type(self):
        return "restore"


@dataclass
class RestoreVFolderFromTrashActionResult(BaseActionResult):
    vfolder_uuid: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)


@dataclass
class DeleteForeverVFolderAction(VFolderAction):
    user_uuid: uuid.UUID

    vfolder_uuid: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)

    @override
    def operation_type(self):
        return "delete_forever"


@dataclass
class DeleteForeverVFolderActionResult(BaseActionResult):
    vfolder_uuid: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)


@dataclass
class ForceDeleteVFolderAction(VFolderAction):
    """
    This action transits the state of vfolder from ready to delete-forever directly.
    """

    user_uuid: uuid.UUID

    vfolder_uuid: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)

    @override
    def operation_type(self):
        return "force_delete"


@dataclass
class ForceDeleteVFolderActionResult(BaseActionResult):
    vfolder_uuid: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)


@dataclass
class CloneVFolderAction(VFolderAction):
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
    def operation_type(self):
        return "clone"


@dataclass
class CloneVFolderActionResult(BaseActionResult):
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


@dataclass
class GetTaskLogsAction(VFolderAction):
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
    def operation_type(self):
        return "get_task_logs"


@dataclass
class GetTaskLogsActionResult(BaseActionResult):
    # TODO: Add proper type
    response: Any
    # TODO: Replace this with VFolderData
    vfolder_data: Any

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_data["id"])
