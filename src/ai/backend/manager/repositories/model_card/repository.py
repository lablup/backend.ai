from __future__ import annotations

import logging
from collections.abc import Sequence
from uuid import UUID

from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    SearchDeploymentRevisionPresetsInput,
)
from ai.backend.common.dto.manager.v2.model_card.request import DeleteModelCardOptions
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.model_card.types import (
    BulkModelCardDeleteResultData,
    ModelCardData,
    VFolderScanData,
)
from ai.backend.manager.models.model_card.purgers import ModelCardPurger
from ai.backend.manager.models.model_card.updaters import ModelCardUpdater
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.model_card.types import (
    AvailablePresetsSearchResult,
)
from ai.backend.manager.repositories.model_card.upserters import ModelCardScanUpserterSpec

from .db_source.db_source import ModelCardDBSource

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ModelCardRepository:
    _db_source: ModelCardDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = ModelCardDBSource(db)

    async def update(self, updater: ModelCardUpdater) -> ModelCardData:
        return await self._db_source.update(updater)

    async def delete(
        self,
        purger: ModelCardPurger,
        options: DeleteModelCardOptions,
    ) -> UUID:
        return await self._db_source.delete(purger, options)

    async def bulk_delete(
        self,
        purgers: list[ModelCardPurger],
        options: DeleteModelCardOptions,
    ) -> BulkModelCardDeleteResultData:
        return await self._db_source.bulk_delete(purgers, options)

    async def get_scan_target_vfolders(self, project_id: UUID) -> list[VFolderScanData]:
        return await self._db_source.get_scan_target_vfolders(project_id)

    async def get_existing_card_names(self, project_id: UUID, domain: str) -> set[str]:
        return await self._db_source.get_existing_card_names(project_id, domain)

    async def search_available_presets(
        self,
        model_card_id: UUID,
        search_input: SearchDeploymentRevisionPresetsInput,
    ) -> AvailablePresetsSearchResult:
        return await self._db_source.search_available_presets(model_card_id, search_input)

    async def bulk_upsert_scan(
        self,
        specs: Sequence[ModelCardScanUpserterSpec],
        existing_names: set[str],
    ) -> tuple[int, int]:
        return await self._db_source.bulk_upsert_scan(specs, existing_names)
