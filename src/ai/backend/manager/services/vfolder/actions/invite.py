import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import (
    Any,
    override,
)

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeRef
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE
from ai.backend.common.data.entity.vfolder_invitation import (
    VFOLDER_INVITATION_ENTITY_TYPE,
    VFolderInvitationID,
)
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.models.vfolder import VFolderPermission as VFolderMountPermission
from ai.backend.manager.services.vfolder.actions.base import (
    VFolderAction,
    VFolderScopeActionResult,
)
from ai.backend.manager.services.vfolder.types import VFolderInvitationInfo


@dataclass
class VFolderInvitationAction(BaseSingleEntityAction):
    """Base for an operation on one invitation.

    An invitation answers for itself rather than through the folder: the invitee
    acts on it while holding no permission on the folder yet.
    """

    invitation_id: VFolderInvitationID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.invitation_id


@dataclass
class VFolderInvitationScopeAction(BaseScopeAction):
    """Base for reading the invitations a user sent or received."""

    user_uuid: uuid.UUID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return VFOLDER_INVITATION_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=self.user_uuid),)


@dataclass
class InviteVFolderAction(VFolderAction):
    keypair_resource_policy: Mapping[str, Any]
    user_uuid: uuid.UUID

    mount_permission: VFolderMountPermission
    invitee_emails: list[str]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "invite_vfolder"


@dataclass
class InviteVFolderActionResult:
    vfolder_uuid: uuid.UUID
    invitation_ids: list[str]


@dataclass
class AcceptInvitationAction(VFolderInvitationAction):
    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "accept_invitation"


@dataclass
class AcceptInvitationActionResult:
    invitation_id: uuid.UUID


@dataclass
class RejectInvitationAction(VFolderInvitationAction):
    requester_user_uuid: uuid.UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "reject_invitation"


@dataclass
class RejectInvitationActionResult:
    invitation_id: uuid.UUID


@dataclass
class UpdateInvitationAction(VFolderInvitationAction):
    requester_user_uuid: uuid.UUID
    mount_permission: VFolderMountPermission

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_invitation"


@dataclass
class UpdateInvitationActionResult:
    invitation_id: uuid.UUID


@dataclass
class ListInvitationAction(VFolderInvitationScopeAction):
    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "list_invitation"


@dataclass
class ListInvitationActionResult(VFolderScopeActionResult):
    requester_user_uuid: uuid.UUID
    info: list[VFolderInvitationInfo]


@dataclass
class LeaveInvitedVFolderAction(VFolderAction):
    """Give up one's own access to a shared folder.

    ``PURGE``: what goes away is the permission row, and that table carries no
    lifecycle flag to set instead.
    """

    requester_user_uuid: uuid.UUID
    shared_user_uuid: uuid.UUID | None = None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "leave_invited_vfolder"


@dataclass
class LeaveInvitedVFolderActionResult:
    vfolder_uuid: uuid.UUID


@dataclass
class RevokeInvitedVFolderAction(VFolderAction):
    """Take a shared folder's access away from someone else.

    ``PURGE`` for the same reason as leaving one: the permission row is removed.
    """

    shared_user_id: uuid.UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "revoke_invited_vfolder"


@dataclass
class RevokeInvitedVFolderActionResult:
    vfolder_id: uuid.UUID
    shared_user_id: uuid.UUID


@dataclass
class UpdateInvitedVFolderMountPermissionAction(VFolderAction):
    user_id: uuid.UUID
    permission: VFolderMountPermission

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_invited_vfolder_mount_permission"


@dataclass
class UpdateInvitedVFolderMountPermissionActionResult:
    vfolder_id: uuid.UUID
    user_id: uuid.UUID
    permission: VFolderMountPermission


@dataclass
class ListSentInvitationsAction(VFolderInvitationScopeAction):
    """List invitations sent by the requester."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "list_sent_invitations"


@dataclass
class ListSentInvitationsActionResult(VFolderScopeActionResult):
    invitations: list[VFolderInvitationInfo]
