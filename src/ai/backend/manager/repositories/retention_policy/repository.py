from __future__ import annotations

import logging

from ai.backend.common.identifier.retention_policy import RetentionPolicyID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.retention.types import RetentionPolicyData, RetentionPolicySearchResult
from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.ops import DBOpsProvider

from .db_source.db_source import RetentionPolicyDBSource

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RetentionPolicyRepository:
    _db_source: RetentionPolicyDBSource

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._db_source = RetentionPolicyDBSource(ops_provider)

    async def create(self, creator: Creator[RetentionPolicyRow]) -> RetentionPolicyData:
        return await self._db_source.create(creator)

    async def update(self, updater: Updater[RetentionPolicyRow]) -> RetentionPolicyData:
        return await self._db_source.update(updater)

    async def delete(self, policy_id: RetentionPolicyID) -> RetentionPolicyData:
        return await self._db_source.delete(policy_id)

    async def purge(self, purger: Purger[RetentionPolicyRow]) -> RetentionPolicyData:
        return await self._db_source.purge(purger)

    async def search(self, querier: BatchQuerier) -> RetentionPolicySearchResult:
        return await self._db_source.search(querier)
