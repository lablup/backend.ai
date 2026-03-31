import logging

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.model_card.repository import ModelCardRepository
from ai.backend.manager.services.model_card.actions.create import (
    CreateModelCardAction,
    CreateModelCardActionResult,
)
from ai.backend.manager.services.model_card.actions.delete import (
    DeleteModelCardAction,
    DeleteModelCardActionResult,
)
from ai.backend.manager.services.model_card.actions.search import (
    SearchModelCardsAction,
    SearchModelCardsActionResult,
)
from ai.backend.manager.services.model_card.actions.update import (
    UpdateModelCardAction,
    UpdateModelCardActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ModelCardService:
    _repository: ModelCardRepository

    def __init__(self, repository: ModelCardRepository) -> None:
        self._repository = repository

    async def create(self, action: CreateModelCardAction) -> CreateModelCardActionResult:
        data = await self._repository.create(action.creator)
        return CreateModelCardActionResult(model_card=data)

    async def update(self, action: UpdateModelCardAction) -> UpdateModelCardActionResult:
        action.updater.pk_value = action.id
        data = await self._repository.update(action.updater)
        return UpdateModelCardActionResult(model_card=data)

    async def delete(self, action: DeleteModelCardAction) -> DeleteModelCardActionResult:
        data = await self._repository.delete(action.id)
        return DeleteModelCardActionResult(model_card=data)

    async def search(self, action: SearchModelCardsAction) -> SearchModelCardsActionResult:
        items, total_count, has_next_page, has_previous_page = await self._repository.search(
            action.querier
        )
        return SearchModelCardsActionResult(
            items=items,
            total_count=total_count,
            has_next_page=has_next_page,
            has_previous_page=has_previous_page,
        )
