"""Tests for nested filter and entity order extensions on fair share GQL types."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.fair_share.request import (
    DomainFairShareFilter as DomainFairShareFilterDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.request import (
    DomainFairShareOrder as DomainFairShareOrderDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.request import (
    ProjectFairShareFilter as ProjectFairShareFilterDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.request import (
    ProjectFairShareOrder as ProjectFairShareOrderDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.request import (
    UserFairShareFilter as UserFairShareFilterDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.request import (
    UserFairShareOrder as UserFairShareOrderDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.types import (
    DomainFairShareOrderField as DomainFairShareOrderFieldDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.types import (
    ProjectFairShareOrderField as ProjectFairShareOrderFieldDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.types import (
    UserFairShareOrderField as UserFairShareOrderFieldDTO,
)
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
    """Tests for DomainFairShareDomainNestedFilter.to_pydantic()."""

    def test_to_pydantic_empty(self) -> None:
        nested = DomainFairShareDomainNestedFilter()
        dto = nested.to_pydantic()
        assert dto.is_active is None

    def test_to_pydantic_is_active_true(self) -> None:
        nested = DomainFairShareDomainNestedFilter(is_active=True)
        dto = nested.to_pydantic()
        assert dto.is_active is True

    def test_to_pydantic_is_active_false(self) -> None:
        nested = DomainFairShareDomainNestedFilter(is_active=False)
        dto = nested.to_pydantic()
        assert dto.is_active is False

    def test_filter_includes_domain_nested(self) -> None:
        nested = DomainFairShareDomainNestedFilter(is_active=True)
        f = DomainFairShareFilter(domain=nested)
        dto = f.to_pydantic()
        assert isinstance(dto, DomainFairShareFilterDTO)
        assert dto.domain is not None
        assert dto.domain.is_active is True


class TestDomainFairShareEntityOrderField:
    """Tests for DomainFairShareOrderBy.to_pydantic()."""

    def test_domain_is_active_order_asc(self) -> None:
        order_by = DomainFairShareOrderBy(
            field=DomainFairShareOrderField.DOMAIN_IS_ACTIVE,
            direction=OrderDirection.ASC,
        )
        dto = order_by.to_pydantic()
        assert isinstance(dto, DomainFairShareOrderDTO)
        assert dto.field == DomainFairShareOrderFieldDTO.DOMAIN_IS_ACTIVE

    def test_domain_is_active_order_desc(self) -> None:
        order_by = DomainFairShareOrderBy(
            field=DomainFairShareOrderField.DOMAIN_IS_ACTIVE,
            direction=OrderDirection.DESC,
        )
        dto = order_by.to_pydantic()
        assert isinstance(dto, DomainFairShareOrderDTO)
        assert dto.field == DomainFairShareOrderFieldDTO.DOMAIN_IS_ACTIVE


class TestProjectFairShareProjectNestedFilter:
    """Tests for ProjectFairShareProjectNestedFilter.to_pydantic()."""

    def test_to_pydantic_empty(self) -> None:
        nested = ProjectFairShareProjectNestedFilter()
        dto = nested.to_pydantic()
        assert dto.is_active is None

    def test_to_pydantic_is_active(self) -> None:
        nested = ProjectFairShareProjectNestedFilter(is_active=True)
        dto = nested.to_pydantic()
        assert dto.is_active is True

    def test_to_pydantic_name_field_exists(self) -> None:
        # name field is in the GQL type but not yet propagated to DTO
        nested = ProjectFairShareProjectNestedFilter(
            name=StringFilter(equals="my-project"),
        )
        dto = nested.to_pydantic()
        assert dto.is_active is None  # DTO only has is_active for now

    def test_to_pydantic_type_filter_exists(self) -> None:
        # type filter is in the GQL type but not propagated to DTO
        nested = ProjectFairShareProjectNestedFilter(
            type=ProjectFairShareTypeEnumFilter(equals=ProjectFairShareTypeEnum.GENERAL),
        )
        dto = nested.to_pydantic()
        assert dto.is_active is None  # DTO only has is_active for now

    def test_filter_includes_project_nested(self) -> None:
        nested = ProjectFairShareProjectNestedFilter(is_active=True)
        f = ProjectFairShareFilter(project=nested)
        dto = f.to_pydantic()
        assert isinstance(dto, ProjectFairShareFilterDTO)
        assert dto.project is not None
        assert dto.project.is_active is True


class TestProjectFairShareEntityOrderField:
    """Tests for ProjectFairShareOrderBy.to_pydantic()."""

    def test_project_name_order(self) -> None:
        order_by = ProjectFairShareOrderBy(
            field=ProjectFairShareOrderField.PROJECT_NAME,
            direction=OrderDirection.ASC,
        )
        dto = order_by.to_pydantic()
        assert isinstance(dto, ProjectFairShareOrderDTO)
        assert dto.field == ProjectFairShareOrderFieldDTO.PROJECT_NAME

    def test_project_is_active_order(self) -> None:
        order_by = ProjectFairShareOrderBy(
            field=ProjectFairShareOrderField.PROJECT_IS_ACTIVE,
            direction=OrderDirection.DESC,
        )
        dto = order_by.to_pydantic()
        assert isinstance(dto, ProjectFairShareOrderDTO)
        assert dto.field == ProjectFairShareOrderFieldDTO.PROJECT_IS_ACTIVE


class TestUserFairShareUserNestedFilter:
    """Tests for UserFairShareUserNestedFilter.to_pydantic()."""

    def test_to_pydantic_empty(self) -> None:
        nested = UserFairShareUserNestedFilter()
        dto = nested.to_pydantic()
        assert dto.is_active is None

    def test_to_pydantic_username_field_exists(self) -> None:
        # username field is in the GQL type but DTO only has is_active for now
        nested = UserFairShareUserNestedFilter(
            username=StringFilter(equals="admin"),
        )
        dto = nested.to_pydantic()
        assert dto.is_active is None

    def test_to_pydantic_email_field_exists(self) -> None:
        # email field is in the GQL type but DTO only has is_active for now
        nested = UserFairShareUserNestedFilter(
            email=StringFilter(contains="@example"),
        )
        dto = nested.to_pydantic()
        assert dto.is_active is None

    def test_to_pydantic_is_active(self) -> None:
        nested = UserFairShareUserNestedFilter(is_active=True)
        dto = nested.to_pydantic()
        assert dto.is_active is True

    def test_filter_includes_user_nested(self) -> None:
        nested = UserFairShareUserNestedFilter(is_active=False)
        f = UserFairShareFilter(user=nested)
        dto = f.to_pydantic()
        assert isinstance(dto, UserFairShareFilterDTO)
        assert dto.user is not None
        assert dto.user.is_active is False


class TestUserFairShareEntityOrderField:
    """Tests for UserFairShareOrderBy.to_pydantic()."""

    def test_user_username_order(self) -> None:
        order_by = UserFairShareOrderBy(
            field=UserFairShareOrderField.USER_USERNAME,
            direction=OrderDirection.ASC,
        )
        dto = order_by.to_pydantic()
        assert isinstance(dto, UserFairShareOrderDTO)
        assert dto.field == UserFairShareOrderFieldDTO.USER_USERNAME

    def test_user_email_order(self) -> None:
        order_by = UserFairShareOrderBy(
            field=UserFairShareOrderField.USER_EMAIL,
            direction=OrderDirection.DESC,
        )
        dto = order_by.to_pydantic()
        assert isinstance(dto, UserFairShareOrderDTO)
        assert dto.field == UserFairShareOrderFieldDTO.USER_EMAIL


class TestDomainFairShareFilterNegatedCaseInsensitive:
    """Tests for negated/case-insensitive GQL filter fields via to_pydantic()."""

    def test_not_contains_filter_produces_dto(self) -> None:
        f = DomainFairShareFilter(resource_group=StringFilter(not_contains="a"))
        dto = f.to_pydantic()
        assert isinstance(dto, DomainFairShareFilterDTO)
        assert dto.resource_group is not None
        assert dto.resource_group.not_contains == "a"

    def test_i_contains_filter_produces_dto(self) -> None:
        f = DomainFairShareFilter(domain_name=StringFilter(i_contains="a"))
        dto = f.to_pydantic()
        assert isinstance(dto, DomainFairShareFilterDTO)
        assert dto.domain_name is not None
        assert dto.domain_name.i_contains == "a"

    def test_i_not_contains_filter_produces_dto(self) -> None:
        f = DomainFairShareFilter(resource_group=StringFilter(i_not_contains="a"))
        dto = f.to_pydantic()
        assert isinstance(dto, DomainFairShareFilterDTO)
        assert dto.resource_group is not None
        assert dto.resource_group.i_not_contains == "a"


class TestProjectFairShareFilterNegatedCaseInsensitive:
    """Tests for negated/case-insensitive project filter fields via to_pydantic()."""

    def test_project_resource_group_not_contains(self) -> None:
        f = ProjectFairShareFilter(resource_group=StringFilter(not_contains="test"))
        dto = f.to_pydantic()
        assert isinstance(dto, ProjectFairShareFilterDTO)
        assert dto.resource_group is not None
        assert dto.resource_group.not_contains == "test"

    def test_project_domain_name_i_contains(self) -> None:
        f = ProjectFairShareFilter(domain_name=StringFilter(i_contains="test"))
        dto = f.to_pydantic()
        assert isinstance(dto, ProjectFairShareFilterDTO)
        assert dto.domain_name is not None
        assert dto.domain_name.i_contains == "test"

    def test_resource_group_i_not_contains(self) -> None:
        f = ProjectFairShareFilter(resource_group=StringFilter(i_not_contains="rg"))
        dto = f.to_pydantic()
        assert isinstance(dto, ProjectFairShareFilterDTO)
        assert dto.resource_group is not None
        assert dto.resource_group.i_not_contains == "rg"


class TestUserFairShareFilterNegatedCaseInsensitive:
    """Tests for negated/case-insensitive user filter fields via to_pydantic()."""

    def test_user_resource_group_not_contains(self) -> None:
        f = UserFairShareFilter(resource_group=StringFilter(not_contains="admin"))
        dto = f.to_pydantic()
        assert isinstance(dto, UserFairShareFilterDTO)
        assert dto.resource_group is not None
        assert dto.resource_group.not_contains == "admin"

    def test_user_domain_name_i_contains(self) -> None:
        f = UserFairShareFilter(domain_name=StringFilter(i_contains="@EXAMPLE"))
        dto = f.to_pydantic()
        assert isinstance(dto, UserFairShareFilterDTO)
        assert dto.domain_name is not None
        assert dto.domain_name.i_contains == "@EXAMPLE"

    def test_domain_name_i_not_contains(self) -> None:
        f = UserFairShareFilter(domain_name=StringFilter(i_not_contains="dom"))
        dto = f.to_pydantic()
        assert isinstance(dto, UserFairShareFilterDTO)
        assert dto.domain_name is not None
        assert dto.domain_name.i_not_contains == "dom"
