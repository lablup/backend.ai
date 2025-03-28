from ai.backend.manager.actions.processor import ActionProcessor

from ..actions.invite import (
    InviteVFolderAction,
    InviteVFolderActionResult,
    LeaveInvitedVFolderAction,
    LeaveInvitedVFolderActionResult,
    ListInvitationAction,
    ListInvitationActionResult,
    ReceiveInvitationAction,
    ReceiveInvitationActionResult,
    UpdateInvitationAction,
    UpdateInvitationActionResult,
)
from ..services.invite import VFolderInviteService


class VFolderInviteProcessors:
    invite_vfolder = ActionProcessor[InviteVFolderAction, InviteVFolderActionResult]
    receive_invitation = ActionProcessor[ReceiveInvitationAction, ReceiveInvitationActionResult]
    update_invitation = ActionProcessor[UpdateInvitationAction, UpdateInvitationActionResult]
    list_invitation = ActionProcessor[ListInvitationAction, ListInvitationActionResult]
    leave_invited_vfolder = ActionProcessor[
        LeaveInvitedVFolderAction, LeaveInvitedVFolderActionResult
    ]

    def __init__(self, service: VFolderInviteService):
        self.invite_vfolder = ActionProcessor(service.invite)
        self.receive_invitation = ActionProcessor(service.receive_invitation)
        self.update_invitation = ActionProcessor(service.update_invitation)
        self.list_invitation = ActionProcessor(service.list_invitation)
        self.leave_invited_vfolder = ActionProcessor(service.leave_invited_vfolder)
