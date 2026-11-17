"""Partial reads: a searcher or querier given ``fields`` reads the id and those columns only."""

from __future__ import annotations

import uuid
from typing import Any

import pytest

from ai.backend.common.errors.partial_record import InvalidPartialRecordError, NotSelectedError
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.models.specs.pagination import (
    CursorForwardPagination,
    NoPagination,
    OffsetPagination,
    QueryPagination,
)
from ai.backend.manager.models.specs.search.field import QueryColumn
from ai.backend.manager.models.specs.searcher import GlobalSearcher, ScopedSearcher, SearcherResult
from ai.backend.manager.repositories.ops.repository import OpsRepository

from .shelf_fields import (
    ShelfPartialQuerier,
    ShelfPartialSearcher,
    ShelfSearchableFields,
    ZoneShelfTarget,
)
from .shelf_fixtures import TIMES, Seeded
from .shelf_rows import ShelfID, ShelfPartialData, ShelfRow

OWN = ShelfSearchableFields.own
SHELF_COLUMNS: list[QueryColumn[Any, Any, Any]] = [
    OWN.id,
    OWN.name,
    OWN.note,
    OWN.count,
    OWN.price,
    OWN.kind,
    OWN.active,
    OWN.tags,
    OWN.opened_at,
    OWN.closed_at,
    OWN.stocked_on,
    OWN.zone_id,
    OWN.category_id,
]


class _UndeclaredColumns:
    label = QueryColumn(ShelfRow.name, None, None)


def _searcher(
    fields: list[QueryColumn[Any, Any, Any]] | None,
    pagination: QueryPagination | None = None,
    **options: Any,
) -> GlobalSearcher[Any, ShelfPartialData]:
    return GlobalSearcher(
        used_by=(),
        searcher=ShelfPartialSearcher(
            pagination=pagination if pagination is not None else NoPagination(),
            fields=fields,
            **options,
        ),
    )


def _ids(result: SearcherResult[ShelfPartialData]) -> list[uuid.UUID]:
    return [item.id for item in result.items]


class TestPartialSearch:
    async def test_items_hold_the_id_and_the_requested_fields(
        self, partial_reads: OpsRepository[ShelfPartialData], seeded: Seeded
    ) -> None:
        result = await partial_reads.global_search(_searcher([OWN.name, OWN.count]))

        assert {item.id: (item.name, item.count) for item in result.items} == {
            shelf.id: (shelf.name, shelf.count) for shelf in seeded.shelves.values()
        }
        assert {item.selected_fields() for item in result.items} == {("id", "name", "count")}

    async def test_reading_a_field_not_requested_raises(
        self, partial_reads: OpsRepository[ShelfPartialData], seeded: Seeded
    ) -> None:
        result = await partial_reads.global_search(_searcher([OWN.name]))

        with pytest.raises(NotSelectedError):
            _ = result.items[0].count

    async def test_a_null_value_is_selected(
        self, partial_reads: OpsRepository[ShelfPartialData], seeded: Seeded
    ) -> None:
        result = await partial_reads.global_search(
            _searcher([OWN.note], conditions=[OWN.count.filter.equals(1)])
        )

        assert result.items[0].is_selected("note")
        assert result.items[0].note is None

    async def test_no_fields_reads_the_id_only(
        self, partial_reads: OpsRepository[ShelfPartialData], seeded: Seeded
    ) -> None:
        result = await partial_reads.global_search(_searcher([]))

        assert set(_ids(result)) == seeded.shelf_ids("S1", "S2", "S3", "S4")
        assert {item.selected_fields() for item in result.items} == {("id",)}

    async def test_requesting_the_id_reads_it_once(
        self,
        partial_reads: OpsRepository[ShelfPartialData],
        seeded: Seeded,
        shelf_select_lists: list[list[str]],
    ) -> None:
        await partial_reads.global_search(_searcher([OWN.id, OWN.name]))

        assert shelf_select_lists == [["test_search_shelf.id", "test_search_shelf.name"]]

    async def test_fields_of_none_reads_the_whole_row(
        self,
        partial_reads: OpsRepository[ShelfPartialData],
        seeded: Seeded,
        shelf_select_lists: list[list[str]],
    ) -> None:
        result = await partial_reads.global_search(_searcher(None))

        assert {item.selected_fields() for item in result.items} == {
            tuple(column.name for column in SHELF_COLUMNS)
        }
        assert len(shelf_select_lists[0]) == len(SHELF_COLUMNS)

    async def test_filter_and_order_by_fields_not_requested_match_the_full_read(
        self, partial_reads: OpsRepository[ShelfPartialData], seeded: Seeded
    ) -> None:
        options: dict[str, Any] = {
            "conditions": [OWN.count.filter.greater_than(1)],
            "orders": [OWN.price.order.apply(False), OWN.id.order.apply(True)],
        }

        partial = await partial_reads.global_search(_searcher([OWN.name], **options))
        full = await partial_reads.global_search(_searcher(None, **options))

        assert _ids(partial) == _ids(full)
        assert _ids(partial) == seeded.ordered_shelf_ids("S3", "S2", "S4")

    async def test_select_list_holds_only_the_id_and_the_requested_columns(
        self,
        partial_reads: OpsRepository[ShelfPartialData],
        seeded: Seeded,
        shelf_select_lists: list[list[str]],
    ) -> None:
        await partial_reads.global_search(
            _searcher(
                [OWN.name, OWN.count],
                conditions=[OWN.active.filter.equals(True)],
                orders=[OWN.opened_at.order.apply(True)],
            )
        )

        assert shelf_select_lists == [
            ["test_search_shelf.id", "test_search_shelf.name", "test_search_shelf.count"]
        ]

    async def test_offset_pages_match_the_full_read(
        self, partial_reads: OpsRepository[ShelfPartialData], seeded: Seeded
    ) -> None:
        pagination = OffsetPagination(limit=2, offset=1)
        orders = [OWN.opened_at.order.apply(True)]

        partial = await partial_reads.global_search(
            _searcher([OWN.name], pagination, orders=orders)
        )
        full = await partial_reads.global_search(_searcher(None, pagination, orders=orders))

        assert _ids(partial) == _ids(full) == seeded.ordered_shelf_ids("S2", "S3")
        assert (partial.total_count, partial.has_next_page, partial.has_previous_page) == (
            full.total_count,
            full.has_next_page,
            full.has_previous_page,
        )

    async def test_cursor_pages_match_the_full_read(
        self,
        partial_reads: OpsRepository[ShelfPartialData],
        seeded: Seeded,
        shelf_select_lists: list[list[str]],
    ) -> None:
        pagination = CursorForwardPagination(
            first=2,
            cursor_order=OWN.opened_at.order.apply(True),
            cursor_condition=OWN.opened_at.filter.after(TIMES[0]),
        )

        partial = await partial_reads.global_search(_searcher([OWN.name], pagination))
        full = await partial_reads.global_search(_searcher(None, pagination))

        assert _ids(partial) == _ids(full) == seeded.ordered_shelf_ids("S2", "S3")
        assert (partial.total_count, partial.has_next_page, partial.has_previous_page) == (
            full.total_count,
            full.has_next_page,
            full.has_previous_page,
        )
        assert shelf_select_lists[0] == ["test_search_shelf.id", "test_search_shelf.name"]

    async def test_scoped_search_reads_the_requested_fields(
        self, partial_reads: OpsRepository[ShelfPartialData], seeded: Seeded
    ) -> None:
        result = await partial_reads.scoped_search(
            ScopedSearcher(
                scopes=[ZoneShelfTarget(seeded.zones["Z1"])],
                used_by=(),
                searcher=ShelfPartialSearcher(pagination=NoPagination(), fields=[OWN.kind]),
            )
        )

        assert {item.id: item.kind for item in result.items} == {
            seeded.shelves[key].id: seeded.shelves[key].kind for key in ("S1", "S2")
        }

    async def test_a_field_the_record_does_not_declare_raises(
        self, partial_reads: OpsRepository[ShelfPartialData], seeded: Seeded
    ) -> None:
        with pytest.raises(InvalidPartialRecordError):
            await partial_reads.global_search(_searcher([OWN.name, _UndeclaredColumns.label]))


class TestPartialGet:
    async def test_result_holds_the_id_and_the_requested_fields(
        self,
        partial_reads: OpsRepository[ShelfPartialData],
        seeded: Seeded,
        shelf_select_lists: list[list[str]],
    ) -> None:
        shelf = seeded.shelves["S2"]

        data = await partial_reads.get(
            ShelfPartialQuerier(ShelfID(shelf.id), fields=[OWN.name, OWN.closed_at])
        )

        assert data.selected_fields() == ("id", "name", "closed_at")
        assert (data.id, data.name, data.closed_at) == (shelf.id, shelf.name, shelf.closed_at)
        with pytest.raises(NotSelectedError):
            _ = data.count
        assert shelf_select_lists == [
            ["test_search_shelf.id", "test_search_shelf.name", "test_search_shelf.closed_at"]
        ]

    async def test_fields_of_none_reads_the_whole_row(
        self, partial_reads: OpsRepository[ShelfPartialData], seeded: Seeded
    ) -> None:
        shelf = seeded.shelves["S1"]

        data = await partial_reads.get(ShelfPartialQuerier(ShelfID(shelf.id)))

        assert data.selected_fields() == tuple(column.name for column in SHELF_COLUMNS)
        assert (data.price, data.tags) == (shelf.price, shelf.tags)

    async def test_missing_id_raises_not_found(
        self, partial_reads: OpsRepository[ShelfPartialData], seeded: Seeded
    ) -> None:
        with pytest.raises(EntityNotFoundError):
            await partial_reads.get(ShelfPartialQuerier(ShelfID(uuid.uuid4()), fields=[OWN.name]))
