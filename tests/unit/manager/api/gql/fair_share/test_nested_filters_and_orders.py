"""Tests for nested filter and entity order extensions on fair share GQL types."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql.base import PGDialect as _PostgreSQLDialect

from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.fair_share.types.domain import (
    DomainFairShareDomainNestedFilter,
    DomainFairShareFilter,
    DomainFairShareOrderBy,
    DomainFairShareOrderField,
)
from ai.backend.manager.api.gql.fair_share.types.project import (
    ProjectFairShareFilter,
    ProjectFairShareOrderBy,
    ProjectFairShareOrderField,
    ProjectFairShareProjectNestedFilter,
    ProjectFairShareTypeEnum,
    ProjectFairShareTypeEnumFilter,
)
from ai.backend.manager.api.gql.fair_share.types.user import (
    UserFairShareFilter,
    UserFairShareOrderBy,
    UserFairShareOrderField,
    UserFairShareUserNestedFilter,
)


class TestDomainFairShareDomainNestedFilter:
    """Tests for DomainFairShareDomainNestedFilter."""

    def test_build_conditions_empty(self) -> None:
        nested = DomainFairShareDomainNestedFilter()
        conditions = nested.build_conditions()
        assert conditions == []

    def test_build_conditions_is_active_true(self) -> None:
        nested = DomainFairShareDomainNestedFilter(is_active=True)
        conditions = nested.build_conditions()
        assert len(conditions) == 1

    def test_build_conditions_is_active_false(self) -> None:
        nested = DomainFairShareDomainNestedFilter(is_active=False)
        conditions = nested.build_conditions()
        assert len(conditions) == 1

    def test_filter_includes_domain_nested(self) -> None:
        nested = DomainFairShareDomainNestedFilter(is_active=True)
        f = DomainFairShareFilter(domain=nested)
        conditions = f.build_conditions()
        assert len(conditions) == 1


class TestDomainFairShareEntityOrderField:
    """Tests for DOMAIN_IS_ACTIVE order field."""

    def test_domain_is_active_order(self) -> None:
        order_by = DomainFairShareOrderBy(
            field=DomainFairShareOrderField.DOMAIN_IS_ACTIVE,
            direction=OrderDirection.ASC,
        )
        query_order = order_by.to_query_order()
        assert query_order is not None

    def test_domain_is_active_order_desc(self) -> None:
        order_by = DomainFairShareOrderBy(
            field=DomainFairShareOrderField.DOMAIN_IS_ACTIVE,
            direction=OrderDirection.DESC,
        )
        query_order = order_by.to_query_order()
        assert query_order is not None


class TestProjectFairShareProjectNestedFilter:
    """Tests for ProjectFairShareProjectNestedFilter."""

    def test_build_conditions_empty(self) -> None:
        nested = ProjectFairShareProjectNestedFilter()
        conditions = nested.build_conditions()
        assert conditions == []

    def test_build_conditions_is_active(self) -> None:
        nested = ProjectFairShareProjectNestedFilter(is_active=True)
        conditions = nested.build_conditions()
        assert len(conditions) == 1

    def test_build_conditions_name_equals(self) -> None:
        nested = ProjectFairShareProjectNestedFilter(
            name=StringFilter(equals="my-project"),
        )
        conditions = nested.build_conditions()
        assert len(conditions) == 1

    def test_build_conditions_type_equals(self) -> None:
        nested = ProjectFairShareProjectNestedFilter(
            type=ProjectFairShareTypeEnumFilter(equals=ProjectFairShareTypeEnum.GENERAL),
        )
        conditions = nested.build_conditions()
        assert len(conditions) == 1

    def test_build_conditions_type_in(self) -> None:
        nested = ProjectFairShareProjectNestedFilter(
            type=ProjectFairShareTypeEnumFilter(
                in_=[ProjectFairShareTypeEnum.GENERAL, ProjectFairShareTypeEnum.MODEL_STORE],
            ),
        )
        conditions = nested.build_conditions()
        assert len(conditions) == 1

    def test_build_conditions_type_not_equals(self) -> None:
        nested = ProjectFairShareProjectNestedFilter(
            type=ProjectFairShareTypeEnumFilter(not_equals=ProjectFairShareTypeEnum.MODEL_STORE),
        )
        conditions = nested.build_conditions()
        assert len(conditions) == 1

    def test_build_conditions_type_not_in(self) -> None:
        nested = ProjectFairShareProjectNestedFilter(
            type=ProjectFairShareTypeEnumFilter(
                not_in=[ProjectFairShareTypeEnum.MODEL_STORE],
            ),
        )
        conditions = nested.build_conditions()
        assert len(conditions) == 1

    def test_build_conditions_combined(self) -> None:
        nested = ProjectFairShareProjectNestedFilter(
            name=StringFilter(contains="test"),
            is_active=True,
            type=ProjectFairShareTypeEnumFilter(equals=ProjectFairShareTypeEnum.GENERAL),
        )
        conditions = nested.build_conditions()
        assert len(conditions) == 3

    def test_filter_includes_project_nested(self) -> None:
        nested = ProjectFairShareProjectNestedFilter(is_active=True)
        f = ProjectFairShareFilter(project=nested)
        conditions = f.build_conditions()
        assert len(conditions) == 1


class TestProjectFairShareEntityOrderField:
    """Tests for PROJECT_NAME and PROJECT_IS_ACTIVE order fields."""

    def test_project_name_order(self) -> None:
        order_by = ProjectFairShareOrderBy(
            field=ProjectFairShareOrderField.PROJECT_NAME,
            direction=OrderDirection.ASC,
        )
        query_order = order_by.to_query_order()
        assert query_order is not None

    def test_project_is_active_order(self) -> None:
        order_by = ProjectFairShareOrderBy(
            field=ProjectFairShareOrderField.PROJECT_IS_ACTIVE,
            direction=OrderDirection.DESC,
        )
        query_order = order_by.to_query_order()
        assert query_order is not None


class TestUserFairShareUserNestedFilter:
    """Tests for UserFairShareUserNestedFilter."""

    def test_build_conditions_empty(self) -> None:
        nested = UserFairShareUserNestedFilter()
        conditions = nested.build_conditions()
        assert conditions == []

    def test_build_conditions_username_equals(self) -> None:
        nested = UserFairShareUserNestedFilter(
            username=StringFilter(equals="admin"),
        )
        conditions = nested.build_conditions()
        assert len(conditions) == 1

    def test_build_conditions_email_contains(self) -> None:
        nested = UserFairShareUserNestedFilter(
            email=StringFilter(contains="@example"),
        )
        conditions = nested.build_conditions()
        assert len(conditions) == 1

    def test_build_conditions_is_active(self) -> None:
        nested = UserFairShareUserNestedFilter(is_active=True)
        conditions = nested.build_conditions()
        assert len(conditions) == 1

    def test_build_conditions_combined(self) -> None:
        nested = UserFairShareUserNestedFilter(
            username=StringFilter(starts_with="admin"),
            email=StringFilter(ends_with=".com"),
            is_active=True,
        )
        conditions = nested.build_conditions()
        assert len(conditions) == 3

    def test_filter_includes_user_nested(self) -> None:
        nested = UserFairShareUserNestedFilter(is_active=False)
        f = UserFairShareFilter(user=nested)
        conditions = f.build_conditions()
        assert len(conditions) == 1


class TestUserFairShareEntityOrderField:
    """Tests for USER_USERNAME and USER_EMAIL order fields."""

    def test_user_username_order(self) -> None:
        order_by = UserFairShareOrderBy(
            field=UserFairShareOrderField.USER_USERNAME,
            direction=OrderDirection.ASC,
        )
        query_order = order_by.to_query_order()
        assert query_order is not None

    def test_user_email_order(self) -> None:
        order_by = UserFairShareOrderBy(
            field=UserFairShareOrderField.USER_EMAIL,
            direction=OrderDirection.DESC,
        )
        query_order = order_by.to_query_order()
        assert query_order is not None


_PG_DIALECT: sa.engine.Dialect = _PostgreSQLDialect()


def _compile_sql(expr: sa.sql.expression.ColumnElement[bool]) -> str:
    """Compile a SQLAlchemy expression to a string for assertion."""
    return str(expr.compile(dialect=_PG_DIALECT, compile_kwargs={"literal_binds": True}))


class TestDomainFairShareFilterNegatedCaseInsensitive:
    """Regression tests: negated/case-insensitive filters go through GQL → SQL correctly (BA-4633)."""

    def test_not_contains_filter(self) -> None:
        f = DomainFairShareFilter(resource_group=StringFilter(not_contains="a"))
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile_sql(conditions[0]())
        assert "NOT" in sql
        assert "LIKE" in sql

    def test_i_contains_filter(self) -> None:
        f = DomainFairShareFilter(domain_name=StringFilter(i_contains="a"))
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile_sql(conditions[0]())
        assert "ILIKE" in sql

    def test_i_not_contains_filter(self) -> None:
        f = DomainFairShareFilter(resource_group=StringFilter(i_not_contains="a"))
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile_sql(conditions[0]())
        assert "NOT" in sql
        assert "ILIKE" in sql


class TestProjectFairShareFilterNegatedCaseInsensitive:
    """Regression tests: negated/case-insensitive project filters (BA-4633)."""

    def test_project_name_not_contains(self) -> None:
        nested = ProjectFairShareProjectNestedFilter(
            name=StringFilter(not_contains="test"),
        )
        conditions = nested.build_conditions()
        assert len(conditions) == 1
        sql = _compile_sql(conditions[0]())
        assert "NOT" in sql

    def test_project_name_i_contains(self) -> None:
        nested = ProjectFairShareProjectNestedFilter(
            name=StringFilter(i_contains="test"),
        )
        conditions = nested.build_conditions()
        assert len(conditions) == 1
        sql = _compile_sql(conditions[0]())
        assert "ILIKE" in sql

    def test_resource_group_i_not_contains(self) -> None:
        f = ProjectFairShareFilter(resource_group=StringFilter(i_not_contains="rg"))
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile_sql(conditions[0]())
        assert "NOT" in sql
        assert "ILIKE" in sql


class TestUserFairShareFilterNegatedCaseInsensitive:
    """Regression tests: negated/case-insensitive user filters (BA-4633)."""

    def test_username_not_contains(self) -> None:
        nested = UserFairShareUserNestedFilter(
            username=StringFilter(not_contains="admin"),
        )
        conditions = nested.build_conditions()
        assert len(conditions) == 1
        sql = _compile_sql(conditions[0]())
        assert "NOT" in sql

    def test_email_i_contains(self) -> None:
        nested = UserFairShareUserNestedFilter(
            email=StringFilter(i_contains="@EXAMPLE"),
        )
        conditions = nested.build_conditions()
        assert len(conditions) == 1
        sql = _compile_sql(conditions[0]())
        assert "ILIKE" in sql

    def test_domain_name_i_not_contains(self) -> None:
        f = UserFairShareFilter(domain_name=StringFilter(i_not_contains="dom"))
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile_sql(conditions[0]())
        assert "NOT" in sql
        assert "ILIKE" in sql
