from __future__ import annotations

from ai.backend.manager.actions.v2.bulk.result import PartialBulkEntityResult, PartialBulkResult
from ai.backend.manager.actions.v2.ops.result import EntityOpsResult
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.models.runtime_variant.purgers import RuntimeVariantPurger
from ai.backend.manager.repositories.runtime_variant.repository import RuntimeVariantRepository
from ai.backend.manager.services.runtime_variant.actions.bulk_purge import (
    BulkPurgeRuntimeVariantsAction,
)
from ai.backend.manager.services.runtime_variant.actions.purge import PurgeRuntimeVariantAction

__all__ = ("RuntimeVariantService",)


class RuntimeVariantService:
    """The purges that clear a variant's presets first; every other operation runs against ops."""

    _repository: RuntimeVariantRepository

    def __init__(self, repository: RuntimeVariantRepository) -> None:
        self._repository = repository

    async def purge(self, action: PurgeRuntimeVariantAction) -> EntityOpsResult[RuntimeVariantData]:
        """Purge a runtime variant with the presets in its catalog."""
        data = await self._repository.purge(action.to_purger())
        return EntityOpsResult(data=data)

    async def bulk_purge(
        self, action: BulkPurgeRuntimeVariantsAction
    ) -> PartialBulkResult[RuntimeVariantData]:
        """Purge each named runtime variant with its presets, answering for every one."""
        result = await self._repository.partial_bulk_purge([
            RuntimeVariantPurger(variant_id=variant_id) for variant_id in action.ids
        ])
        return PartialBulkResult(
            items=[
                *(
                    PartialBulkEntityResult[RuntimeVariantData].succeeded(entity_id, data)
                    for entity_id, data in result.successes.items()
                ),
                *(
                    PartialBulkEntityResult[RuntimeVariantData].failed(entity_id, error)
                    for entity_id, error in result.errors.items()
                ),
            ]
        )
