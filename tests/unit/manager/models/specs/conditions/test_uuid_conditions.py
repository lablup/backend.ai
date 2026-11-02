from __future__ import annotations

import uuid
from collections.abc import Callable

import pytest
import sqlalchemy as sa

from ai.backend.common.data.filter_specs import UUIDEqualMatchSpec, UUIDInMatchSpec
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions

type Render = Callable[[sa.sql.ClauseElement], str]

FIRST_ID = uuid.UUID(int=1)
SECOND_ID = uuid.UUID(int=2)


class TestUUIDConditionsEquals:
    @pytest.mark.parametrize(
        ("negated", "expected"),
        [
            (False, f"items.id = '{FIRST_ID}'"),
            (True, f"items.id != '{FIRST_ID}'"),
        ],
    )
    def test_equality(
        self, items_table: sa.Table, render: Render, negated: bool, expected: str
    ) -> None:
        condition = UUIDConditions(items_table.c.id).equals(
            UUIDEqualMatchSpec(value=FIRST_ID, negated=negated)
        )

        assert render(condition()) == expected


class TestUUIDConditionsIn:
    @pytest.mark.parametrize(
        ("negated", "expected"),
        [
            (False, f"items.id IN ('{FIRST_ID}', '{SECOND_ID}')"),
            (True, f"(items.id NOT IN ('{FIRST_ID}', '{SECOND_ID}'))"),
        ],
    )
    def test_membership(
        self, items_table: sa.Table, render: Render, negated: bool, expected: str
    ) -> None:
        condition = UUIDConditions(items_table.c.id).in_(
            UUIDInMatchSpec(values=[FIRST_ID, SECOND_ID], negated=negated)
        )

        assert render(condition()) == expected
