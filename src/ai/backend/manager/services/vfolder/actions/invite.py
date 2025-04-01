import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import (
    Any,
    Optional,
)

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.vfolder import VFolderPermission as VFolderMountPermission

from .base import VFolderAction


class InviteVFolderAction(VFolderAction):
    keypair_resource_policy: Mapping[str, Any]
    user_uuid: uuid.UUID

    vfolder_uuid: uuid.UUID
    mount_permission: VFolderMountPermission
    invitee_user_uuids: list[uuid.UUID]


class InviteVFolderActionResult(BaseActionResult):
    pass


class AcceptInvitationAction(VFolderAction):
    invitation_id: uuid.UUID


class AcceptInvitationActionResult(BaseActionResult):
    pass


class RejectInvitationAction(VFolderAction):
    invitation_id: uuid.UUID
    requester_user_uuid: uuid.UUID


class RejectInvitationActionResult(BaseActionResult):
    pass


class UpdateInvitationAction(VFolderAction):
    invitation_id: uuid.UUID

    requester_user_uuid: uuid.UUID
    mount_permission: VFolderMountPermission


class UpdateInvitationActionResult(BaseActionResult):
    pass


class ListInvitationAction(VFolderAction):
    requester_user_uuid: uuid.UUID


class ListInvitationActionResult(BaseActionResult):
    pass


@dataclass
class LeaveInvitedVFolderAction(VFolderAction):
    shared_user_uuid: uuid.UUID
    vfolder_uuid: uuid.UUID
    requester_user_uuid: Optional[uuid.UUID] = None


class LeaveInvitedVFolderActionResult(BaseActionResult):
    pass
