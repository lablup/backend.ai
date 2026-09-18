from __future__ import annotations

import logging
from collections.abc import Sequence
from uuid import UUID

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.models.runtime_variant.purgers import RuntimeVariantPurger
from ai.backend.manager.models.runtime_variant_preset.purgers import (
    RuntimeVariantPresetsOfVariantPurger,
)
from ai.backend.manager.models.specs.types import BulkResultWithFailures
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.write import V2WriteOps

from .db_source.db_source import RuntimeVariantDBSource

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RuntimeVariantRepository:
    """The two reads that live outside the action layer, and the purge clearing presets.

    The reads remain for sokovan's deployment executor and the model-serving service,
    which read a variant without an action.
    """

    _db_source: RuntimeVariantDBSource
    _ops: V2DBOpsProvider

    def __init__(self, db: ExtendedAsyncSAEngine, ops_provider: V2DBOpsProvider) -> None:
        self._db_source = RuntimeVariantDBSource(db)
        self._ops = ops_provider

    async def get_by_id(self, variant_id: UUID) -> RuntimeVariantData:
        return await self._db_source.get_by_id(variant_id)

    async def get_by_name(self, name: str) -> RuntimeVariantData:
        return await self._db_source.get_by_name(name)

    async def purge(self, purger: RuntimeVariantPurger) -> RuntimeVariantData:
        """Purge a runtime variant with the presets in its catalog."""
        async with self._ops.write_ops() as w:
            return await self._purge(w, purger)

    async def partial_bulk_purge(
        self, purgers: Sequence[RuntimeVariantPurger]
    ) -> BulkResultWithFailures[RuntimeVariantData]:
        """Purge each named variant with its presets in its own savepoint."""
        successes: dict[EntityIdentifier, RuntimeVariantData] = {}
        errors: dict[EntityIdentifier, Exception] = {}
        if not purgers:
            return BulkResultWithFailures(successes=successes, errors=errors)
        async with self._ops.write_ops() as w:
            for purger in purgers:
                try:
                    async with w.savepoint() as sp:
                        successes[purger.variant_id] = await self._purge(sp, purger)
                except Exception as e:
                    errors[purger.variant_id] = e
        return BulkResultWithFailures(successes=successes, errors=errors)

    async def _purge(self, w: V2WriteOps, purger: RuntimeVariantPurger) -> RuntimeVariantData:
        await w.batch_purge_entities_in_global(
            RuntimeVariantPresetsOfVariantPurger(variant_id=purger.variant_id)
        )
        data = await w.purge_entity(purger)
        if data is None:
            raise EntityNotFoundError(
                entity_type=purger.variant_id.entity_type(),
                operation=ActionOperationType.PURGE,
                extra_msg=f"runtime variant {purger.variant_id} not found",
            )
        return data
