from __future__ import annotations

import enum
from collections.abc import Callable

import pytest
import sqlalchemy as sa

from ai.backend.manager.models.specs.conditions.enum import EnumConditions

type Render = Callable[[sa.sql.ClauseElement], str]


class ItemStatusField(enum.StrEnum):
    """A request-side enum, distinct from the column's."""

    ACTIVE = "active"
    DELETED = "deleted"


class TestEnumConditions:
    def test_equals(
        self, items_table: sa.Table, item_status_type: type[enum.StrEnum], render: Render
    ) -> None:
        conditions = EnumConditions(items_table.c.status, item_status_type)

        condition = conditions.equals(item_status_type("active"))

        assert condition is not None
        assert render(condition()) == "items.status = 'ACTIVE'"

    def test_not_equals(
        self, items_table: sa.Table, item_status_type: type[enum.StrEnum], render: Render
    ) -> None:
        conditions = EnumConditions(items_table.c.status, item_status_type)

        condition = conditions.not_equals(item_status_type("active"))

        assert condition is not None
        assert render(condition()) == "items.status != 'ACTIVE'"

    def test_in(
        self, items_table: sa.Table, item_status_type: type[enum.StrEnum], render: Render
    ) -> None:
        conditions = EnumConditions(items_table.c.status, item_status_type)

        condition = conditions.in_([item_status_type("active"), item_status_type("deleted")])

        assert condition is not None
        assert render(condition()) == "items.status IN ('ACTIVE', 'DELETED')"

    def test_not_in(
        self, items_table: sa.Table, item_status_type: type[enum.StrEnum], render: Render
    ) -> None:
        conditions = EnumConditions(items_table.c.status, item_status_type)

        condition = conditions.not_in([item_status_type("deleted")])

        assert condition is not None
        assert render(condition()) == "(items.status NOT IN ('DELETED'))"

    def test_none_gives_no_condition(
        self, items_table: sa.Table, item_status_type: type[enum.StrEnum]
    ) -> None:
        conditions = EnumConditions(items_table.c.status, item_status_type)

        assert [
            conditions.equals(None),
            conditions.not_equals(None),
            conditions.in_(None),
            conditions.not_in(None),
        ] == [None, None, None, None]


class TestEnumConditionsToValue:
    def test_request_member_becomes_column_member(
        self, items_table: sa.Table, item_status_type: type[enum.StrEnum]
    ) -> None:
        conditions = EnumConditions(items_table.c.status, item_status_type)

        assert conditions.to_value(ItemStatusField.DELETED) is item_status_type("deleted")

    def test_request_members_become_column_members(
        self, items_table: sa.Table, item_status_type: type[enum.StrEnum]
    ) -> None:
        conditions = EnumConditions(items_table.c.status, item_status_type)

        assert conditions.to_values([ItemStatusField.ACTIVE, ItemStatusField.DELETED]) == [
            item_status_type("active"),
            item_status_type("deleted"),
        ]

    def test_none_stays_none(
        self, items_table: sa.Table, item_status_type: type[enum.StrEnum]
    ) -> None:
        conditions = EnumConditions(items_table.c.status, item_status_type)

        assert (conditions.to_value(None), conditions.to_values(None)) == (None, None)

    def test_unknown_value_is_rejected(
        self, items_table: sa.Table, item_status_type: type[enum.StrEnum]
    ) -> None:
        conditions = EnumConditions(items_table.c.status, item_status_type)

        with pytest.raises(ValueError):
            conditions.to_value("missing")
