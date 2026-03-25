"""Unit tests for UserV2 GraphQL nested filter and order-by types."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.user.request import UserFilter as UserFilterDTO
from ai.backend.common.dto.manager.v2.user.types import UserOrderField
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.user.types.filters import (
    UserDomainNestedFilterGQL,
    UserFilterGQL,
    UserOrderByGQL,
    UserOrderFieldGQL,
    UserProjectNestedFilterGQL,
)

# Row imports to trigger mapper initialization (FK dependency order).
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.deployment_auto_scaling_policy import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.vfolder import VFolderRow

# Reference Row models to prevent unused-import removal.
_MAPPER_ROWS = [
    DomainRow,
    ScalingGroupRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    UserRoleRow,
    UserRow,
    KeyPairRow,
    GroupRow,
    AssocGroupUserRow,
    ImageRow,
    VFolderRow,
    EndpointRow,
    DeploymentPolicyRow,
    DeploymentAutoScalingPolicyRow,
    DeploymentRevisionRow,
    SessionRow,
    AgentRow,
    KernelRow,
    RoutingRow,
    ResourcePresetRow,
]


class TestUserDomainNestedFilter:
    """Tests for UserDomainNestedFilterGQL.to_pydantic()."""

    def test_name_filter_converts_to_pydantic(self) -> None:
        f = UserDomainNestedFilterGQL(
            name=StringFilter(contains="test"),
            is_active=None,
        )
        dto = f.to_pydantic()
        assert dto.name is not None
        assert dto.name.contains == "test"
        assert dto.is_active is None

    def test_is_active_filter_converts_to_pydantic(self) -> None:
        f = UserDomainNestedFilterGQL(
            name=None,
            is_active=True,
        )
        dto = f.to_pydantic()
        assert dto.name is None
        assert dto.is_active is True

    def test_combined_name_and_is_active_converts_to_pydantic(self) -> None:
        f = UserDomainNestedFilterGQL(
            name=StringFilter(equals="my-domain"),
            is_active=True,
        )
        dto = f.to_pydantic()
        assert dto.name is not None
        assert dto.name.equals == "my-domain"
        assert dto.is_active is True

    def test_empty_filter_produces_none_fields(self) -> None:
        f = UserDomainNestedFilterGQL(
            name=None,
            is_active=None,
        )
        dto = f.to_pydantic()
        assert dto.name is None
        assert dto.is_active is None


class TestUserProjectNestedFilter:
    """Tests for UserProjectNestedFilterGQL.to_pydantic()."""

    def test_name_filter_converts_to_pydantic(self) -> None:
        f = UserProjectNestedFilterGQL(
            name=StringFilter(contains="ml-team"),
            is_active=None,
        )
        dto = f.to_pydantic()
        assert dto.name is not None
        assert dto.name.contains == "ml-team"
        assert dto.is_active is None

    def test_is_active_filter_converts_to_pydantic(self) -> None:
        f = UserProjectNestedFilterGQL(
            name=None,
            is_active=False,
        )
        dto = f.to_pydantic()
        assert dto.name is None
        assert dto.is_active is False

    def test_combined_name_and_is_active_converts_to_pydantic(self) -> None:
        f = UserProjectNestedFilterGQL(
            name=StringFilter(equals="project-x"),
            is_active=True,
        )
        dto = f.to_pydantic()
        assert dto.name is not None
        assert dto.name.equals == "project-x"
        assert dto.is_active is True

    def test_empty_filter_produces_none_fields(self) -> None:
        f = UserProjectNestedFilterGQL(
            name=None,
            is_active=None,
        )
        dto = f.to_pydantic()
        assert dto.name is None
        assert dto.is_active is None


class TestUserFilterGQLWithNestedFilters:
    """Tests for UserFilterGQL integration with nested domain/project filters via to_pydantic()."""

    def test_domain_nested_propagates_to_pydantic(self) -> None:
        f = UserFilterGQL(
            domain=UserDomainNestedFilterGQL(
                name=StringFilter(contains="example"),
                is_active=None,
            ),
        )
        dto = f.to_pydantic()
        assert isinstance(dto, UserFilterDTO)
        assert dto.domain is not None
        assert dto.domain.name is not None
        assert dto.domain.name.contains == "example"

    def test_project_nested_propagates_to_pydantic(self) -> None:
        f = UserFilterGQL(
            project=UserProjectNestedFilterGQL(
                name=StringFilter(contains="team"),
                is_active=None,
            ),
        )
        dto = f.to_pydantic()
        assert isinstance(dto, UserFilterDTO)
        assert dto.project is not None
        assert dto.project.name is not None
        assert dto.project.name.contains == "team"

    def test_both_nested_filters_propagate_to_pydantic(self) -> None:
        f = UserFilterGQL(
            domain=UserDomainNestedFilterGQL(
                name=StringFilter(contains="corp"),
                is_active=None,
            ),
            project=UserProjectNestedFilterGQL(
                name=StringFilter(contains="dev"),
                is_active=None,
            ),
        )
        dto = f.to_pydantic()
        assert isinstance(dto, UserFilterDTO)
        assert dto.domain is not None
        assert dto.project is not None

    def test_nested_with_username_field(self) -> None:
        f = UserFilterGQL(
            username=StringFilter(contains="admin"),
            domain=UserDomainNestedFilterGQL(
                name=StringFilter(contains="corp"),
                is_active=None,
            ),
        )
        dto = f.to_pydantic()
        assert isinstance(dto, UserFilterDTO)
        assert dto.username is not None
        assert dto.username.contains == "admin"
        assert dto.domain is not None

    def test_empty_nested_filters_produce_none_in_pydantic(self) -> None:
        f = UserFilterGQL(
            domain=UserDomainNestedFilterGQL(name=None, is_active=None),
            project=UserProjectNestedFilterGQL(name=None, is_active=None),
        )
        dto = f.to_pydantic()
        assert isinstance(dto, UserFilterDTO)
        # domain and project DTOs are present but with all None fields
        assert dto.domain is not None
        assert dto.domain.name is None
        assert dto.domain.is_active is None
        assert dto.project is not None
        assert dto.project.name is None
        assert dto.project.is_active is None


class TestUserOrderByGQLNewFields:
    """Tests for UserOrderByGQL.to_pydantic() with DOMAIN_NAME and PROJECT_NAME order fields."""

    def test_domain_name_ascending_converts_to_pydantic(self) -> None:
        order = UserOrderByGQL(
            field=UserOrderFieldGQL.DOMAIN_NAME,
            direction=OrderDirection.ASC,
        )
        dto = order.to_pydantic()
        assert dto.field == UserOrderField.DOMAIN_NAME

    def test_domain_name_descending_converts_to_pydantic(self) -> None:
        order = UserOrderByGQL(
            field=UserOrderFieldGQL.DOMAIN_NAME,
            direction=OrderDirection.DESC,
        )
        dto = order.to_pydantic()
        assert dto.field == UserOrderField.DOMAIN_NAME

    def test_project_name_ascending_converts_to_pydantic(self) -> None:
        order = UserOrderByGQL(
            field=UserOrderFieldGQL.PROJECT_NAME,
            direction=OrderDirection.ASC,
        )
        dto = order.to_pydantic()
        assert dto.field == UserOrderField.PROJECT_NAME

    def test_project_name_descending_converts_to_pydantic(self) -> None:
        order = UserOrderByGQL(
            field=UserOrderFieldGQL.PROJECT_NAME,
            direction=OrderDirection.DESC,
        )
        dto = order.to_pydantic()
        assert dto.field == UserOrderField.PROJECT_NAME

    def test_existing_fields_still_work(self) -> None:
        order = UserOrderByGQL(
            field=UserOrderFieldGQL.CREATED_AT,
            direction=OrderDirection.ASC,
        )
        dto = order.to_pydantic()
        assert dto.field == UserOrderField.CREATED_AT

    def test_username_order_field(self) -> None:
        order = UserOrderByGQL(
            field=UserOrderFieldGQL.USERNAME,
            direction=OrderDirection.ASC,
        )
        dto = order.to_pydantic()
        assert dto.field == UserOrderField.USERNAME

    def test_email_order_field(self) -> None:
        order = UserOrderByGQL(
            field=UserOrderFieldGQL.EMAIL,
            direction=OrderDirection.DESC,
        )
        dto = order.to_pydantic()
        assert dto.field == UserOrderField.EMAIL
