from __future__ import annotations

import logging
from uuid import UUID

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.deployment_revision_preset.db_source.db_source import (
    DeploymentRevisionPresetDBSource,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class DeploymentRevisionPresetRepository:
    _db_source: DeploymentRevisionPresetDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = DeploymentRevisionPresetDBSource(db)

    async def get_next_rank(self, variant_id: UUID) -> int:
        return await self._db_source.get_next_rank(variant_id)

    async def create(
        self, creator: Creator[DeploymentRevisionPresetRow]
    ) -> DeploymentRevisionPresetData:
        return await self._db_source.create(creator)

    async def get_by_id(self, preset_id: UUID) -> DeploymentRevisionPresetData:
        return await self._db_source.get_by_id(preset_id)

    async def update(
        self, updater: Updater[DeploymentRevisionPresetRow]
    ) -> DeploymentRevisionPresetData:
        return await self._db_source.update(updater)

    async def delete(self, preset_id: UUID) -> DeploymentRevisionPresetData:
        return await self._db_source.delete(preset_id)

    async def search(
        self,
        querier: BatchQuerier,
    ) -> tuple[list[DeploymentRevisionPresetData], int, bool, bool]:
        return await self._db_source.search(querier)
