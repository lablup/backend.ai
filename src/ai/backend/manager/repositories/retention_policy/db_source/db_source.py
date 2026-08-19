"""Database source for retention policy repository operations.

Each public method binds its work to a single session through the injected
``DBOpsProvider``. The caller passes in the spec
(``Creator`` / ``Updater`` / ``Purger`` / ``BatchQuerier``) that scopes the operation.
"""

from __future__ import annotations

import logging

import sqlalchemy as sa

from ai.backend.common.identifier.retention_policy import RetentionPolicyID
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.retention.types import RetentionPolicyData, RetentionPolicySearchResult
from ai.backend.manager.errors.retention import RetentionPolicyNotFound
from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.repositories.base import BatchQuerier, Creator, Purger, Updater
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.manager.repositories.retention_policy.purgers import RetentionPolicyPurgerSpec

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RetentionPolicyDBSource:
    _ops: DBOpsProvider

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._ops = ops_provider

    async def create(self, creator: Creator[RetentionPolicyRow]) -> RetentionPolicyData:
        async with self._ops.write_ops() as w:
            created = await w.create(creator)
            return created.row.to_data()

    async def update(self, updater: Updater[RetentionPolicyRow]) -> RetentionPolicyData:
        async with self._ops.write_ops() as w:
            result = await w.update(updater)
            if result is None:
                raise RetentionPolicyNotFound(
                    f"Retention policy with ID {updater.pk_value} not found."
                )
            return result.row.to_data()

    async def delete(self, policy_id: RetentionPolicyID) -> RetentionPolicyData:
        async with self._ops.write_ops() as w:
            result = await w.purge(Purger(spec=RetentionPolicyPurgerSpec(policy_id=policy_id)))
            if result is None:
                raise RetentionPolicyNotFound()
            return result.row.to_data()

    async def purge(self, purger: Purger[RetentionPolicyRow]) -> RetentionPolicyData:
        async with self._ops.write_ops() as w:
            result = await w.purge(purger)
            if result is None:
                raise RetentionPolicyNotFound()
            return result.row.to_data()

    async def search(self, querier: BatchQuerier) -> RetentionPolicySearchResult:
        async with self._ops.read_ops() as r:
            result = await r.batch_query_in_global(sa.select(RetentionPolicyRow), querier)
            items = [row.RetentionPolicyRow.to_data() for row in result.rows]
            return RetentionPolicySearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
