from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

import pytest
import sqlalchemy as sa

from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions

type Render = Callable[[sa.sql.ClauseElement], str]
type Operation = Callable[[DateTimeConditions, datetime], QueryCondition]

MOMENT = datetime(2026, 1, 1, tzinfo=UTC)


class TestDateTimeConditions:
    @pytest.mark.parametrize(
        ("operation", "expected"),
        [
            (DateTimeConditions.equals, "items.created_at = '2026-01-01 00:00:00+00:00'"),
            (DateTimeConditions.before, "items.created_at < '2026-01-01 00:00:00+00:00'"),
            (DateTimeConditions.after, "items.created_at > '2026-01-01 00:00:00+00:00'"),
        ],
    )
    def test_each_operation(
        self, items_table: sa.Table, render: Render, operation: Operation, expected: str
    ) -> None:
        condition = operation(DateTimeConditions(items_table.c.created_at), MOMENT)

        assert render(condition()) == expected
