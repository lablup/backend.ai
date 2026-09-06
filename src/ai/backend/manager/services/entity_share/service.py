from __future__ import annotations

from ai.backend.manager.repositories.entity_share.repository import EntityShareRepository
from ai.backend.manager.services.entity_share.actions.answer import (
    AcceptEntityShareAction,
    CancelEntityShareAction,
    CancelEntityShareActionResult,
    EntityShareAnswerResult,
    RejectEntityShareAction,
)

__all__ = ("EntityShareService",)


class EntityShareService:
    """The three answers an invitation can receive.

    Creating and reading one is a single spec and runs against ops without passing
    through here.
    """

    _repository: EntityShareRepository

    def __init__(self, repository: EntityShareRepository) -> None:
        self._repository = repository

    async def accept(self, action: AcceptEntityShareAction) -> EntityShareAnswerResult:
        data = await self._repository.accept(action.share_id, action.recipient_user_id)
        return EntityShareAnswerResult(data=data)

    async def reject(self, action: RejectEntityShareAction) -> EntityShareAnswerResult:
        data = await self._repository.reject(action.share_id, action.recipient_user_id)
        return EntityShareAnswerResult(data=data)

    async def cancel(self, action: CancelEntityShareAction) -> CancelEntityShareActionResult:
        data = await self._repository.cancel(action.share_id)
        return CancelEntityShareActionResult(data=data)
