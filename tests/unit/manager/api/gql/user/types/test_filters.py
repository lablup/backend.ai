"""Unit tests for UserV2 GraphQL nested filter and order-by types."""

from __future__ import annotations

from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.user.types.filters import (
    UserDomainNestedFilter,
    UserFilterGQL,
    UserOrderByGQL,
    UserOrderFieldGQL,
    UserProjectNestedFilter,
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
from ai.backend.manager.repositories.base import QueryCondition

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


def _compile(condition_callable: QueryCondition) -> str:
    """Compile a QueryCondition callable to SQL string."""
    return str(condition_callable().compile(compile_kwargs={"literal_binds": True}))


class TestUserDomainNestedFilter:
    """Tests for UserDomainNestedFilter.build_conditions()."""

    def test_name_filter_generates_exists_with_domains(self) -> None:
        f = UserDomainNestedFilter(
            name=StringFilter(contains="test"),
            is_active=None,
        )
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile(conditions[0])
        assert "EXISTS" in sql
        assert "domains" in sql

    def test_is_active_filter_generates_exists(self) -> None:
        f = UserDomainNestedFilter(
            name=None,
            is_active=True,
        )
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile(conditions[0])
        assert "EXISTS" in sql
        assert "is_active" in sql

    def test_combined_name_and_is_active_single_exists(self) -> None:
        f = UserDomainNestedFilter(
            name=StringFilter(equals="my-domain"),
            is_active=True,
        )
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile(conditions[0])
        assert "EXISTS" in sql
        assert sql.count("EXISTS") == 1

    def test_empty_filter_returns_empty_list(self) -> None:
        f = UserDomainNestedFilter(
            name=None,
            is_active=None,
        )
        conditions = f.build_conditions()
        assert conditions == []


class TestUserProjectNestedFilter:
    """Tests for UserProjectNestedFilter.build_conditions()."""

    def test_name_filter_generates_exists_with_join(self) -> None:
        f = UserProjectNestedFilter(
            name=StringFilter(contains="ml-team"),
            is_active=None,
        )
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile(conditions[0])
        assert "EXISTS" in sql
        assert "association_groups_users" in sql
        assert "groups" in sql

    def test_is_active_filter_generates_exists(self) -> None:
        f = UserProjectNestedFilter(
            name=None,
            is_active=False,
        )
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile(conditions[0])
        assert "EXISTS" in sql
        assert "is_active" in sql

    def test_combined_name_and_is_active_single_exists(self) -> None:
        f = UserProjectNestedFilter(
            name=StringFilter(equals="project-x"),
            is_active=True,
        )
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile(conditions[0])
        assert "EXISTS" in sql
        assert sql.count("EXISTS") == 1

    def test_empty_filter_returns_empty_list(self) -> None:
        f = UserProjectNestedFilter(
            name=None,
            is_active=None,
        )
        conditions = f.build_conditions()
        assert conditions == []


class TestUserFilterGQLWithNestedFilters:
    """Tests for UserFilterGQL integration with nested domain/project filters."""

    def test_domain_nested_adds_exists_condition(self) -> None:
        f = UserFilterGQL(
            domain=UserDomainNestedFilter(
                name=StringFilter(contains="example"),
                is_active=None,
            ),
        )
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile(conditions[0])
        assert "EXISTS" in sql
        assert "domains" in sql

    def test_project_nested_adds_exists_condition(self) -> None:
        f = UserFilterGQL(
            project=UserProjectNestedFilter(
                name=StringFilter(contains="team"),
                is_active=None,
            ),
        )
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile(conditions[0])
        assert "EXISTS" in sql
        assert "association_groups_users" in sql

    def test_both_nested_filters_combined(self) -> None:
        f = UserFilterGQL(
            domain=UserDomainNestedFilter(
                name=StringFilter(contains="corp"),
                is_active=None,
            ),
            project=UserProjectNestedFilter(
                name=StringFilter(contains="dev"),
                is_active=None,
            ),
        )
        conditions = f.build_conditions()
        assert len(conditions) == 2

    def test_nested_with_existing_fields(self) -> None:
        f = UserFilterGQL(
            username=StringFilter(contains="admin"),
            domain=UserDomainNestedFilter(
                name=StringFilter(contains="corp"),
                is_active=None,
            ),
        )
        conditions = f.build_conditions()
        assert len(conditions) == 2

    def test_empty_nested_filters_no_extra_conditions(self) -> None:
        f = UserFilterGQL(
            domain=UserDomainNestedFilter(name=None, is_active=None),
            project=UserProjectNestedFilter(name=None, is_active=None),
        )
        conditions = f.build_conditions()
        assert len(conditions) == 0


class TestUserOrderByGQLNewFields:
    """Tests for new DOMAIN_NAME and PROJECT_NAME order fields."""

    def test_domain_name_ascending(self) -> None:
        order = UserOrderByGQL(
            field=UserOrderFieldGQL.DOMAIN_NAME,
            direction=OrderDirection.ASC,
        )
        result = order.to_query_order()
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "domains" in sql
        assert "ASC" in sql.upper()

    def test_domain_name_descending(self) -> None:
        order = UserOrderByGQL(
            field=UserOrderFieldGQL.DOMAIN_NAME,
            direction=OrderDirection.DESC,
        )
        result = order.to_query_order()
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "domains" in sql
        assert "DESC" in sql.upper()

    def test_project_name_ascending(self) -> None:
        order = UserOrderByGQL(
            field=UserOrderFieldGQL.PROJECT_NAME,
            direction=OrderDirection.ASC,
        )
        result = order.to_query_order()
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "min" in sql.lower()
        assert "groups" in sql
        assert "ASC" in sql.upper()

    def test_project_name_descending(self) -> None:
        order = UserOrderByGQL(
            field=UserOrderFieldGQL.PROJECT_NAME,
            direction=OrderDirection.DESC,
        )
        result = order.to_query_order()
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "min" in sql.lower()
        assert "groups" in sql
        assert "DESC" in sql.upper()

    def test_existing_fields_still_work(self) -> None:
        order = UserOrderByGQL(
            field=UserOrderFieldGQL.CREATED_AT,
            direction=OrderDirection.ASC,
        )
        result = order.to_query_order()
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "created_at" in sql
