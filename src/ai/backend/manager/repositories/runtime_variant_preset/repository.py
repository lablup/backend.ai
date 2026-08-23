from __future__ import annotations

import logging
from uuid import UUID

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from .db_source.db_source import RuntimeVariantPresetDBSource

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RuntimeVariantPresetRepository:
    """The reads other domains resolve presets through; the writes run against ops."""

    _db_source: RuntimeVariantPresetDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = RuntimeVariantPresetDBSource(db)

    async def get_by_id(self, preset_id: UUID) -> RuntimeVariantPresetData:
        return await self._db_source.get_by_id(preset_id)

    async def get_by_ids(self, preset_ids: list[UUID]) -> list[RuntimeVariantPresetData]:
        return await self._db_source.get_by_ids(preset_ids)
