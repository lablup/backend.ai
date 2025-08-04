import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import (
    Any,
    Optional,
    override,
)

from ai.backend.manager.actions.action.base import BaseAction, BaseActionResult
from ai.backend.manager.actions.action.create import BaseCreateAction, BaseCreateActionResult
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.models.vfolder import VFolderPermission as VFolderMountPermission

from ..types import VFolderInvitationInfo


@dataclass
class VFolderInvitationAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "vfolder_invitation"


@dataclass
class InviteVFolderAction(VFolderInvitationAction):
    keypair_resource_policy: Mapping[str, Any]
    user_uuid: uuid.UUID

    vfolder_uuid: uuid.UUID
    mount_permission: VFolderMountPermission
    invitee_user_uuids: list[uuid.UUID]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "invite"


@dataclass
class InviteVFolderActionResult(BaseActionResult):
    vfolder_uuid: uuid.UUID
    invitation_ids: list[uuid.UUID]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)


@dataclass
class AcceptInvitationAction(BaseCreateAction):
    invitation_id: uuid.UUID

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "vfolder"

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "accept"


@dataclass
class AcceptInvitationActionResult(BaseCreateActionResult):
    invitation_id: uuid.UUID
    vfolder_id: uuid.UUID

    @override
    def scope_id(self) -> ScopeId:
        return ScopeId(
            scope_type="user",
            scope_id=str(self.vfolder_id),
        )

    @override
    def entity_id(self) -> ObjectId:
        return ObjectId(
            entity_type="vfolder",
            entity_id=str(self.vfolder_id),
        )


@dataclass
class RejectInvitationAction(VFolderInvitationAction):
    invitation_id: uuid.UUID
    requester_user_uuid: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.invitation_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "reject"


@dataclass
class RejectInvitationActionResult(BaseActionResult):
    invitation_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.invitation_id)


@dataclass
class UpdateInvitationAction(VFolderInvitationAction):
    invitation_id: uuid.UUID

    requester_user_uuid: uuid.UUID
    mount_permission: VFolderMountPermission

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.invitation_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "update"


@dataclass
class UpdateInvitationActionResult(BaseActionResult):
    invitation_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.invitation_id)


@dataclass
class ListInvitationAction(VFolderInvitationAction):
    requester_user_uuid: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.requester_user_uuid)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "list"


@dataclass
class ListInvitationActionResult(BaseActionResult):
    requester_user_uuid: uuid.UUID
    info: list[VFolderInvitationInfo]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.requester_user_uuid)


@dataclass
class LeaveInvitedVFolderAction(VFolderInvitationAction):
    vfolder_uuid: uuid.UUID
    requester_user_uuid: uuid.UUID
    shared_user_uuid: Optional[uuid.UUID] = None

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "leave"


@dataclass
class LeaveInvitedVFolderActionResult(BaseActionResult):
    vfolder_uuid: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.vfolder_uuid)
