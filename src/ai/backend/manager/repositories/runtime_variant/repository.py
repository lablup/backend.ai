from __future__ import annotations

import logging
from uuid import UUID

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from .db_source.db_source import RuntimeVariantDBSource

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RuntimeVariantRepository:
    """The two reads that live outside the action layer.

    Every action wires straight to ops; these remain for sokovan's deployment executor
    and the model-serving service, which read a variant without an action.
    """

    _db_source: RuntimeVariantDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = RuntimeVariantDBSource(db)

    async def get_by_id(self, variant_id: UUID) -> RuntimeVariantData:
        return await self._db_source.get_by_id(variant_id)

    async def get_by_name(self, name: str) -> RuntimeVariantData:
        return await self._db_source.get_by_name(name)
