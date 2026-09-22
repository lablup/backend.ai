"""Scenario 가: one declared field's conditions, run against the database."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from ai.backend.common.data.filter_specs import (
    StringInMatchSpec,
    StringMatchSpec,
    UUIDEqualMatchSpec,
    UUIDInMatchSpec,
)
from ai.backend.common.dto.manager.query import DateRangeFilter
from ai.backend.manager.repositories.base.filter_adapter import BaseFilterAdapter

from .shelf_fields import ShelfSearchableFields
from .shelf_fixtures import DATES, TIMES, Seeded
from .shelf_rows import ShelfKind
from .shelf_search import ShelfSearches, ids

OWN = ShelfSearchableFields.own


def _match(value: str, *, case_insensitive: bool = False, negated: bool = False) -> StringMatchSpec:
    return StringMatchSpec(value=value, case_insensitive=case_insensitive, negated=negated)


class TestStringFilters:
    async def test_가1_contains_honors_case_insensitivity(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        insensitive = await searches.in_global(
            conditions=[OWN.name.filter.contains(_match("alpha", case_insensitive=True))]
        )
        sensitive = await searches.in_global(conditions=[OWN.name.filter.contains(_match("alpha"))])

        assert ids(insensitive) == seeded.shelf_ids("S1", "S2")
        assert ids(sensitive) == seeded.shelf_ids("S2")

    async def test_가1_equals_starts_with_and_ends_with(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        equals = await searches.in_global(
            conditions=[OWN.name.filter.equals(_match("alpha", case_insensitive=True))]
        )
        starts = await searches.in_global(
            conditions=[OWN.name.filter.starts_with(_match("alpha", case_insensitive=True))]
        )
        starts_sensitive = await searches.in_global(
            conditions=[OWN.name.filter.starts_with(_match("alpha"))]
        )
        ends = await searches.in_global(conditions=[OWN.name.filter.ends_with(_match("beta"))])

        assert ids(equals) == seeded.shelf_ids("S1")
        assert ids(starts) == seeded.shelf_ids("S1", "S2")
        assert ids(starts_sensitive) == seeded.shelf_ids("S2")
        assert ids(ends) == seeded.shelf_ids("S2")

    async def test_가2_negation_inverts_the_same_match(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        matched = await searches.in_global(
            conditions=[OWN.name.filter.equals(_match("alpha", case_insensitive=True))]
        )
        negated = await searches.in_global(
            conditions=[
                OWN.name.filter.equals(_match("alpha", case_insensitive=True, negated=True))
            ]
        )

        assert ids(matched) == seeded.shelf_ids("S1")
        assert ids(negated) == seeded.shelf_ids("S2", "S3", "S4")

    async def test_가2_in_and_not_in(self, searches: ShelfSearches, seeded: Seeded) -> None:
        included = await searches.in_global(
            conditions=[
                OWN.name.filter.in_(
                    StringInMatchSpec(
                        values=["Alpha", "Gamma"], case_insensitive=False, negated=False
                    )
                )
            ]
        )
        excluded = await searches.in_global(
            conditions=[
                OWN.name.filter.in_(
                    StringInMatchSpec(
                        values=["Alpha", "Gamma"], case_insensitive=False, negated=True
                    )
                )
            ]
        )

        assert ids(included) == seeded.shelf_ids("S1", "S3")
        assert ids(excluded) == seeded.shelf_ids("S2", "S4")

    async def test_가3_negated_equality_drops_null_rows(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        """Fixed behavior: ``NOT (note = 'n')`` is unknown for a null note, so S1/S3/S4 fall out."""
        matched = await searches.in_global(conditions=[OWN.note.filter.equals(_match("n"))])
        negated = await searches.in_global(
            conditions=[OWN.note.filter.equals(_match("n", negated=True))]
        )

        assert ids(matched) == seeded.shelf_ids("S2")
        assert ids(negated) == set()


class TestNumberFilters:
    async def test_가4_integer_comparisons_at_the_boundary(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        equal = await searches.in_global(conditions=[OWN.count.filter.equals(5)])
        above = await searches.in_global(conditions=[OWN.count.filter.greater_than(5)])
        at_or_above = await searches.in_global(
            conditions=[OWN.count.filter.greater_than_or_equal(5)]
        )
        at_or_below = await searches.in_global(conditions=[OWN.count.filter.less_than_or_equal(5)])
        within = await searches.in_global(
            conditions=[
                OWN.count.filter.greater_than_or_equal(1),
                OWN.count.filter.less_than_or_equal(5),
            ]
        )

        assert ids(equal) == seeded.shelf_ids("S2", "S3")
        assert ids(above) == seeded.shelf_ids("S4")
        assert ids(at_or_above) == seeded.shelf_ids("S2", "S3", "S4")
        assert ids(at_or_below) == seeded.shelf_ids("S1", "S2", "S3")
        assert ids(within) == seeded.shelf_ids("S1", "S2", "S3")

    async def test_가4_decimal_comparisons_at_the_boundary(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        boundary = seeded.shelves["S2"].price
        at_or_above = await searches.in_global(
            conditions=[OWN.price.filter.greater_than_or_equal(boundary)]
        )
        above = await searches.in_global(conditions=[OWN.price.filter.greater_than(boundary)])
        within = await searches.in_global(
            conditions=[
                OWN.price.filter.greater_than_or_equal(Decimal("5.25")),
                OWN.price.filter.less_than_or_equal(Decimal("10.50")),
            ]
        )

        assert ids(at_or_above) == seeded.shelf_ids("S1", "S2", "S3")
        assert ids(above) == seeded.shelf_ids("S1", "S3")
        assert ids(within) == seeded.shelf_ids("S1", "S2", "S4")


class TestDateTimeFilters:
    async def test_가5_before_after_and_range_are_exclusive(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        after = await searches.in_global(conditions=[OWN.opened_at.filter.after(TIMES[1])])
        before = await searches.in_global(conditions=[OWN.opened_at.filter.before(TIMES[2])])
        within = await searches.in_global(
            conditions=[
                OWN.opened_at.filter.after(TIMES[0]),
                OWN.opened_at.filter.before(TIMES[3]),
            ]
        )

        assert ids(after) == seeded.shelf_ids("S3", "S4")
        assert ids(before) == seeded.shelf_ids("S1", "S2")
        assert ids(within) == seeded.shelf_ids("S2", "S3")

    async def test_가5_null_datetime_is_dropped_by_a_comparison(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        """Fixed behavior: a null ``closed_at`` satisfies neither bound; the null checks find it."""
        before = await searches.in_global(conditions=[OWN.closed_at.filter.before(TIMES[4])])
        missing = await searches.in_global(conditions=[OWN.closed_at.filter.is_null()])
        present = await searches.in_global(conditions=[OWN.closed_at.filter.is_not_null()])

        assert ids(before) == seeded.shelf_ids("S2")
        assert ids(missing) == seeded.shelf_ids("S1", "S4")
        assert ids(present) == seeded.shelf_ids("S2", "S3")

    async def test_가5_equality_matches_the_stored_instant(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        stored: datetime = seeded.shelves["S3"].opened_at
        result = await searches.in_global(conditions=[OWN.opened_at.filter.equals(stored)])

        assert ids(result) == seeded.shelf_ids("S3")


class TestDateFilters:
    async def test_가10_equality_and_its_negation(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        equal = await searches.in_global(conditions=[OWN.stocked_on.filter.equals(DATES[1])])
        unequal = await searches.in_global(conditions=[OWN.stocked_on.filter.not_equals(DATES[1])])

        assert ids(equal) == seeded.shelf_ids("S2")
        assert ids(unequal) == seeded.shelf_ids("S1", "S3", "S4")

    async def test_가10_before_and_after_exclude_the_bound(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        before = await searches.in_global(conditions=[OWN.stocked_on.filter.before(DATES[2])])
        after = await searches.in_global(conditions=[OWN.stocked_on.filter.after(DATES[1])])

        assert ids(before) == seeded.shelf_ids("S1", "S2")
        assert ids(after) == seeded.shelf_ids("S3", "S4")

    async def test_가10_on_or_before_and_on_or_after_include_the_bound(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        on_or_before = await searches.in_global(
            conditions=[OWN.stocked_on.filter.on_or_before(DATES[2])]
        )
        on_or_after = await searches.in_global(
            conditions=[OWN.stocked_on.filter.on_or_after(DATES[1])]
        )

        assert ids(on_or_before) == seeded.shelf_ids("S1", "S2", "S3")
        assert ids(on_or_after) == seeded.shelf_ids("S2", "S3", "S4")

    async def test_가10_range_filter_includes_both_bounds(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        adapter = BaseFilterAdapter()
        both = await searches.in_global(
            conditions=adapter.apply_date_range_filter(
                DateRangeFilter(after=DATES[1], before=DATES[2]), OWN.stocked_on.filter
            )
        )
        lower_only = await searches.in_global(
            conditions=adapter.apply_date_range_filter(
                DateRangeFilter(after=DATES[2]), OWN.stocked_on.filter
            )
        )
        upper_only = await searches.in_global(
            conditions=adapter.apply_date_range_filter(
                DateRangeFilter(before=DATES[1]), OWN.stocked_on.filter
            )
        )
        unbounded = await searches.in_global(
            conditions=adapter.apply_date_range_filter(DateRangeFilter(), OWN.stocked_on.filter)
        )

        assert ids(both) == seeded.shelf_ids("S2", "S3")
        assert ids(lower_only) == seeded.shelf_ids("S3", "S4")
        assert ids(upper_only) == seeded.shelf_ids("S1", "S2")
        assert ids(unbounded) == seeded.shelf_ids("S1", "S2", "S3", "S4")


class TestEnumBoolUUIDFilters:
    async def test_가6_enum_equality_and_membership(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        equal = await searches.in_global(conditions=[OWN.kind.filter.equals(ShelfKind.BOOK)])
        included = await searches.in_global(
            conditions=[OWN.kind.filter.in_([ShelfKind.TOOL, ShelfKind.TOY])]
        )
        excluded = await searches.in_global(conditions=[OWN.kind.filter.not_in([ShelfKind.BOOK])])

        assert ids(equal) == seeded.shelf_ids("S1", "S2")
        assert ids(included) == seeded.shelf_ids("S3", "S4")
        assert ids(excluded) == seeded.shelf_ids("S3", "S4")

    async def test_가7_boolean_equality(self, searches: ShelfSearches, seeded: Seeded) -> None:
        enabled = await searches.in_global(conditions=[OWN.active.filter.equals(True)])
        disabled = await searches.in_global(conditions=[OWN.active.filter.equals(False)])

        assert ids(enabled) == seeded.shelf_ids("S1", "S3")
        assert ids(disabled) == seeded.shelf_ids("S2", "S4")

    async def test_가8_uuid_equality_and_membership(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        equal = await searches.in_global(
            conditions=[
                OWN.id.filter.equals(UUIDEqualMatchSpec(value=seeded.shelf_id("S1"), negated=False))
            ]
        )
        included = await searches.in_global(
            conditions=[
                OWN.id.filter.in_(
                    UUIDInMatchSpec(
                        values=[seeded.shelf_id("S1"), seeded.shelf_id("S3")], negated=False
                    )
                )
            ]
        )

        assert ids(equal) == seeded.shelf_ids("S1")
        assert ids(included) == seeded.shelf_ids("S1", "S3")


class TestArrayFilters:
    async def test_가9_containment_and_overlap(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        contains = await searches.in_global(conditions=[OWN.tags.filter.contains("a")])
        contains_all = await searches.in_global(
            conditions=[OWN.tags.filter.contains_all(["a", "b"])]
        )
        overlaps = await searches.in_global(conditions=[OWN.tags.filter.contains_any(["a", "b"])])

        assert ids(contains) == seeded.shelf_ids("S1", "S4")
        assert ids(contains_all) == seeded.shelf_ids("S1")
        assert ids(overlaps) == seeded.shelf_ids("S1", "S2", "S4")

    async def test_가9_empty_argument_keeps_or_drops_every_row(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        """Fixed behavior: every array contains the empty one, and none overlaps it."""
        contains_all = await searches.in_global(conditions=[OWN.tags.filter.contains_all([])])
        overlaps = await searches.in_global(conditions=[OWN.tags.filter.contains_any([])])

        assert ids(contains_all) == seeded.shelf_ids("S1", "S2", "S3", "S4")
        assert ids(overlaps) == set()
