from __future__ import annotations

from ai.backend.manager.repositories.entity_share.repository import EntityShareRepository
from ai.backend.manager.services.entity_share.actions.answer import (
    AcceptEntityShareAction,
    CancelEntityShareAction,
    CancelEntityShareActionResult,
    EntityShareAnswerResult,
    LeaveEntityShareAction,
    RejectEntityShareAction,
    RevokeEntityShareAction,
    RevokeEntityShareActionResult,
)
from ai.backend.manager.services.entity_share.actions.create import (
    CreateEntityShareAction,
    CreateEntityShareActionResult,
)

__all__ = ("EntityShareService",)


class EntityShareService:
    """Making an offer and the answers it can receive.

    Reading one is a single spec and runs against ops without passing through here.
    """

    _repository: EntityShareRepository

    def __init__(self, repository: EntityShareRepository) -> None:
        self._repository = repository

    async def create(self, action: CreateEntityShareAction) -> CreateEntityShareActionResult:
        """Write the offer, or restate what already stands for the same pair."""
        data = await self._repository.create(action.creator)
        return CreateEntityShareActionResult(data=data)

    async def accept(self, action: AcceptEntityShareAction) -> EntityShareAnswerResult:
        data = await self._repository.accept(action.share_id, action.answering_scope)
        return EntityShareAnswerResult(data=data)

    async def reject(self, action: RejectEntityShareAction) -> EntityShareAnswerResult:
        data = await self._repository.reject(action.share_id, action.answering_scope)
        return EntityShareAnswerResult(data=data)

    async def leave(self, action: LeaveEntityShareAction) -> EntityShareAnswerResult:
        data = await self._repository.leave(action.share_id, action.answering_scope)
        return EntityShareAnswerResult(data=data)

    async def revoke(self, action: RevokeEntityShareAction) -> RevokeEntityShareActionResult:
        data = await self._repository.revoke(action.share_id)
        return RevokeEntityShareActionResult(data=data)

    async def cancel(self, action: CancelEntityShareAction) -> CancelEntityShareActionResult:
        data = await self._repository.cancel(action.share_id)
        return CancelEntityShareActionResult(data=data)
