"""The two aggregate ops paths against a real database, over a table declared here.

- The admin total equals the search total under the same conditions, and the group counts
  add up to it.
- Datetime buckets are half-open: a row on a boundary falls into the later bucket.
- Each scope is counted on its own; its total equals that scope's search total, and a row
  reached by two paths of one scope is counted once.
- A count order and a limit keep the top groups of each scope.
- NULL keys are dropped unless asked for; an enum group fills the values no row has.
"""

from __future__ import annotations

import enum
import uuid
from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, override
from zoneinfo import ZoneInfo

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute, Mapped, mapped_column

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.manager.models.base import GUID, Base, StrEnumType
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.scopes import AggregateScopeTarget, ExistenceCheck
from ai.backend.manager.models.specs.aggregate.aggregator import (
    AggregateResult,
    Aggregator,
    CountOrder,
    GroupKeyOrder,
)
from ai.backend.manager.models.specs.aggregate.group import (
    DateTimeBucket,
    DateTimeGroupField,
    EnumGroupField,
    StringGroupField,
    UUIDGroupField,
)
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.specs.search.field import SearchableField
from ai.backend.manager.models.specs.searcher import Searcher
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import with_tables

_START = datetime(2026, 1, 5, tzinfo=UTC)


class _Status(enum.StrEnum):
    OK = "ok"
    FAILED = "failed"
    SKIPPED = "skipped"


class _ItemRow(Base):
    __tablename__ = "test_aggregate_items"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column("id", GUID(), primary_key=True)
    status: Mapped[_Status] = mapped_column("status", StrEnumType(_Status), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        "created_at", sa.DateTime(timezone=True), nullable=False
    )
    owner_id: Mapped[uuid.UUID | None] = mapped_column("owner_id", GUID(), nullable=True)
    label: Mapped[str | None] = mapped_column("label", sa.String(64), nullable=True)


class _ItemLinkRow(Base):
    """A second path from a scope to an item."""

    __tablename__ = "test_aggregate_item_links"
    __table_args__ = {"extend_existing": True}

    scope_id: Mapped[uuid.UUID] = mapped_column("scope_id", GUID(), primary_key=True)
    item_id: Mapped[uuid.UUID] = mapped_column("item_id", GUID(), primary_key=True)


class _ItemAggregateFields:
    status = EnumGroupField(
        SearchableField(_ItemRow.status, None, None),
        _Status,
    )
    created_at = DateTimeGroupField(SearchableField(_ItemRow.created_at, None, None))
    owner_id = UUIDGroupField(SearchableField(_ItemRow.owner_id, None, None))
    label = StringGroupField(SearchableField(_ItemRow.label, None, None))


@dataclass
class _ItemAggregator(Aggregator[_ItemRow]):
    @override
    def row_class(self) -> type[_ItemRow]:
        return _ItemRow

    @override
    def row_id_column(self) -> InstrumentedAttribute[Any]:
        return _ItemRow.id


@dataclass
class _ItemSearcher(Searcher[_ItemRow, uuid.UUID]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(_ItemRow)

    @override
    def to_data(self, row: _ItemRow) -> uuid.UUID:
        return row.id


class _OwnerID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserEntityType()


@dataclass(frozen=True)
class _OwnerTarget(AggregateScopeTarget):
    """The items an owner holds, by the owner column or by a link."""

    owner: _OwnerID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.owner

    @override
    def to_condition(self) -> QueryCondition:
        owner = self.owner

        def inner() -> sa.ColumnElement[bool]:
            return sa.or_(
                _ItemRow.owner_id == owner,
                sa.exists().where(
                    _ItemLinkRow.item_id == _ItemRow.id, _ItemLinkRow.scope_id == owner
                ),
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()

    @override
    def scope_row_ids(self) -> sa.SelectBase:
        return sa.union_all(
            sa.select(_ItemRow.id).where(_ItemRow.owner_id == self.owner),
            sa.select(_ItemLinkRow.item_id).where(_ItemLinkRow.scope_id == self.owner),
        )


class _Items:
    owner_a: _OwnerID
    owner_b: _OwnerID

    def __init__(self, owner_a: _OwnerID, owner_b: _OwnerID) -> None:
        self.owner_a = owner_a
        self.owner_b = owner_b


@pytest.fixture
async def database(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, [_ItemRow, _ItemLinkRow]):
        yield database_connection


@pytest.fixture
def repository(database: ExtendedAsyncSAEngine) -> OpsRepository[Any]:
    return OpsRepository(V2DBOpsProvider(database))


@pytest.fixture
async def items(database: ExtendedAsyncSAEngine) -> _Items:
    """Seven items. Owner A reaches five (one by both paths), owner B three."""
    owner_a = _OwnerID(uuid.uuid4())
    owner_b = _OwnerID(uuid.uuid4())
    ids = [uuid.uuid4() for _ in range(7)]
    rows = [
        (ids[0], _Status.OK, 0, owner_a, "x"),
        (ids[1], _Status.OK, 1, owner_a, "x"),
        (ids[2], _Status.FAILED, 3, owner_a, None),
        (ids[3], _Status.FAILED, 4, owner_b, "y"),
        (ids[4], _Status.FAILED, 7, owner_b, "y"),
        (ids[5], _Status.OK, 7, None, None),
        (ids[6], _Status.FAILED, 2, owner_a, "x"),
    ]
    links = [(owner_a, ids[5]), (owner_a, ids[6]), (owner_b, ids[0])]
    async with database.begin_session() as sess:
        await sess.execute(
            sa.insert(_ItemRow),
            [
                {
                    "id": item_id,
                    "status": status,
                    "created_at": _START + timedelta(hours=hours),
                    "owner_id": owner,
                    "label": label,
                }
                for item_id, status, hours, owner, label in rows
            ],
        )
        await sess.execute(
            sa.insert(_ItemLinkRow),
            [{"scope_id": scope, "item_id": item_id} for scope, item_id in links],
        )
    return _Items(owner_a, owner_b)


def _failed() -> QueryCondition:
    return lambda: _ItemRow.status == _Status.FAILED


def _counts(result: AggregateResult) -> list[tuple[Sequence[Any], int]]:
    return [(group.keys, group.value.count) for group in result.groups]


class TestAggregateInGlobal:
    async def test_total_equals_search_total_under_the_same_conditions(
        self, repository: OpsRepository[Any], items: _Items
    ) -> None:
        searched = await repository.search_in_global(
            _ItemSearcher(pagination=OffsetPagination(limit=1), conditions=[_failed()])
        )

        result = await repository.aggregate_in_global(_ItemAggregator(conditions=[_failed()]))

        assert result.total.count == searched.total_count == 4
        assert result.groups == []

    async def test_group_counts_add_up_to_the_total(
        self, repository: OpsRepository[Any], items: _Items
    ) -> None:
        status = _ItemAggregateFields.status.by(include_empty=False)

        result = await repository.aggregate_in_global(_ItemAggregator(groups=[status]))

        assert result.total.count == 7
        assert sorted(_counts(result)) == [([_Status.FAILED], 4), ([_Status.OK], 3)]

    async def test_a_row_on_a_bucket_boundary_falls_into_the_later_bucket(
        self, repository: OpsRepository[Any], items: _Items
    ) -> None:
        bucket = _ItemAggregateFields.created_at.by(
            interval=timedelta(hours=3), timezone=ZoneInfo("UTC")
        )

        result = await repository.aggregate_in_global(_ItemAggregator(groups=[bucket]))

        hours = timedelta(hours=1)
        assert sorted(_counts(result), key=lambda item: item[0][0].start) == [
            ([DateTimeBucket(_START, _START + 3 * hours)], 3),
            ([DateTimeBucket(_START + 3 * hours, _START + 6 * hours)], 2),
            ([DateTimeBucket(_START + 6 * hours, _START + 9 * hours)], 2),
        ]

    async def test_buckets_align_to_midnight_in_the_time_zone(
        self, repository: OpsRepository[Any], items: _Items
    ) -> None:
        seoul = ZoneInfo("Asia/Seoul")
        bucket = _ItemAggregateFields.created_at.by(interval=timedelta(days=1), timezone=seoul)

        result = await repository.aggregate_in_global(_ItemAggregator(groups=[bucket]))

        midnight = datetime(2026, 1, 5, tzinfo=seoul)
        assert _counts(result) == [([DateTimeBucket(midnight, midnight + timedelta(days=1))], 7)]

    async def test_null_keys_are_dropped_unless_asked_for(
        self, repository: OpsRepository[Any], items: _Items
    ) -> None:
        without_null = await repository.aggregate_in_global(
            _ItemAggregator(groups=[_ItemAggregateFields.label.by(include_null=False)])
        )
        with_null = await repository.aggregate_in_global(
            _ItemAggregator(groups=[_ItemAggregateFields.owner_id.by(include_null=True)])
        )

        assert without_null.total.count == 7
        assert sorted(_counts(without_null)) == [(["x"], 3), (["y"], 2)]
        assert ([None], 1) in _counts(with_null)
        assert sum(count for _, count in _counts(with_null)) == 7

    async def test_enum_group_fills_the_values_no_row_has(
        self, repository: OpsRepository[Any], items: _Items
    ) -> None:
        status = _ItemAggregateFields.status.by(include_empty=True)

        result = await repository.aggregate_in_global(_ItemAggregator(groups=[status]))

        assert sorted(_counts(result)) == [
            ([_Status.FAILED], 4),
            ([_Status.OK], 3),
            ([_Status.SKIPPED], 0),
        ]


class TestAggregateInScopes:
    async def test_each_total_equals_that_scope_search_total(
        self, repository: OpsRepository[Any], items: _Items
    ) -> None:
        targets = [_OwnerTarget(items.owner_a), _OwnerTarget(items.owner_b)]
        searched = [
            await repository.search_in_scopes([target], _ItemSearcher(OffsetPagination(limit=1)))
            for target in targets
        ]

        results = await repository.aggregate_in_scopes(targets, _ItemAggregator())

        assert [result.total.count for result in results] == [
            search.total_count for search in searched
        ]
        assert [result.total.count for result in results] == [5, 3]

    async def test_groups_are_counted_per_scope(
        self, repository: OpsRepository[Any], items: _Items
    ) -> None:
        status = _ItemAggregateFields.status.by(include_empty=True)
        targets = [_OwnerTarget(items.owner_a), _OwnerTarget(items.owner_b)]

        results = await repository.aggregate_in_scopes(
            targets, _ItemAggregator(groups=[status], orders=[GroupKeyOrder(status, True)])
        )

        assert _counts(results[0]) == [
            ([_Status.FAILED], 2),
            ([_Status.OK], 3),
            ([_Status.SKIPPED], 0),
        ]
        assert _counts(results[1]) == [
            ([_Status.FAILED], 2),
            ([_Status.OK], 1),
            ([_Status.SKIPPED], 0),
        ]

    async def test_count_order_and_limit_keep_the_top_groups_of_each_scope(
        self, repository: OpsRepository[Any], items: _Items
    ) -> None:
        bucket = _ItemAggregateFields.created_at.by(
            interval=timedelta(hours=3), timezone=ZoneInfo("UTC")
        )
        targets = [_OwnerTarget(items.owner_a), _OwnerTarget(items.owner_b)]

        results = await repository.aggregate_in_scopes(
            targets, _ItemAggregator(groups=[bucket], orders=[CountOrder(False)], limit=1)
        )

        assert [result.total.count for result in results] == [5, 3]
        assert [len(result.groups) for result in results] == [1, 1]
        assert results[0].groups[0].keys == [DateTimeBucket(_START, _START + timedelta(hours=3))]
        assert results[0].groups[0].value.count == 3
        assert results[1].groups[0].value.count == 1

    async def test_a_scope_with_no_rows_has_a_zero_total(
        self, repository: OpsRepository[Any], items: _Items
    ) -> None:
        status = _ItemAggregateFields.status.by(include_empty=False)

        results = await repository.aggregate_in_scopes(
            [_OwnerTarget(_OwnerID(uuid.uuid4()))], _ItemAggregator(groups=[status])
        )

        assert results[0].total.count == 0
        assert results[0].groups == []
