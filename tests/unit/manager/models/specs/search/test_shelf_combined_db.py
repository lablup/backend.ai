"""Scenario 사: scope, use, filter, nesting, order and paging on one search."""

from __future__ import annotations

import pytest
import sqlalchemy as sa

from ai.backend.manager.errors.repository import EmptyOperationScopeError
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from .shelf_fields import (
    BoxSearchableFields,
    ShelfSearchableFields,
    SpecSearchableFields,
)
from .shelf_fixtures import Seeded
from .shelf_rows import BoxRow, BoxState, CategoryRow, ShelfKind, SpecRow
from .shelf_search import ShelfSearches, ids, ordered_ids, spec_graded

OWN = ShelfSearchableFields.own
BOXES = ShelfSearchableFields.nested.boxes
CATEGORY = ShelfSearchableFields.nested.category
CARTS = ShelfSearchableFields.linked.usage.carts
BOX = BoxSearchableFields.own


class TestCombinedSearch:
    async def test_사1_scopes_are_or_ed_and_filters_and_ed(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        result = await searches.scoped(
            zones=[seeded.zones["Z1"], seeded.zones["Z2"]],
            conditions=[OWN.count.filter.equals(5)],
        )

        assert ids(result) == seeded.shelf_ids("S2", "S3")
        assert result.total_count == 2

    async def test_사2_each_kind_of_condition_narrows_independently(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        result = await searches.scoped(
            zones=[seeded.zones["Z1"]],
            conditions=[
                OWN.kind.filter.equals(ShelfKind.BOOK),
                BOXES.correlation.some([BOX.state.filter.equals(BoxState.OPEN)]),
            ],
            orders=[OWN.name.order.apply(True)],
            used_by=[CARTS.used_by(seeded.carts["K1"])],
        )

        assert ids(result) == seeded.shelf_ids("S1")
        assert result.total_count == 1

    async def test_사3_an_empty_scope_list_is_refused(self, searches: ShelfSearches) -> None:
        with pytest.raises(EmptyOperationScopeError):
            await searches.scoped(zones=[])

    async def test_사4_two_level_nesting_with_a_to_one_order_pages_cleanly(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        conditions = [BOXES.correlation.some([BOX.size.filter.equals(9), spec_graded("y")])]
        orders = [
            CATEGORY.correlation.order(CategoryRow.rank).apply(True),
            OWN.id.order.apply(True),
        ]
        first = await searches.in_global(
            conditions=conditions, orders=orders, pagination=OffsetPagination(limit=1, offset=0)
        )
        second = await searches.in_global(
            conditions=conditions, orders=orders, pagination=OffsetPagination(limit=1, offset=1)
        )

        assert first.total_count == 2
        assert second.total_count == 2
        assert ordered_ids(first) + ordered_ids(second) == seeded.ordered_shelf_ids("S2", "S1")

    async def test_사5_the_declaration_reads_back_what_the_row_holds(
        self, searches: ShelfSearches, shelf_db: ExtendedAsyncSAEngine, seeded: Seeded
    ) -> None:
        result = await searches.in_global(
            conditions=[OWN.count.filter.equals(seeded.shelves["S2"].count)],
            orders=[OWN.id.order.apply(True)],
        )
        converted = {item.id: item for item in result.items}
        expected = seeded.shelves["S2"]
        item = converted[expected.id]

        assert (item.name, item.note, item.count, item.price) == (
            expected.name,
            expected.note,
            expected.count,
            expected.price,
        )
        assert (item.kind, item.active, item.tags) == (
            expected.kind,
            expected.active,
            expected.tags,
        )
        assert (item.opened_at, item.closed_at) == (expected.opened_at, expected.closed_at)
        assert (item.zone_id, item.category_id) == (expected.zone_id, expected.category_id)

        async with shelf_db.begin_readonly_session() as sess:
            box_row = (
                await sess.scalars(sa.select(BoxRow).where(BoxRow.id == seeded.boxes["B3"]))
            ).one()
            box = BoxSearchableFields.own.to_data(box_row)
            spec_row = (
                await sess.scalars(sa.select(SpecRow).where(SpecRow.id == seeded.specs["P3"]))
            ).one()
            spec = SpecSearchableFields.own.to_data(spec_row)

        assert (box.shelf_id, box.label, box.size, box.state, box.spec_id) == (
            expected.id,
            "b3",
            9,
            BoxState.OPEN,
            seeded.specs["P3"],
        )
        assert (spec.shelf_id, spec.grade, spec.weight) == (expected.id, "y", 5)
