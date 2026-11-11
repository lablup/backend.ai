"""Aggregate-read spec of the v2 lineage: what to count, how to group it and which groups to keep."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.exception import UnreachableError
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.scopes import AggregateScopeTarget
from ai.backend.manager.models.specs.aggregate.group import GroupBy

__all__ = (
    "AggregateColumns",
    "AggregateGroup",
    "AggregateOrder",
    "AggregateResult",
    "AggregateValue",
    "Aggregator",
    "CountOrder",
    "GroupKeyOrder",
    "ScopeAggregateResult",
)


@dataclass(frozen=True)
class AggregateColumns:
    """The columns an order can sort the groups by."""

    keys: Sequence[tuple[GroupBy, sa.ColumnElement[Any]]]
    count: sa.ColumnElement[int]

    def key(self, group: GroupBy) -> sa.ColumnElement[Any]:
        for candidate, column in self.keys:
            if candidate is group:
                return column
        raise UnreachableError(f"{group!r} is not one of the aggregate's groups")


class AggregateOrder(ABC):
    """One sort criterion over the groups."""

    @abstractmethod
    def apply(self, columns: AggregateColumns) -> sa.ColumnElement[Any]:
        raise NotImplementedError


@dataclass(frozen=True)
class GroupKeyOrder(AggregateOrder):
    group: GroupBy
    ascending: bool

    @override
    def apply(self, columns: AggregateColumns) -> sa.ColumnElement[Any]:
        column = columns.key(self.group)
        return column.asc() if self.ascending else column.desc()


@dataclass(frozen=True)
class CountOrder(AggregateOrder):
    ascending: bool

    @override
    def apply(self, columns: AggregateColumns) -> sa.ColumnElement[Any]:
        return columns.count.asc() if self.ascending else columns.count.desc()


@dataclass
class Aggregator[TRow](ABC):
    """Counts one entity's rows, in total and per group.

    ``conditions`` narrow the rows as a search's do, so ``total.count`` equals the search's
    total count. ``limit`` keeps that many groups per scope after ``orders``.
    """

    groups: Sequence[GroupBy] = field(default_factory=list)
    conditions: Sequence[QueryCondition] = field(default_factory=list)
    orders: Sequence[AggregateOrder] = field(default_factory=list)
    limit: int | None = None

    @abstractmethod
    def row_class(self) -> type[TRow]:
        raise NotImplementedError

    @abstractmethod
    def row_id_column(self) -> InstrumentedAttribute[Any]:
        """The column a scope's row ids are matched against."""
        raise NotImplementedError


@dataclass(frozen=True)
class AggregateValue:
    count: int


@dataclass(frozen=True)
class AggregateGroup:
    """One group: ``keys`` follow the aggregator's ``groups`` in order."""

    keys: Sequence[Any]
    value: AggregateValue


@dataclass(frozen=True)
class AggregateResult:
    total: AggregateValue
    groups: Sequence[AggregateGroup]


@dataclass(frozen=True)
class ScopeAggregateResult[TTarget: AggregateScopeTarget]:
    target: TTarget
    result: AggregateResult
