"""Unit tests for ``BaseFilterAdapter.convert_and / convert_or / convert_not``.

Each helper takes pre-converted ``list[list[QueryCondition]]`` so adapters
keep ownership of per-field conversion. The tests exercise the boolean-clause
grouping (notably the ``(A AND B) OR (C AND D)`` shape) by feeding sentinel
``QueryCondition`` callables and compiling the produced SQL — a regression
that flattens a sub-filter group would surface here as a different SQL tree.
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa

from ai.backend.manager.api.rest.adapter import BaseFilterAdapter
from ai.backend.manager.repositories.base import QueryCondition


def _const(label: str) -> QueryCondition:
    """A ``QueryCondition`` whose compiled SQL is the literal ``'label'``."""

    def _inner() -> Any:
        return sa.literal_column(f"'{label}'")

    return _inner


def _compile(qc: QueryCondition) -> str:
    return str(qc().compile(compile_kwargs={"literal_binds": True}))


class _Adapter(BaseFilterAdapter):
    pass


class TestConvertAnd:
    def test_empty_input_returns_empty(self) -> None:
        assert _Adapter().convert_and([]) == []

    def test_single_sub_with_single_condition_passes_through(self) -> None:
        result = _Adapter().convert_and([[_const("A")]])
        assert [_compile(c) for c in result] == ["'A'"]

    def test_multiple_subs_flatten_in_order(self) -> None:
        """AND sub-conditions append individually; ``BatchQuerier`` AND-combines them downstream."""
        result = _Adapter().convert_and([[_const("A"), _const("B")], [_const("C")]])
        assert [_compile(c) for c in result] == ["'A'", "'B'", "'C'"]

    def test_empty_sub_lists_are_skipped_implicitly(self) -> None:
        result = _Adapter().convert_and([[], [_const("A")], []])
        assert [_compile(c) for c in result] == ["'A'"]


class TestConvertOr:
    def test_empty_input_returns_empty(self) -> None:
        assert _Adapter().convert_or([]) == []

    def test_all_empty_sub_lists_returns_empty(self) -> None:
        assert _Adapter().convert_or([[], [], []]) == []

    def test_single_sub_with_single_condition_yields_a_one_term_or(self) -> None:
        """A single non-empty sub still goes through the AND-then-OR pipeline."""
        result = _Adapter().convert_or([[_const("A")]])
        assert len(result) == 1
        assert _compile(result[0]) == "'A'"

    def test_multi_field_subs_preserve_internal_and_grouping(self) -> None:
        """``[(A, B), (C, D)]`` must compile to ``A AND B OR C AND D`` (AND binds tighter than OR).

        Regression guard for BA-5975: a flat OR over all sub-conditions would
        compile to ``A OR B OR C OR D`` and silently widen the result set.
        SQLAlchemy elides redundant parentheses, so the textual form has none —
        but the operator counts pin the structure.
        """
        result = _Adapter().convert_or([
            [_const("A"), _const("B")],
            [_const("C"), _const("D")],
        ])
        assert len(result) == 1
        sql = _compile(result[0])
        assert sql == "'A' AND 'B' OR 'C' AND 'D'"
        # The bug would drop both AND operators in favor of a flat OR.
        assert sql.count(" AND ") == 2
        assert sql.count(" OR ") == 1

    def test_empty_sub_lists_are_dropped_from_grouping(self) -> None:
        result = _Adapter().convert_or([[], [_const("A"), _const("B")], []])
        assert len(result) == 1
        assert _compile(result[0]) == "'A' AND 'B'"


class TestConvertNot:
    def test_empty_input_returns_empty(self) -> None:
        assert _Adapter().convert_not([]) == []

    def test_each_sub_is_negated_independently(self) -> None:
        """``NOT [{A, B}, {C}]`` produces ``NOT (A AND B)`` and ``NOT C`` as separate clauses."""
        result = _Adapter().convert_not([[_const("A"), _const("B")], [_const("C")]])
        assert len(result) == 2
        assert _compile(result[0]) == "NOT ('A' AND 'B')"
        assert _compile(result[1]) == "NOT 'C'"

    def test_empty_sub_lists_are_skipped(self) -> None:
        result = _Adapter().convert_not([[], [_const("A")], []])
        assert len(result) == 1
        assert _compile(result[0]) == "NOT 'A'"
