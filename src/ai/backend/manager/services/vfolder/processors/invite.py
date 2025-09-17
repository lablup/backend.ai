from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec

from ..actions.invite import (
    AcceptInvitationAction,
    AcceptInvitationActionResult,
    InviteVFolderAction,
    InviteVFolderActionResult,
    LeaveInvitedVFolderAction,
    LeaveInvitedVFolderActionResult,
    ListInvitationAction,
    ListInvitationActionResult,
    RejectInvitationAction,
    RejectInvitationActionResult,
    RevokeInvitedVFolderAction,
    RevokeInvitedVFolderActionResult,
    UpdateInvitationAction,
    UpdateInvitationActionResult,
    UpdateInvitedVFolderMountPermissionAction,
    UpdateInvitedVFolderMountPermissionActionResult,
)
from ..services.invite import VFolderInviteService


class VFolderInviteProcessors(AbstractProcessorPackage):
    invite_vfolder: ActionProcessor[InviteVFolderAction, InviteVFolderActionResult]
    accept_invitation: ActionProcessor[AcceptInvitationAction, AcceptInvitationActionResult]
    reject_invitation: ActionProcessor[RejectInvitationAction, RejectInvitationActionResult]
    update_invitation: ActionProcessor[UpdateInvitationAction, UpdateInvitationActionResult]
    list_invitation: ActionProcessor[ListInvitationAction, ListInvitationActionResult]
    leave_invited_vfolder: ActionProcessor[
        LeaveInvitedVFolderAction, LeaveInvitedVFolderActionResult
    ]
    revoke_invited_vfolder: ActionProcessor[
        RevokeInvitedVFolderAction, RevokeInvitedVFolderActionResult
    ]
    update_invited_vfolder_mount_permission: ActionProcessor[
        UpdateInvitedVFolderMountPermissionAction, UpdateInvitedVFolderMountPermissionActionResult
    ]

    def __init__(self, service: VFolderInviteService, action_monitors: list[ActionMonitor]):
        self.invite_vfolder = ActionProcessor(service.invite, action_monitors)
        self.accept_invitation = ActionProcessor(service.accept_invitation, action_monitors)
        self.reject_invitation = ActionProcessor(service.reject_invitation, action_monitors)
        self.update_invitation = ActionProcessor(service.update_invitation, action_monitors)
        self.list_invitation = ActionProcessor(service.list_invitation, action_monitors)
        self.leave_invited_vfolder = ActionProcessor(service.leave_invited_vfolder, action_monitors)
        self.revoke_invited_vfolder = ActionProcessor(
            service.revoke_invited_vfolder, action_monitors
        )
        self.update_invited_vfolder_mount_permission = ActionProcessor(
            service.update_invited_vfolder_mount_permission, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            InviteVFolderAction.spec(),
            AcceptInvitationAction.spec(),
            RejectInvitationAction.spec(),
            UpdateInvitationAction.spec(),
            ListInvitationAction.spec(),
            LeaveInvitedVFolderAction.spec(),
            RevokeInvitedVFolderAction.spec(),
            UpdateInvitedVFolderMountPermissionAction.spec(),
        ]
