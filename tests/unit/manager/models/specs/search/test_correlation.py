from __future__ import annotations

from collections.abc import Callable

import pytest
import sqlalchemy as sa

from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation, ToOneCorrelation

type Render = Callable[[sa.sql.ClauseElement], str]


@pytest.fixture
def to_many(items_table: sa.Table, tags_table: sa.Table) -> ToManyCorrelation:
    return ToManyCorrelation(tags_table, items_table, tags_table.c.item_id == items_table.c.id)


@pytest.fixture
def to_one(items_table: sa.Table, tags_table: sa.Table) -> ToOneCorrelation:
    return ToOneCorrelation(tags_table, items_table, tags_table.c.item_id == items_table.c.id)


@pytest.fixture
def key_is_a(tags_table: sa.Table) -> QueryCondition:
    return lambda: tags_table.c.key == "a"


@pytest.fixture
def key_is_not_b(tags_table: sa.Table) -> QueryCondition:
    return lambda: tags_table.c.key != "b"


class TestToManyCorrelation:
    def test_some_puts_every_condition_on_one_row(
        self,
        items_table: sa.Table,
        to_many: ToManyCorrelation,
        key_is_a: QueryCondition,
        key_is_not_b: QueryCondition,
        render: Render,
    ) -> None:
        condition = to_many.some([key_is_a, key_is_not_b])

        assert render(sa.select(items_table.c.id).where(condition())) == (
            "SELECT items.id FROM items WHERE EXISTS (SELECT 1 AS anon_1 FROM tags "
            "WHERE tags.item_id = items.id AND tags.key = 'a' AND tags.key != 'b')"
        )

    def test_none_negates_some(
        self,
        items_table: sa.Table,
        to_many: ToManyCorrelation,
        key_is_a: QueryCondition,
        render: Render,
    ) -> None:
        condition = to_many.none([key_is_a])

        assert render(sa.select(items_table.c.id).where(condition())) == (
            "SELECT items.id FROM items WHERE NOT (EXISTS (SELECT 1 AS anon_1 FROM tags "
            "WHERE tags.item_id = items.id AND tags.key = 'a'))"
        )

    def test_every_is_no_row_failing_one_condition(
        self,
        items_table: sa.Table,
        to_many: ToManyCorrelation,
        key_is_a: QueryCondition,
        render: Render,
    ) -> None:
        condition = to_many.every([key_is_a])

        assert render(sa.select(items_table.c.id).where(condition())) == (
            "SELECT items.id FROM items WHERE NOT (EXISTS (SELECT 1 AS anon_1 FROM tags "
            "WHERE tags.item_id = items.id AND tags.key != 'a'))"
        )

    def test_every_is_no_row_failing_all_conditions(
        self,
        items_table: sa.Table,
        to_many: ToManyCorrelation,
        key_is_a: QueryCondition,
        key_is_not_b: QueryCondition,
        render: Render,
    ) -> None:
        condition = to_many.every([key_is_a, key_is_not_b])

        assert render(sa.select(items_table.c.id).where(condition())) == (
            "SELECT items.id FROM items WHERE NOT (EXISTS (SELECT 1 AS anon_1 FROM tags "
            "WHERE tags.item_id = items.id AND NOT (tags.key = 'a' AND tags.key != 'b')))"
        )


class TestToOneCorrelation:
    def test_has_puts_every_condition_on_the_related_row(
        self,
        items_table: sa.Table,
        to_one: ToOneCorrelation,
        key_is_a: QueryCondition,
        key_is_not_b: QueryCondition,
        render: Render,
    ) -> None:
        condition = to_one.has([key_is_a, key_is_not_b])

        assert render(sa.select(items_table.c.id).where(condition())) == (
            "SELECT items.id FROM items WHERE EXISTS (SELECT 1 AS anon_1 FROM tags "
            "WHERE tags.item_id = items.id AND tags.key = 'a' AND tags.key != 'b')"
        )

    @pytest.mark.parametrize(("ascending", "direction"), [(True, "ASC"), (False, "DESC")])
    def test_order_reads_the_related_column(
        self,
        items_table: sa.Table,
        tags_table: sa.Table,
        to_one: ToOneCorrelation,
        render: Render,
        ascending: bool,
        direction: str,
    ) -> None:
        order = to_one.order(tags_table.c.key).apply(ascending)

        assert render(sa.select(items_table.c.id).order_by(order)) == (
            "SELECT items.id FROM items ORDER BY "
            f"(SELECT tags.key FROM tags WHERE tags.item_id = items.id) {direction}"
        )
