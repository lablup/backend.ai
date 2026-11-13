"""The statement an aggregate runs as: totals and kept groups of every scope in one query."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa

from ai.backend.common.exception import UnreachableError
from ai.backend.manager.models.scopes import AggregateScopeTarget
from ai.backend.manager.models.specs.aggregate.aggregator import (
    AggregateColumns,
    AggregateGroup,
    AggregateResult,
    AggregateValue,
    Aggregator,
)

__all__ = ("AggregateStatement",)

_SCOPE = "scope"
_ROW_ID = "row_id"
_COUNT = "count"
_GROUPING = "grouping"
_RANK = "rank"


class AggregateStatement:
    """Builds and reads one aggregate query.

    ``GROUPING SETS`` computes the totals and the groups together; a total row has rank 0,
    a group row its 1-based rank under the aggregator's orders. With scopes, each scope is
    a partition: the totals, the ranks and the limit are per scope.
    """

    _aggregator: Aggregator[Any]
    _targets: Sequence[AggregateScopeTarget] | None
    _key_names: Sequence[str]

    def __init__(
        self,
        aggregator: Aggregator[Any],
        targets: Sequence[AggregateScopeTarget] | None,
    ) -> None:
        self._aggregator = aggregator
        self._targets = targets
        self._key_names = [f"key_{index}" for index in range(len(aggregator.groups))]

    def build(self) -> sa.Select[Any] | sa.CompoundSelect[Any]:
        source = self._source()
        partition = [source.c[_SCOPE]] if self._targets is not None else []
        keys = [source.c[name] for name in self._key_names]
        if not keys:
            return (
                sa.select(*partition, sa.func.count().label(_COUNT), sa.literal(0).label(_RANK))
                .select_from(source)
                .group_by(*partition)
            )
        counted = (
            sa.select(
                *partition,
                *keys,
                sa.func.count().label(_COUNT),
                sa.func.grouping(*keys).label(_GROUPING),
            )
            .group_by(sa.func.grouping_sets(sa.tuple_(*partition), sa.tuple_(*partition, *keys)))
            .cte("aggregate_counts")
        )
        totals = sa.select(
            *self._partition_of(counted),
            *self._keys_of(counted),
            counted.c[_COUNT],
            sa.literal(0).label(_RANK),
        ).where(counted.c[_GROUPING] != 0)
        groups = self._filled(self._group_rows(counted))
        return sa.union_all(totals, self._kept(groups))

    def read(self, rows: Sequence[sa.Row[Any]]) -> list[AggregateResult]:
        """One result per scope in the order the targets were given, or one for no scope."""
        scope_count = len(self._targets) if self._targets is not None else 1
        totals = [0] * scope_count
        ranked: list[list[tuple[int, AggregateGroup]]] = [[] for _ in range(scope_count)]
        groups = self._aggregator.groups
        for row in rows:
            mapping = row._mapping
            scope = mapping[_SCOPE] if self._targets is not None else 0
            if mapping[_RANK] == 0:
                totals[scope] = mapping[_COUNT]
                continue
            keys = [
                group.to_key(mapping[name])
                for group, name in zip(groups, self._key_names, strict=True)
            ]
            ranked[scope].append((
                mapping[_RANK],
                AggregateGroup(keys=keys, value=AggregateValue(count=mapping[_COUNT])),
            ))
        return [
            AggregateResult(
                total=AggregateValue(count=totals[scope]),
                groups=[group for _, group in sorted(ranked[scope], key=lambda item: item[0])],
            )
            for scope in range(scope_count)
        ]

    def _source(self) -> sa.Subquery:
        """The rows to count: id, each group's value and, with scopes, the scope position."""
        aggregator = self._aggregator
        key_columns = [
            group.expression().label(name)
            for group, name in zip(aggregator.groups, self._key_names, strict=True)
        ]
        row_id = aggregator.row_id_column().label(_ROW_ID)
        if self._targets is None:
            query = sa.select(row_id, *key_columns).select_from(aggregator.row_class())
        else:
            scope_rows = self._scope_rows(self._targets)
            query = (
                sa.select(scope_rows.c[_SCOPE], row_id, *key_columns)
                .select_from(aggregator.row_class())
                .join(scope_rows, scope_rows.c[_ROW_ID] == aggregator.row_id_column())
            )
        for condition in aggregator.conditions:
            query = query.where(condition())
        return query.subquery("aggregate_source")

    def _scope_rows(self, targets: Sequence[AggregateScopeTarget]) -> sa.Subquery:
        """(scope position, row id) pairs, each pair once however many paths reach it."""
        selects = []
        for position, target in enumerate(targets):
            row_ids = target.scope_row_ids().subquery()
            selects.append(
                sa.select(
                    sa.literal(position, sa.Integer()).label(_SCOPE),
                    list(row_ids.c)[0].label(_ROW_ID),
                )
            )
        if len(selects) == 1:
            return selects[0].distinct().subquery("aggregate_scope_rows")
        return sa.union(*selects).subquery("aggregate_scope_rows")

    def _group_rows(self, counted: sa.CTE) -> sa.Select[Any]:
        """The group rows, without the NULL groups the request leaves out."""
        excluded_nulls = [
            counted.c[name].is_not(None)
            for group, name in zip(self._aggregator.groups, self._key_names, strict=True)
            if not group.include_null()
        ]
        return sa.select(
            *self._partition_of(counted), *self._keys_of(counted), counted.c[_COUNT]
        ).where(counted.c[_GROUPING] == 0, *excluded_nulls)

    def _filled(self, group_rows: sa.Select[Any]) -> sa.Subquery:
        """The group rows plus a zero count for every value asked for that no row has.

        The values are crossed with the scopes, and with the other keys' combinations that
        have rows.
        """
        groups = self._aggregator.groups
        if not any(group.empty_values() for group in groups):
            return group_rows.subquery("aggregate_groups")
        found = group_rows.cte("aggregate_found")
        fixed = [
            found.c[name]
            for group, name in zip(groups, self._key_names, strict=True)
            if not group.empty_values()
        ]
        domains: list[sa.FromClause] = []
        if fixed:
            domains.append(
                sa.select(*self._partition_of(found), *fixed).distinct().subquery("aggregate_seen")
            )
        elif self._targets is not None:
            domains.append(
                sa.values(sa.column(_SCOPE, sa.Integer()), name="aggregate_scopes").data([
                    (position,) for position in range(len(self._targets))
                ])
            )
        for index, (group, name) in enumerate(zip(groups, self._key_names, strict=True)):
            values = group.empty_values()
            if values:
                domains.append(
                    sa.values(
                        sa.column(name, group.expression().type), name=f"aggregate_values_{index}"
                    ).data([(value,) for value in values])
                )
        joined: sa.FromClause = domains[0]
        for domain in domains[1:]:
            joined = sa.join(joined, domain, sa.true())

        def domain_column(name: str) -> sa.ColumnElement[Any]:
            for domain in domains:
                if name in domain.c:
                    return domain.c[name]
            raise UnreachableError(f"{name} is in no aggregate domain")

        names = [*([_SCOPE] if self._targets is not None else []), *self._key_names]
        matched = sa.and_(
            sa.true(), *[domain_column(name).is_not_distinct_from(found.c[name]) for name in names]
        )
        return (
            sa.select(
                *[domain_column(name).label(name) for name in names],
                sa.func.coalesce(found.c[_COUNT], 0).label(_COUNT),
            )
            .select_from(joined.outerjoin(found, matched))
            .subquery("aggregate_groups")
        )

    def _kept(self, groups: sa.Subquery) -> sa.Select[Any]:
        """The groups ranked by the orders, cut at the limit within each scope."""
        aggregator = self._aggregator
        columns = AggregateColumns(
            keys=[
                (group, groups.c[name])
                for group, name in zip(aggregator.groups, self._key_names, strict=True)
            ],
            count=groups.c[_COUNT],
        )
        order_by = [
            *(order.apply(columns) for order in aggregator.orders),
            *(groups.c[name].asc() for name in self._key_names),
        ]
        ranked = sa.select(
            *self._partition_of(groups),
            *self._keys_of(groups),
            groups.c[_COUNT],
            sa.func.row_number()
            .over(partition_by=self._partition_of(groups), order_by=order_by)
            .label(_RANK),
        ).subquery("aggregate_ranked")
        kept = sa.select(*ranked.c)
        if aggregator.limit is not None:
            kept = kept.where(ranked.c[_RANK] <= aggregator.limit)
        return kept

    def _partition_of(self, source: sa.FromClause) -> list[sa.ColumnElement[Any]]:
        return [source.c[_SCOPE]] if self._targets is not None else []

    def _keys_of(self, source: sa.FromClause) -> list[sa.ColumnElement[Any]]:
        return [source.c[name] for name in self._key_names]
