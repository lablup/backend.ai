"""Scenarios 다·라·마: conditions on the rows a shelf reaches, one and two levels out."""

from __future__ import annotations

import uuid

import pytest
import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.errors.repository import EmptyMatchConditionError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from .shelf_fields import BoxSearchableFields, ShelfSearchableFields
from .shelf_fixtures import Seeded
from .shelf_rows import BoxRow, BoxState
from .shelf_search import ShelfSearches, ids, negate, spec_graded

BOXES = ShelfSearchableFields.nested.boxes
CATEGORY = ShelfSearchableFields.nested.category
BOX = BoxSearchableFields.own
SPEC = BoxSearchableFields.nested.spec
ITEMS = BoxSearchableFields.nested.items


class TestOneLevelNesting:
    async def test_다1_some_binds_every_condition_to_one_child(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        """S1 meets both conditions, but on different boxes, so it is out."""
        result = await searches.in_global(
            conditions=[
                BOXES.correlation.some([
                    BOX.size.filter.equals(9),
                    BOX.state.filter.equals(BoxState.OPEN),
                ])
            ]
        )

        assert ids(result) == seeded.shelf_ids("S2")

    async def test_다2_separate_quantifiers_may_be_met_by_different_children(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        result = await searches.in_global(
            conditions=[
                BOXES.correlation.some([BOX.size.filter.equals(9)]),
                BOXES.correlation.some([BOX.state.filter.equals(BoxState.OPEN)]),
            ]
        )

        assert ids(result) == seeded.shelf_ids("S1", "S2")

    async def test_다3_every_holds_for_a_shelf_with_no_child(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        result = await searches.in_global(
            conditions=[BOXES.correlation.every([BOX.state.filter.equals(BoxState.OPEN)])]
        )

        assert ids(result) == seeded.shelf_ids("S2", "S3", "S4")

    async def test_다4_none_excludes_only_the_shelf_holding_a_matching_child(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        result = await searches.in_global(
            conditions=[BOXES.correlation.none([BOX.state.filter.equals(BoxState.CLOSED)])]
        )

        assert ids(result) == seeded.shelf_ids("S2", "S3", "S4")

    async def test_다5_some_and_none_are_two_conditions_and_ed(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        result = await searches.in_global(
            conditions=[
                BOXES.correlation.some([BOX.size.filter.equals(9)]),
                BOXES.correlation.none([BOX.state.filter.equals(BoxState.CLOSED)]),
            ]
        )

        assert ids(result) == seeded.shelf_ids("S2")

    async def test_다6_existence_is_asked_by_name(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        present = await searches.in_global(conditions=[BOXES.correlation.exists()])
        absent = await searches.in_global(conditions=[BOXES.correlation.not_exists()])

        assert ids(present) == seeded.shelf_ids("S1", "S2", "S4")
        assert ids(absent) == seeded.shelf_ids("S3")

    @pytest.mark.parametrize("mode", ["some", "every", "none"])
    async def test_다6_a_matching_mode_with_no_condition_is_refused(self, mode: str) -> None:
        """A mode that constrains nothing was answering "has a child" instead."""
        with pytest.raises(EmptyMatchConditionError):
            getattr(BOXES.correlation, mode)([])


class TestToOneNesting:
    async def test_라1_has_matches_through_the_related_row(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        result = await searches.in_global(
            conditions=[
                CATEGORY.correlation.has([
                    CATEGORY.fields.title.filter.contains(
                        StringMatchSpec(value="Prim", case_insensitive=False, negated=False)
                    )
                ])
            ]
        )

        assert ids(result) == seeded.shelf_ids("S1")

    async def test_라2_a_shelf_with_no_related_row_is_absent_from_exists(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        result = await searches.in_global(conditions=[CATEGORY.correlation.exists()])

        assert ids(result) == seeded.shelf_ids("S1", "S2")

    async def test_라2_has_with_no_condition_is_refused(self) -> None:
        with pytest.raises(EmptyMatchConditionError):
            CATEGORY.correlation.has([])

    async def test_라3_negating_has_keeps_the_shelves_with_no_related_row(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        """Fixed behavior: the negation is ``NOT EXISTS``, so a missing category passes."""
        result = await searches.in_global(
            conditions=[
                negate(
                    CATEGORY.correlation.has([
                        CATEGORY.fields.title.filter.contains(
                            StringMatchSpec(value="Prim", case_insensitive=False, negated=False)
                        )
                    ])
                )
            ]
        )

        assert ids(result) == seeded.shelf_ids("S2", "S3", "S4")


class TestTwoLevelNesting:
    async def test_마1_the_child_and_its_own_related_row_bind_together(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        result = await searches.in_global(
            conditions=[BOXES.correlation.some([BOX.size.filter.equals(9), spec_graded("y")])]
        )

        assert ids(result) == seeded.shelf_ids("S1", "S2")

    async def test_마2_the_condition_does_not_leak_to_another_childs_related_row(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        """S1's open box points at grade ``x``; its grade ``y`` spec belongs to another box."""
        result = await searches.in_global(
            conditions=[
                BOXES.correlation.some([BOX.state.filter.equals(BoxState.OPEN), spec_graded("y")])
            ]
        )

        assert ids(result) == seeded.shelf_ids("S2")

    async def test_마3_a_child_with_no_related_row_is_found_only_by_the_negation(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        present = await searches.in_global(
            conditions=[BOXES.correlation.some([SPEC.correlation.exists()])]
        )
        absent = await searches.in_global(
            conditions=[BOXES.correlation.some([negate(SPEC.correlation.exists())])]
        )

        assert ids(present) == seeded.shelf_ids("S1", "S2")
        assert ids(absent) == seeded.shelf_ids("S4")

    async def test_마4_the_second_level_joins_on_the_predicate_alone(
        self, searches: ShelfSearches, shelf_db: ExtendedAsyncSAEngine, seeded: Seeded
    ) -> None:
        """No foreign key backs ``box.spec_id``; a value naming no row simply matches nothing."""
        async with shelf_db.begin_session() as sess:
            await sess.execute(
                sa.update(BoxRow)
                .where(BoxRow.id == seeded.boxes["B4"])
                .values(spec_id=uuid.uuid4())
            )

        present = await searches.in_global(
            conditions=[BOXES.correlation.some([SPEC.correlation.exists()])]
        )
        absent = await searches.in_global(
            conditions=[BOXES.correlation.some([negate(SPEC.correlation.exists())])]
        )

        assert ids(present) == seeded.shelf_ids("S1", "S2")
        assert ids(absent) == seeded.shelf_ids("S4")

    async def test_마5_a_to_many_inside_a_to_many_runs(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        """Allowed by the shared implementation; the entity declarations avoid it by rule."""
        result = await searches.in_global(
            conditions=[
                BOXES.correlation.some([
                    ITEMS.correlation.some([ITEMS.fields.qty.filter.greater_than(1)])
                ])
            ]
        )

        assert ids(result) == seeded.shelf_ids("S2")

    async def test_마6_the_second_level_is_evaluated_per_outer_row(
        self, searches: ShelfSearches, seeded: Seeded
    ) -> None:
        """No box of size 1 points at a grade ``y`` spec, so nothing matches."""
        result = await searches.in_global(
            conditions=[BOXES.correlation.some([BOX.size.filter.equals(1), spec_graded("y")])]
        )

        assert ids(result) == set()
