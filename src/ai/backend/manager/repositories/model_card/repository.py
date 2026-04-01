from __future__ import annotations

import logging
from uuid import UUID

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater

from .db_source.db_source import ModelCardDBSource

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ModelCardRepository:
    _db_source: ModelCardDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = ModelCardDBSource(db)

    async def create(self, creator: Creator[ModelCardRow]) -> ModelCardData:
        return await self._db_source.create(creator)

    async def get_by_id(self, card_id: UUID) -> ModelCardData:
        return await self._db_source.get_by_id(card_id)

    async def update(self, updater: Updater[ModelCardRow]) -> ModelCardData:
        return await self._db_source.update(updater)

    async def delete(self, card_id: UUID) -> ModelCardData:
        return await self._db_source.delete(card_id)

    async def search(
        self,
        querier: BatchQuerier,
    ) -> tuple[list[ModelCardData], int, bool, bool]:
        return await self._db_source.search(querier)
