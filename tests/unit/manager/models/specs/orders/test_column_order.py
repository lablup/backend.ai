from __future__ import annotations

from collections.abc import Callable

import pytest
import sqlalchemy as sa

from ai.backend.manager.models.specs.orders.column import ColumnOrder

type Render = Callable[[sa.sql.ClauseElement], str]


class TestColumnOrderApply:
    @pytest.mark.parametrize(
        ("ascending", "expected"),
        [
            (True, "items.name ASC"),
            (False, "items.name DESC"),
        ],
    )
    def test_orders_by_the_column(
        self, items_table: sa.Table, render: Render, ascending: bool, expected: str
    ) -> None:
        assert render(ColumnOrder(items_table.c.name).apply(ascending)) == expected

    @pytest.mark.parametrize(
        ("ascending", "direction"),
        [
            (True, "ASC"),
            (False, "DESC"),
        ],
    )
    def test_orders_by_a_scalar_subquery(
        self, items_table: sa.Table, render: Render, ascending: bool, direction: str
    ) -> None:
        owners = sa.Table(
            "owners", sa.MetaData(), sa.Column("id", sa.Uuid), sa.Column("email", sa.String)
        )
        owner_email = (
            sa.select(owners.c.email)
            .where(owners.c.id == items_table.c.id)
            .correlate(items_table)
            .scalar_subquery()
        )

        query = sa.select(items_table.c.id).order_by(ColumnOrder(owner_email).apply(ascending))

        assert render(query) == (
            "SELECT items.id FROM items ORDER BY "
            f"(SELECT owners.email FROM owners WHERE owners.id = items.id) {direction}"
        )
