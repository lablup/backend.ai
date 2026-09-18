from __future__ import annotations

from collections.abc import Callable

import pytest
import sqlalchemy as sa

from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.conditions.integer import IntConditions

type Render = Callable[[sa.sql.ClauseElement], str]
type Operation = Callable[[IntConditions, int | None], QueryCondition | None]


class TestIntConditions:
    @pytest.mark.parametrize(
        ("operation", "expected"),
        [
            (IntConditions.equals, "items.count = 3"),
            (IntConditions.not_equals, "items.count != 3"),
            (IntConditions.greater_than, "items.count > 3"),
            (IntConditions.greater_than_or_equal, "items.count >= 3"),
            (IntConditions.less_than, "items.count < 3"),
            (IntConditions.less_than_or_equal, "items.count <= 3"),
        ],
    )
    def test_each_operation(
        self, items_table: sa.Table, render: Render, operation: Operation, expected: str
    ) -> None:
        condition = operation(IntConditions(items_table.c.count), 3)

        assert condition is not None
        assert render(condition()) == expected

    def test_zero_is_a_value(self, items_table: sa.Table, render: Render) -> None:
        condition = IntConditions(items_table.c.count).equals(0)

        assert condition is not None
        assert render(condition()) == "items.count = 0"

    @pytest.mark.parametrize(
        "operation",
        [
            IntConditions.equals,
            IntConditions.not_equals,
            IntConditions.greater_than,
            IntConditions.greater_than_or_equal,
            IntConditions.less_than,
            IntConditions.less_than_or_equal,
        ],
    )
    def test_none_gives_no_condition(self, items_table: sa.Table, operation: Operation) -> None:
        assert operation(IntConditions(items_table.c.count), None) is None
