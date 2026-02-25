"""Regression tests for StringMatchSpec support in fair share condition methods.

Verifies that negated and case_insensitive flags are correctly applied
to generated SQL conditions (BA-4633).
"""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.manager.api.gql.base import StringMatchSpec
from ai.backend.manager.repositories.fair_share.options import (
    DomainFairShareConditions,
    ProjectFairShareConditions,
    UserFairShareConditions,
)


def _compile_sql(expr: sa.sql.expression.ColumnElement[bool]) -> str:
    """Compile a SQLAlchemy expression to a string for assertion.

    Uses the default dialect which compiles ilike as lower(...) LIKE lower(...).
    """
    return str(expr.compile(compile_kwargs={"literal_binds": True}))


class TestDomainFairShareConditionsStringMatchSpec:
    """Regression tests for DomainFairShareConditions with StringMatchSpec."""

    def test_contains_default(self) -> None:
        spec = StringMatchSpec(value="x", case_insensitive=False, negated=False)
        sql = _compile_sql(DomainFairShareConditions.by_resource_group_contains(spec)())
        assert "LIKE" in sql
        assert "lower" not in sql
        assert "NOT" not in sql

    def test_contains_case_insensitive(self) -> None:
        spec = StringMatchSpec(value="x", case_insensitive=True, negated=False)
        sql = _compile_sql(DomainFairShareConditions.by_resource_group_contains(spec)())
        # Default dialect compiles ilike as lower(...) LIKE lower(...)
        assert "lower" in sql
        assert "NOT" not in sql

    def test_contains_negated(self) -> None:
        spec = StringMatchSpec(value="x", case_insensitive=False, negated=True)
        sql = _compile_sql(DomainFairShareConditions.by_resource_group_contains(spec)())
        assert "NOT" in sql
        assert "LIKE" in sql

    def test_contains_case_insensitive_negated(self) -> None:
        spec = StringMatchSpec(value="x", case_insensitive=True, negated=True)
        sql = _compile_sql(DomainFairShareConditions.by_resource_group_contains(spec)())
        assert "NOT" in sql
        # Default dialect compiles ilike as lower(...) LIKE lower(...)
        assert "lower" in sql

    def test_equals_default(self) -> None:
        spec = StringMatchSpec(value="x", case_insensitive=False, negated=False)
        sql = _compile_sql(DomainFairShareConditions.by_domain_name_equals(spec)())
        assert "lower" not in sql
        assert "NOT" not in sql

    def test_equals_case_insensitive(self) -> None:
        spec = StringMatchSpec(value="X", case_insensitive=True, negated=False)
        sql = _compile_sql(DomainFairShareConditions.by_domain_name_equals(spec)())
        assert "lower" in sql

    def test_equals_negated(self) -> None:
        spec = StringMatchSpec(value="x", case_insensitive=False, negated=True)
        sql = _compile_sql(DomainFairShareConditions.by_domain_name_equals(spec)())
        assert "!=" in sql

    def test_starts_with_case_insensitive(self) -> None:
        spec = StringMatchSpec(value="x", case_insensitive=True, negated=False)
        sql = _compile_sql(DomainFairShareConditions.by_resource_group_starts_with(spec)())
        # Default dialect compiles ilike as lower(...) LIKE lower(...)
        assert "lower" in sql

    def test_ends_with_negated(self) -> None:
        spec = StringMatchSpec(value="x", case_insensitive=False, negated=True)
        sql = _compile_sql(DomainFairShareConditions.by_domain_name_ends_with(spec)())
        assert "NOT" in sql


class TestProjectFairShareConditionsStringMatchSpec:
    """Regression tests for ProjectFairShareConditions with StringMatchSpec."""

    def test_resource_group_contains_case_insensitive(self) -> None:
        spec = StringMatchSpec(value="rg", case_insensitive=True, negated=False)
        sql = _compile_sql(ProjectFairShareConditions.by_resource_group_contains(spec)())
        # Default dialect compiles ilike as lower(...) LIKE lower(...)
        assert "lower" in sql

    def test_resource_group_contains_negated(self) -> None:
        spec = StringMatchSpec(value="rg", case_insensitive=False, negated=True)
        sql = _compile_sql(ProjectFairShareConditions.by_resource_group_contains(spec)())
        assert "NOT" in sql

    def test_domain_name_equals_case_insensitive_negated(self) -> None:
        spec = StringMatchSpec(value="Dom", case_insensitive=True, negated=True)
        sql = _compile_sql(ProjectFairShareConditions.by_domain_name_equals(spec)())
        assert "!=" in sql
        assert "lower" in sql

    def test_project_name_contains_case_insensitive(self) -> None:
        spec = StringMatchSpec(value="proj", case_insensitive=True, negated=False)
        sql = _compile_sql(ProjectFairShareConditions.by_project_name_contains(spec)())
        # Default dialect compiles ilike as lower(...) LIKE lower(...)
        assert "lower" in sql

    def test_project_name_starts_with_negated(self) -> None:
        spec = StringMatchSpec(value="proj", case_insensitive=False, negated=True)
        sql = _compile_sql(ProjectFairShareConditions.by_project_name_starts_with(spec)())
        assert "NOT" in sql


class TestUserFairShareConditionsStringMatchSpec:
    """Regression tests for UserFairShareConditions with StringMatchSpec."""

    def test_resource_group_ends_with_case_insensitive(self) -> None:
        spec = StringMatchSpec(value="rg", case_insensitive=True, negated=False)
        sql = _compile_sql(UserFairShareConditions.by_resource_group_ends_with(spec)())
        # Default dialect compiles ilike as lower(...) LIKE lower(...)
        assert "lower" in sql

    def test_domain_name_starts_with_negated(self) -> None:
        spec = StringMatchSpec(value="dom", case_insensitive=False, negated=True)
        sql = _compile_sql(UserFairShareConditions.by_domain_name_starts_with(spec)())
        assert "NOT" in sql

    def test_username_contains_case_insensitive_negated(self) -> None:
        spec = StringMatchSpec(value="admin", case_insensitive=True, negated=True)
        sql = _compile_sql(UserFairShareConditions.by_user_username_contains(spec)())
        assert "NOT" in sql
        # Default dialect compiles ilike as lower(...) LIKE lower(...)
        assert "lower" in sql

    def test_username_equals_case_insensitive(self) -> None:
        spec = StringMatchSpec(value="Admin", case_insensitive=True, negated=False)
        sql = _compile_sql(UserFairShareConditions.by_user_username_equals(spec)())
        assert "lower" in sql

    def test_email_contains_negated(self) -> None:
        spec = StringMatchSpec(value="@example", case_insensitive=False, negated=True)
        sql = _compile_sql(UserFairShareConditions.by_user_email_contains(spec)())
        assert "NOT" in sql

    def test_email_ends_with_case_insensitive(self) -> None:
        spec = StringMatchSpec(value=".COM", case_insensitive=True, negated=False)
        sql = _compile_sql(UserFairShareConditions.by_user_email_ends_with(spec)())
        # Default dialect compiles ilike as lower(...) LIKE lower(...)
        assert "lower" in sql
