"""Scenario 나: what a declared order sorts by, where nulls land, and how it pages."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

import sqlalchemy as sa

from ai.backend.manager.models.specs.pagination import (
    CursorForwardPagination,
    OffsetPagination,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from .shelf_fields import ShelfSearchableFields
from .shelf_fixtures import Seeded, SeededShelf
from .shelf_rows import CategoryRow, ShelfKind, ShelfRow
from .shelf_search import ShelfSearches, ordered_ids

OWN = ShelfSearchableFields.own
CATEGORY = ShelfSearchableFields.nested.category


def _sorted_ids(
    seeded: Seeded, key: Callable[[SeededShelf], Any], *, ascending: bool
) -> list[uuid.UUID]:
    """The ids the fixed rows take when sorted in Python, with the id as the tiebreak.

    Sorted by id first, then stably by the key, which is what ``ORDER BY key, id`` does.
    """
    ordered = sorted(seeded.shelves.values(), key=lambda shelf: shelf.id)
    return [shelf.id for shelf in sorted(ordered, key=key, reverse=not ascending)]


class TestSingleColumnOrders:
    async def test_나1_each_type_matches_the_python_ordering(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        cases: list[tuple[Any, Callable[[SeededShelf], Any]]] = [
            (OWN.count, lambda shelf: shelf.count),
            (OWN.price, lambda shelf: shelf.price),
            (OWN.opened_at, lambda shelf: shelf.opened_at),
            (OWN.active, lambda shelf: shelf.active),
            (OWN.kind, lambda shelf: list(ShelfKind).index(shelf.kind)),
            (OWN.id, lambda shelf: shelf.id),
        ]
        for field, key in cases:
            for ascending in (True, False):
                result = await searches.in_global(
                    orders=[field.order.apply(ascending), OWN.id.order.apply(True)]
                )
                assert ordered_ids(result) == _sorted_ids(seeded, key, ascending=ascending)

    async def test_나1_string_order_matches_the_database_collation(
        self, searches: ShelfSearches, shelf_db: ExtendedAsyncSAEngine, seeded: Seeded
    ) -> None:
        """The declaration is checked against ``ORDER BY name``, not a Python ordering:
        the collation the server sorts text with is the server's, not Python's."""
        async with shelf_db.begin_readonly_session() as sess:
            expected = list(
                (await sess.scalars(sa.select(ShelfRow.id).order_by(ShelfRow.name.asc()))).all()
            )

        result = await searches.in_global(orders=[OWN.name.order.apply(True)])

        assert ordered_ids(result) == expected

    async def test_나2_nulls_sort_last_ascending_and_first_descending(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        """Fixed behavior: the server's default, NULLS LAST for ASC and NULLS FIRST for DESC."""
        ascending = await searches.in_global(
            orders=[OWN.closed_at.order.apply(True), OWN.id.order.apply(True)]
        )
        descending = await searches.in_global(
            orders=[OWN.closed_at.order.apply(False), OWN.id.order.apply(True)]
        )
        null_ids = sorted(seeded.shelf_ids("S1", "S4"))

        assert ordered_ids(ascending) == seeded.ordered_shelf_ids("S2", "S3") + null_ids
        assert ordered_ids(descending) == null_ids + seeded.ordered_shelf_ids("S3", "S2")

    async def test_나3_a_tie_broken_by_a_second_key_survives_paging(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        orders = [OWN.count.order.apply(True), OWN.id.order.apply(True)]
        whole = await searches.in_global(orders=orders)
        first = await searches.in_global(
            orders=orders, pagination=OffsetPagination(limit=2, offset=0)
        )
        second = await searches.in_global(
            orders=orders, pagination=OffsetPagination(limit=2, offset=2)
        )

        assert ordered_ids(whole) == _sorted_ids(seeded, lambda shelf: shelf.count, ascending=True)
        assert ordered_ids(first) + ordered_ids(second) == ordered_ids(whole)

    async def test_나4_order_by_a_to_one_column_puts_the_missing_row_last(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        """S3 and S4 have no category, so their rank subquery is null: NULLS LAST."""
        result = await searches.in_global(
            orders=[
                CATEGORY.correlation.order(CategoryRow.rank).apply(True),
                OWN.id.order.apply(True),
            ]
        )
        ranked = seeded.ordered_shelf_ids("S2", "S1")

        assert ordered_ids(result)[:2] == ranked
        assert ordered_ids(result)[2:] == sorted(seeded.shelf_ids("S3", "S4"))


class TestOrderedPaging:
    async def test_나5_offset_pages_cover_every_row_once(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        orders = [OWN.price.order.apply(True), OWN.id.order.apply(True)]
        collected: list[uuid.UUID] = []
        for offset in (0, 2):
            page = await searches.in_global(
                orders=orders, pagination=OffsetPagination(limit=2, offset=offset)
            )
            assert page.total_count == len(seeded.shelves)
            collected += ordered_ids(page)

        assert collected == _sorted_ids(seeded, lambda shelf: shelf.price, ascending=True)

    async def test_나5_cursor_pages_cover_every_row_once(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        expected = _sorted_ids(seeded, lambda shelf: shelf.id, ascending=True)
        first = await searches.in_global(
            pagination=CursorForwardPagination(first=2, cursor_order=ShelfRow.id.asc())
        )
        last_id = ordered_ids(first)[-1]
        second = await searches.in_global(
            pagination=CursorForwardPagination(
                first=2,
                cursor_order=ShelfRow.id.asc(),
                cursor_condition=lambda: ShelfRow.id > last_id,
            )
        )

        assert first.total_count == len(seeded.shelves)
        assert first.has_next_page is True
        assert second.has_next_page is False
        assert ordered_ids(first) + ordered_ids(second) == expected
