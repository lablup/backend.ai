"""Scenario 바: narrowing a search by which other entity uses the row."""

from __future__ import annotations

from .shelf_fields import ShelfSearchableFields
from .shelf_fixtures import Seeded
from .shelf_search import ShelfSearches, ids

CARTS = ShelfSearchableFields.linked.usage.carts


class TestUsedBy:
    async def test_바1_the_extra_join_condition_applies(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        """K1 also has a line for S2, but it is revoked, and a revoked line is not a use."""
        result = await searches.in_global(used_by=[CARTS.used_by(seeded.carts["K1"])])

        assert ids(result) == seeded.shelf_ids("S1")

    async def test_바2_every_row_the_entity_uses_is_returned(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        result = await searches.in_global(used_by=[CARTS.used_by(seeded.carts["K2"])])

        assert ids(result) == seeded.shelf_ids("S2", "S4")

    async def test_바3_an_entity_using_nothing_returns_nothing(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        result = await searches.in_global(used_by=[CARTS.used_by(seeded.carts["K3"])])

        assert ids(result) == set()
        assert result.total_count == 0

    async def test_바4_several_uses_are_and_ed(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        result = await searches.in_global(
            used_by=[
                CARTS.used_by(seeded.carts["K1"]),
                CARTS.used_by(seeded.carts["K2"]),
            ]
        )

        assert ids(result) == set()

    async def test_바5_a_use_does_not_reach_past_the_scope(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        """K2 uses S4 too, but S4 sits in the zone the search was not given."""
        result = await searches.scoped(
            zones=[seeded.zones["Z1"]],
            used_by=[CARTS.used_by(seeded.carts["K2"])],
        )

        assert ids(result) == seeded.shelf_ids("S2")

    async def test_바6_a_global_search_applies_the_use_with_no_scope_condition(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        result = await searches.in_global(used_by=[CARTS.used_by(seeded.carts["K2"])])

        assert ids(result) == seeded.shelf_ids("S2", "S4")
        assert result.total_count == 2
