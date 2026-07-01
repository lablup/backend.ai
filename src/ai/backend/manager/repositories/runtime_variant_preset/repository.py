from __future__ import annotations

import logging
from uuid import UUID

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater

from .db_source.db_source import RuntimeVariantPresetDBSource

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RuntimeVariantPresetRepository:
    _db_source: RuntimeVariantPresetDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = RuntimeVariantPresetDBSource(db)

    async def get_next_rank(self, variant_id: UUID) -> int:
        return await self._db_source.get_next_rank(variant_id)

    async def create(self, creator: Creator[RuntimeVariantPresetRow]) -> RuntimeVariantPresetData:
        return await self._db_source.create(creator)

    async def get_by_id(self, preset_id: UUID) -> RuntimeVariantPresetData:
        return await self._db_source.get_by_id(preset_id)

    async def get_by_ids(self, preset_ids: list[UUID]) -> list[RuntimeVariantPresetData]:
        return await self._db_source.get_by_ids(preset_ids)

    async def update(self, updater: Updater[RuntimeVariantPresetRow]) -> RuntimeVariantPresetData:
        return await self._db_source.update(updater)

    async def delete(self, preset_id: UUID) -> RuntimeVariantPresetData:
        return await self._db_source.delete(preset_id)

    async def search(
        self,
        querier: BatchQuerier,
    ) -> tuple[list[RuntimeVariantPresetData], int, bool, bool]:
        return await self._db_source.search(querier)
