from ai.backend.manager.actions.processor import ActionProcessor

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
    UpdateInvitationAction,
    UpdateInvitationActionResult,
)
from ..services.invite import VFolderInviteService


class VFolderInviteProcessors:
    invite_vfolder: ActionProcessor[InviteVFolderAction, InviteVFolderActionResult]
    accept_invitation: ActionProcessor[AcceptInvitationAction, AcceptInvitationActionResult]
    reject_invitation: ActionProcessor[RejectInvitationAction, RejectInvitationActionResult]
    update_invitation: ActionProcessor[UpdateInvitationAction, UpdateInvitationActionResult]
    list_invitation: ActionProcessor[ListInvitationAction, ListInvitationActionResult]
    leave_invited_vfolder: ActionProcessor[
        LeaveInvitedVFolderAction, LeaveInvitedVFolderActionResult
    ]

    def __init__(self, service: VFolderInviteService):
        self.invite_vfolder = ActionProcessor(service.invite)
        self.accept_invitation = ActionProcessor(service.accept_invitation)
        self.reject_invitation = ActionProcessor(service.reject_invitation)
        self.update_invitation = ActionProcessor(service.update_invitation)
        self.list_invitation = ActionProcessor(service.list_invitation)
        self.leave_invited_vfolder = ActionProcessor(service.leave_invited_vfolder)
