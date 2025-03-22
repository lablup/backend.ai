from ai.backend.manager.actions.action import BaseActionResult

from .base import VFolderAction


class InviteVFolderAction(VFolderAction):
    pass


class InviteVFolderActionResult(BaseActionResult):
    pass


class ReceiveInvitationAction(VFolderAction):
    pass


class ReceiveInvitationActionResult(BaseActionResult):
    pass


class UpdateInvitationAction(VFolderAction):
    pass


class UpdateInvitationActionResult(BaseActionResult):
    pass


class ListInvitationAction(VFolderAction):
    pass


class ListInvitationActionResult(BaseActionResult):
    pass


class LeaveInvitedVFolderAction(VFolderAction):
    pass


class LeaveInvitedVFolderActionResult(BaseActionResult):
    pass
