from __future__ import annotations

from collections.abc import Callable

import pytest
import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringInMatchSpec, StringMatchSpec
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.conditions.string import StringConditions

type Render = Callable[[sa.sql.ClauseElement], str]
type Operation = Callable[[StringConditions, StringMatchSpec], QueryCondition]


class TestStringConditionsMatch:
    @pytest.mark.parametrize(
        ("operation", "case_insensitive", "negated", "expected"),
        [
            (StringConditions.equals, False, False, "items.name = 'Ab'"),
            (StringConditions.equals, True, False, "lower(items.name) = 'ab'"),
            (StringConditions.equals, False, True, "items.name != 'Ab'"),
            (StringConditions.equals, True, True, "lower(items.name) != 'ab'"),
            (StringConditions.contains, False, False, "items.name LIKE '%%Ab%%'"),
            (StringConditions.contains, True, False, "items.name ILIKE '%%Ab%%'"),
            (StringConditions.contains, False, True, "items.name NOT LIKE '%%Ab%%'"),
            (StringConditions.contains, True, True, "items.name NOT ILIKE '%%Ab%%'"),
            (StringConditions.starts_with, False, False, "items.name LIKE 'Ab%%'"),
            (StringConditions.starts_with, True, False, "items.name ILIKE 'Ab%%'"),
            (StringConditions.starts_with, False, True, "items.name NOT LIKE 'Ab%%'"),
            (StringConditions.starts_with, True, True, "items.name NOT ILIKE 'Ab%%'"),
            (StringConditions.ends_with, False, False, "items.name LIKE '%%Ab'"),
            (StringConditions.ends_with, True, False, "items.name ILIKE '%%Ab'"),
            (StringConditions.ends_with, False, True, "items.name NOT LIKE '%%Ab'"),
            (StringConditions.ends_with, True, True, "items.name NOT ILIKE '%%Ab'"),
        ],
    )
    def test_each_operation(
        self,
        items_table: sa.Table,
        render: Render,
        operation: Operation,
        case_insensitive: bool,
        negated: bool,
        expected: str,
    ) -> None:
        conditions = StringConditions(items_table.c.name)
        spec = StringMatchSpec("Ab", case_insensitive=case_insensitive, negated=negated)

        assert render(operation(conditions, spec)()) == expected


class TestStringConditionsIn:
    @pytest.mark.parametrize(
        ("case_insensitive", "negated", "expected"),
        [
            (False, False, "items.name IN ('Ab', 'c')"),
            (False, True, "(items.name NOT IN ('Ab', 'c'))"),
            (True, False, "lower(items.name) IN ('ab', 'c')"),
            (True, True, "(lower(items.name) NOT IN ('ab', 'c'))"),
        ],
    )
    def test_membership(
        self,
        items_table: sa.Table,
        render: Render,
        case_insensitive: bool,
        negated: bool,
        expected: str,
    ) -> None:
        condition = StringConditions(items_table.c.name).in_(
            StringInMatchSpec(
                values=["Ab", "c"], case_insensitive=case_insensitive, negated=negated
            )
        )

        assert render(condition()) == expected
