"""Database source for replica group repository operations."""

from __future__ import annotations

import logging
from collections.abc import Sequence

import sqlalchemy as sa

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.updater import BulkUpdaterResult, Updater
from ai.backend.manager.repositories.ops.provider import DBOpsProvider
from ai.backend.manager.views.replica_group import (
    ReplicaGroupDeploySchedulingView,
    ReplicaGroupScalingSchedulingView,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ReplicaGroupDBSource:
    _ops: DBOpsProvider

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._ops = DBOpsProvider(db)

    async def search_deploy_scheduling_views(
        self,
        querier: BatchQuerier,
    ) -> list[ReplicaGroupDeploySchedulingView]:
        async with self._ops.read_ops() as r:
            result = await r.batch_query_in_global(sa.select(ReplicaGroupRow), querier)
            return [row.ReplicaGroupRow.to_deploy_scheduling_view() for row in result.rows]

    async def search_scaling_scheduling_views(
        self,
        querier: BatchQuerier,
    ) -> list[ReplicaGroupScalingSchedulingView]:
        async with self._ops.read_ops() as r:
            result = await r.batch_query_in_global(sa.select(ReplicaGroupRow), querier)
            return [row.ReplicaGroupRow.to_scaling_scheduling_view() for row in result.rows]

    async def update_replica_groups(
        self,
        updaters: Sequence[Updater[ReplicaGroupRow]],
    ) -> BulkUpdaterResult[ReplicaGroupRow]:
        async with self._ops.write_ops() as w:
            return await w.bulk_update_partial(updaters)
