from __future__ import annotations

from ai.backend.manager.repositories.entity_invitation.repository import EntityInvitationRepository
from ai.backend.manager.services.entity_invitation.actions.answer import (
    AcceptEntityInvitationAction,
    CancelEntityInvitationAction,
    CancelEntityInvitationActionResult,
    EntityInvitationAnswerResult,
    RejectEntityInvitationAction,
)

__all__ = ("EntityInvitationService",)


class EntityInvitationService:
    """The three answers an invitation can receive.

    Creating and reading one is a single spec and runs against ops without passing
    through here.
    """

    _repository: EntityInvitationRepository

    def __init__(self, repository: EntityInvitationRepository) -> None:
        self._repository = repository

    async def accept(self, action: AcceptEntityInvitationAction) -> EntityInvitationAnswerResult:
        data = await self._repository.accept(action.invitation_id, action.invitee_user_id)
        return EntityInvitationAnswerResult(data=data)

    async def reject(self, action: RejectEntityInvitationAction) -> EntityInvitationAnswerResult:
        data = await self._repository.reject(action.invitation_id, action.invitee_user_id)
        return EntityInvitationAnswerResult(data=data)

    async def cancel(
        self, action: CancelEntityInvitationAction
    ) -> CancelEntityInvitationActionResult:
        data = await self._repository.cancel(action.invitation_id)
        return CancelEntityInvitationActionResult(data=data)
