from __future__ import annotations

from collections.abc import Callable

import pytest
import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringInMatchSpec, StringMatchSpec
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.conditions.string import (
    DelimitedStringConditions,
    StringConditions,
)

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


class TestDelimitedStringConditions:
    @pytest.mark.parametrize(
        ("case_insensitive", "negated", "expected"),
        [
            (False, False, "'Ab' = ANY (string_to_array(items.name, ','))"),
            (True, False, "'ab' = ANY (string_to_array(lower(items.name), ','))"),
            (False, True, "NOT ('Ab' = ANY (string_to_array(items.name, ',')))"),
            (True, True, "NOT ('ab' = ANY (string_to_array(lower(items.name), ',')))"),
        ],
    )
    def test_equals_matches_one_element(
        self,
        items_table: sa.Table,
        render: Render,
        case_insensitive: bool,
        negated: bool,
        expected: str,
    ) -> None:
        condition = DelimitedStringConditions(items_table.c.name).equals(
            StringMatchSpec("Ab", case_insensitive=case_insensitive, negated=negated)
        )

        assert render(condition()) == expected

    @pytest.mark.parametrize(
        ("case_insensitive", "negated", "expected"),
        [
            (False, False, "string_to_array(items.name, ',') && CAST(ARRAY['Ab', 'c'] AS TEXT[])"),
            (
                True,
                False,
                "string_to_array(lower(items.name), ',') && CAST(ARRAY['ab', 'c'] AS TEXT[])",
            ),
            (
                False,
                True,
                "NOT (string_to_array(items.name, ',') && CAST(ARRAY['Ab', 'c'] AS TEXT[]))",
            ),
            (
                True,
                True,
                "NOT (string_to_array(lower(items.name), ',') && CAST(ARRAY['ab', 'c'] AS TEXT[]))",
            ),
        ],
    )
    def test_in_matches_any_element(
        self,
        items_table: sa.Table,
        render: Render,
        case_insensitive: bool,
        negated: bool,
        expected: str,
    ) -> None:
        condition = DelimitedStringConditions(items_table.c.name).in_(
            StringInMatchSpec(
                values=["Ab", "c"], case_insensitive=case_insensitive, negated=negated
            )
        )

        assert render(condition()) == expected

    def test_custom_delimiter(self, items_table: sa.Table, render: Render) -> None:
        condition = DelimitedStringConditions(items_table.c.name, delimiter=";").equals(
            StringMatchSpec("Ab", case_insensitive=False, negated=False)
        )

        assert render(condition()) == "'Ab' = ANY (string_to_array(items.name, ';'))"

    def test_contains_runs_on_whole_column(self, items_table: sa.Table, render: Render) -> None:
        condition = DelimitedStringConditions(items_table.c.name).contains(
            StringMatchSpec("Ab", case_insensitive=True, negated=False)
        )

        assert render(condition()) == "items.name ILIKE '%%Ab%%'"
