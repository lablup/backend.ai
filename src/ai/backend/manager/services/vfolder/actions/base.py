import uuid
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any, Optional

from ai.backend.common.types import (
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
from ai.backend.manager.types import NonNullState

from ..types import VFolderBaseInfo, VFolderOwnershipInfo, VFolderUsageInfo


class VFolderAction(BaseAction):
    def entity_type(self):
        return "vfolder"


@dataclass
class CreateVFolderAction(VFolderAction):
    name: str

    keypair_resource_policy: Mapping[str, Any]
    domain_name: str
    group_id_or_name: Optional[str]
    folder_host: str
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
    permission: VFolderPermission
    mount_permission: VFolderPermission
    usage_mode: VFolderUsageMode
    creator_email: str
    ownership_type: VFolderOwnershipType
    cloneable: bool
    status: VFolderOperationStatus

    def entity_id(self) -> Optional[str]:
        return str(self.id)


@dataclass
class UpdateVFolderAttributeInput:
    name: NonNullState[str] = field(default_factory=NonNullState.none("name"))
    cloneable: NonNullState[bool] = field(default_factory=NonNullState.none("cloneable"))
    mount_permission: NonNullState[VFolderPermission] = field(
        default_factory=NonNullState.none("mount_permission")
    )

    def set_attr(self, obj: Any) -> None:
        self.name.set_attr(obj)
        self.cloneable.set_attr(obj)
        self.mount_permission.set_attr(obj)


class UpdateVFolderAttributeAction(VFolderAction):
    vfolder_uuid: uuid.UUID
    accessible_vfolder_uuids: Iterable[uuid.UUID]
    input: UpdateVFolderAttributeInput = field(default_factory=UpdateVFolderAttributeInput)


class UpdateVFolderAttributeActionResult(BaseActionResult):
    pass


class ChangeOwnershipAction(VFolderAction):
    pass


class ChangeOwnershipActionResult(BaseActionResult):
    pass


class GetVFolderAction(VFolderAction):
    vfolder_uuid: uuid.UUID


class GetVFolderActionResult(BaseActionResult):
    base_info: VFolderBaseInfo
    ownership_info: VFolderOwnershipInfo
    usage_info: VFolderUsageInfo


class ListVFolderAction(VFolderAction):
    vfolder_uuids: Iterable[uuid.UUID]


class ListVFolderActionResult(BaseActionResult):
    vfolders: list[tuple[VFolderBaseInfo, VFolderOwnershipInfo]]


class MoveToTrashVFolderAction(VFolderAction):
    user_uuid: uuid.UUID
    keypair_resource_policy: Mapping[str, Any]

    vfolder_uuid: uuid.UUID


class MoveToTrashVFolderActionResult(BaseActionResult):
    pass


class RestoreVFolderFromTrashAction(VFolderAction):
    user_uuid: uuid.UUID

    vfolder_uuid: uuid.UUID


class RestoreVFolderFromTrashActionResult(BaseActionResult):
    pass


class DeleteForeverVFolderAction(VFolderAction):
    user_uuid: uuid.UUID

    vfolder_uuid: uuid.UUID


class DeleteForeverVFolderActionResult(BaseActionResult):
    pass


class ForceDeleteVFolderAction(VFolderAction):
    """
    This action transits the state of vfolder from ready to delete-forever directly.
    """

    user_uuid: uuid.UUID

    vfolder_uuid: uuid.UUID


class ForceDeleteVFolderActionResult(BaseActionResult):
    pass


class CloneVFolderAction(VFolderAction):
    requester_user_uuid: uuid.UUID

    cloneable: bool = False
    target_name: str
    target_host: Optional[str] = None
    source_vfolder_uuid: uuid.UUID
    usage_mode: VFolderUsageMode = VFolderUsageMode.GENERAL
    mount_permission: VFolderPermission = VFolderPermission.READ_WRITE


class CloneVFolderActionResult(BaseActionResult):
    pass
