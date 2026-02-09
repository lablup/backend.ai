"""Tests for nested filter and entity order extensions on fair share GQL types."""

from __future__ import annotations

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
