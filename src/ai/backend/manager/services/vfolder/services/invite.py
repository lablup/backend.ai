from dataclasses import dataclass

from ....models.utils import ExtendedAsyncSAEngine
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


@dataclass
class ServiceInitParameter:
    db: ExtendedAsyncSAEngine


class VFolderInviteService:
    _db: ExtendedAsyncSAEngine

    def __init__(self, parameter: ServiceInitParameter) -> None:
        self._db = parameter.db

    async def invite(self, action: InviteVFolderAction) -> InviteVFolderActionResult:
        pass

    async def receive_invitation(
        self, action: ReceiveInvitationAction
    ) -> ReceiveInvitationActionResult:
        pass

    async def update_invitation(
        self, action: UpdateInvitationAction
    ) -> UpdateInvitationActionResult:
        pass

    async def list_invitation(self, action: ListInvitationAction) -> ListInvitationActionResult:
        pass

    async def leave_invited_vfolder(
        self, action: LeaveInvitedVFolderAction
    ) -> LeaveInvitedVFolderActionResult:
        pass
