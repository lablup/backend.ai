"""Running a shelf search through the shared ops layer, scoped or global."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.specs.pagination import OffsetPagination, QueryPagination
from ai.backend.manager.models.specs.search.usage import UsedBy
from ai.backend.manager.models.specs.searcher import (
    GlobalSearcher,
    ScopedSearcher,
    SearcherResult,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository

from .shelf_fields import (
    BoxSearchableFields,
    ShelfSearcher,
    SpecSearchableFields,
    ZoneShelfTarget,
)
from .shelf_rows import ShelfData, ZoneID


class ShelfSearches:
    """The two entry points a repository offers, with the searcher built for each call."""

    _repository: OpsRepository[ShelfData]

    def __init__(self, repository: OpsRepository[ShelfData]) -> None:
        self._repository = repository

    async def scoped(
        self,
        zones: Sequence[ZoneID],
        conditions: Sequence[QueryCondition] = (),
        orders: Sequence[QueryOrder] = (),
        used_by: Sequence[UsedBy] = (),
        pagination: QueryPagination | None = None,
    ) -> SearcherResult[ShelfData]:
        return await self._repository.scoped_search(
            ScopedSearcher(
                scopes=[ZoneShelfTarget(zone) for zone in zones],
                used_by=used_by,
                searcher=self._searcher(conditions, orders, pagination),
            )
        )

    async def in_global(
        self,
        conditions: Sequence[QueryCondition] = (),
        orders: Sequence[QueryOrder] = (),
        used_by: Sequence[UsedBy] = (),
        pagination: QueryPagination | None = None,
    ) -> SearcherResult[ShelfData]:
        return await self._repository.global_search(
            GlobalSearcher(
                used_by=used_by,
                searcher=self._searcher(conditions, orders, pagination),
            )
        )

    def _searcher(
        self,
        conditions: Sequence[QueryCondition],
        orders: Sequence[QueryOrder],
        pagination: QueryPagination | None,
    ) -> ShelfSearcher:
        return ShelfSearcher(
            pagination=pagination
            if pagination is not None
            else OffsetPagination(limit=50, offset=0),
            conditions=list(conditions),
            orders=list(orders),
        )


def ids(result: SearcherResult[ShelfData]) -> set[uuid.UUID]:
    return {item.id for item in result.items}


def ordered_ids(result: SearcherResult[ShelfData]) -> list[uuid.UUID]:
    return [item.id for item in result.items]


def negate(condition: QueryCondition) -> QueryCondition:
    """The condition a caller writes for the ``not`` of a quantifier."""

    def inner() -> sa.sql.expression.ColumnElement[bool]:
        return sa.not_(condition())

    return inner


def spec_graded(grade: str) -> QueryCondition:
    """A condition on one box: the spec that box points at carries ``grade``."""
    return BoxSearchableFields.nested.spec.correlation.has([
        SpecSearchableFields.own.grade.filter.equals(
            StringMatchSpec(value=grade, case_insensitive=False, negated=False)
        )
    ])
