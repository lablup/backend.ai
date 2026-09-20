from __future__ import annotations

from collections.abc import Callable

import sqlalchemy as sa

from ai.backend.manager.models.specs.conditions.array import ArrayConditions

type Render = Callable[[sa.sql.ClauseElement], str]


class TestArrayConditions:
    def test_contains_asks_for_one_value(self, items_table: sa.Table, render: Render) -> None:
        conditions = ArrayConditions[int](items_table.c.gids, sa.Integer())

        assert render(conditions.contains(1000)()) == (
            "items.gids @> CAST(ARRAY[1000] AS INTEGER[])"
        )

    def test_contains_all_asks_for_every_value(self, items_table: sa.Table, render: Render) -> None:
        conditions = ArrayConditions[int](items_table.c.gids, sa.Integer())

        assert render(conditions.contains_all([1000, 1001])()) == (
            "items.gids @> CAST(ARRAY[1000, 1001] AS INTEGER[])"
        )

    def test_contains_any_asks_for_an_overlap(self, items_table: sa.Table, render: Render) -> None:
        conditions = ArrayConditions[int](items_table.c.gids, sa.Integer())

        assert render(conditions.contains_any([1000, 1001])()) == (
            "items.gids && CAST(ARRAY[1000, 1001] AS INTEGER[])"
        )
