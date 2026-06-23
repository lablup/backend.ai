"""Database source for app config fragment repository operations."""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentData,
    AppConfigFragmentSearchResult,
)
from ai.backend.manager.errors.app_config import AppConfigFragmentNotFound
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.app_config_fragment.creators import (
    AppConfigFragmentCreateDependency,
    AppConfigFragmentCreatorSpec,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Purger,
    Querier,
    Updater,
)
from ai.backend.manager.repositories.base.creator import NextValuePolicy
from ai.backend.manager.repositories.ops import DBOpsProvider

__all__ = ("AppConfigFragmentDBSource",)

# Gap between successive ranks, leaving room to re-order fragments without renumbering.
RANK_GAP = 100


class AppConfigFragmentDBSource:
    """Database source for app config fragment operations."""

    _ops: DBOpsProvider

    def __init__(self, ops_provider: DBOpsProvider) -> None:
        self._ops = ops_provider

    async def create(self, spec: AppConfigFragmentCreatorSpec) -> AppConfigFragmentData:
        policy = NextValuePolicy(
            column=AppConfigFragmentRow.rank,
            scope_condition=lambda: AppConfigFragmentRow.config_name == spec.config_name,
            lock_selector=sa.select(AppConfigDefinitionRow).where(
                AppConfigDefinitionRow.config_name == spec.config_name
            ),
            gap=RANK_GAP,
        )
        async with self._ops.write_ops() as w:
            created = await w.create_with_next_value(
                policy, spec, lambda rank: AppConfigFragmentCreateDependency(rank=rank)
            )
            return created.row.to_data()

    async def get_by_id(self, fragment_id: AppConfigFragmentID) -> AppConfigFragmentData:
        async with self._ops.read_ops() as r:
            result = await r.query(Querier(row_class=AppConfigFragmentRow, pk_value=fragment_id))
            if result is None:
                raise AppConfigFragmentNotFound(f"App config fragment {fragment_id} not found")
            return result.row.to_data()

    async def update(self, updater: Updater[AppConfigFragmentRow]) -> AppConfigFragmentData:
        async with self._ops.write_ops() as w:
            result = await w.update(updater)
            if result is None:
                raise AppConfigFragmentNotFound(f"App config fragment {updater.pk_value} not found")
            return result.row.to_data()

    async def purge(self, fragment_id: AppConfigFragmentID) -> AppConfigFragmentData:
        async with self._ops.write_ops() as w:
            result = await w.purge(Purger(row_class=AppConfigFragmentRow, pk_value=fragment_id))
            if result is None:
                raise AppConfigFragmentNotFound(f"App config fragment {fragment_id} not found")
            return result.row.to_data()

    async def search(self, querier: BatchQuerier) -> AppConfigFragmentSearchResult:
        async with self._ops.read_ops() as r:
            result = await r.batch_query_in_global(sa.select(AppConfigFragmentRow), querier)
            items = [row.AppConfigFragmentRow.to_data() for row in result.rows]
            return AppConfigFragmentSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
