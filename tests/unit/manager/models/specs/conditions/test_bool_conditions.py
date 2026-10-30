from __future__ import annotations

from collections.abc import Callable

import pytest
import sqlalchemy as sa

from ai.backend.manager.models.specs.conditions.boolean import BoolConditions

type Render = Callable[[sa.sql.ClauseElement], str]


class TestBoolConditions:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (True, "items.flag = true"),
            (False, "items.flag = false"),
        ],
    )
    def test_equals(
        self, items_table: sa.Table, render: Render, value: bool, expected: str
    ) -> None:
        condition = BoolConditions(items_table.c.flag).equals(value)

        assert render(condition()) == expected
