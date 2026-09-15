from __future__ import annotations

from ai.backend.manager.actions.v2.ops.result import EntityOpsResult
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.repositories.runtime_variant.repository import RuntimeVariantRepository
from ai.backend.manager.services.runtime_variant.actions.purge import PurgeRuntimeVariantAction

__all__ = ("RuntimeVariantService",)


class RuntimeVariantService:
    """The purge that clears a variant's presets first; every other operation runs against ops."""

    _repository: RuntimeVariantRepository

    def __init__(self, repository: RuntimeVariantRepository) -> None:
        self._repository = repository

    async def purge(self, action: PurgeRuntimeVariantAction) -> EntityOpsResult[RuntimeVariantData]:
        """Purge a runtime variant with the presets in its catalog."""
        data = await self._repository.purge(action.to_purger())
        return EntityOpsResult(data=data)
