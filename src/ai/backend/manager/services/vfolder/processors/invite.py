from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.services.vfolder.actions.invite import (
    AcceptInvitationAction,
    AcceptInvitationActionResult,
    InviteVFolderAction,
    InviteVFolderActionResult,
    LeaveInvitedVFolderAction,
    LeaveInvitedVFolderActionResult,
    ListInvitationAction,
    ListInvitationActionResult,
    ListSentInvitationsAction,
    ListSentInvitationsActionResult,
    RejectInvitationAction,
    RejectInvitationActionResult,
    RevokeInvitedVFolderAction,
    RevokeInvitedVFolderActionResult,
    UpdateInvitationAction,
    UpdateInvitationActionResult,
    UpdateInvitedVFolderMountPermissionAction,
    UpdateInvitedVFolderMountPermissionActionResult,
)
from ai.backend.manager.services.vfolder.services.invite import VFolderInviteService


class VFolderInviteProcessors:
    invite_vfolder: SingleEntityActionProcessor[InviteVFolderAction, InviteVFolderActionResult]
    accept_invitation: SingleEntityActionProcessor[
        AcceptInvitationAction, AcceptInvitationActionResult
    ]
    reject_invitation: SingleEntityActionProcessor[
        RejectInvitationAction, RejectInvitationActionResult
    ]
    update_invitation: SingleEntityActionProcessor[
        UpdateInvitationAction, UpdateInvitationActionResult
    ]
    list_invitation: ScopeActionProcessor[ListInvitationAction, ListInvitationActionResult]
    leave_invited_vfolder: SingleEntityActionProcessor[
        LeaveInvitedVFolderAction, LeaveInvitedVFolderActionResult
    ]
    revoke_invited_vfolder: SingleEntityActionProcessor[
        RevokeInvitedVFolderAction, RevokeInvitedVFolderActionResult
    ]
    update_invited_vfolder_mount_permission: SingleEntityActionProcessor[
        UpdateInvitedVFolderMountPermissionAction, UpdateInvitedVFolderMountPermissionActionResult
    ]
    list_sent_invitations: ScopeActionProcessor[
        ListSentInvitationsAction, ListSentInvitationsActionResult
    ]

    def __init__(self, group: ProcessorGroup[VFolderData], service: VFolderInviteService) -> None:
        self.invite_vfolder = group.single_entity(InviteVFolderAction, service.invite)
        self.accept_invitation = group.single_entity(
            AcceptInvitationAction, service.accept_invitation
        )
        self.reject_invitation = group.single_entity(
            RejectInvitationAction, service.reject_invitation
        )
        self.update_invitation = group.single_entity(
            UpdateInvitationAction, service.update_invitation
        )
        self.list_invitation = group.scope(ListInvitationAction, service.list_invitation)
        self.leave_invited_vfolder = group.single_entity(
            LeaveInvitedVFolderAction, service.leave_invited_vfolder
        )
        self.revoke_invited_vfolder = group.single_entity(
            RevokeInvitedVFolderAction, service.revoke_invited_vfolder
        )
        self.update_invited_vfolder_mount_permission = group.single_entity(
            UpdateInvitedVFolderMountPermissionAction,
            service.update_invited_vfolder_mount_permission,
        )
        self.list_sent_invitations = group.scope(
            ListSentInvitationsAction, service.list_sent_invitations
        )
