from __future__ import annotations

from collections.abc import Callable

import sqlalchemy as sa

from ai.backend.manager.models.specs.orders.condition import ConditionOrder

type Render = Callable[[sa.sql.ClauseElement], str]


class TestConditionOrder:
    def test_first_puts_matching_rows_ahead(self, items_table: sa.Table, render: Render) -> None:
        order = ConditionOrder(lambda: items_table.c.flag.is_(True))

        assert render(order.first()) == "items.flag IS true DESC"

    def test_last_puts_matching_rows_behind(self, items_table: sa.Table, render: Render) -> None:
        order = ConditionOrder(lambda: items_table.c.flag.is_(True))

        assert render(order.last()) == "items.flag IS true ASC"
