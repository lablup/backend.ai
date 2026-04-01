from __future__ import annotations

import logging
from uuid import UUID

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater

from .db_source.db_source import RuntimeVariantDBSource

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RuntimeVariantRepository:
    _db_source: RuntimeVariantDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = RuntimeVariantDBSource(db)

    async def create(self, creator: Creator[RuntimeVariantRow]) -> RuntimeVariantData:
        return await self._db_source.create(creator)

    async def get_by_id(self, variant_id: UUID) -> RuntimeVariantData:
        return await self._db_source.get_by_id(variant_id)

    async def update(self, updater: Updater[RuntimeVariantRow]) -> RuntimeVariantData:
        return await self._db_source.update(updater)

    async def delete(self, variant_id: UUID) -> RuntimeVariantData:
        return await self._db_source.delete(variant_id)

    async def search(
        self,
        querier: BatchQuerier,
    ) -> tuple[list[RuntimeVariantData], int, bool, bool]:
        return await self._db_source.search(querier)
