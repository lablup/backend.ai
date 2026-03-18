"""Unit tests for ResourceGroup GraphQL filter and order-by types."""

from __future__ import annotations

from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.resource_group.types import (
    ResourceGroupFilterGQL,
    ResourceGroupOrderByGQL,
    ResourceGroupOrderFieldGQL,
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
from ai.backend.manager.models.group import GroupRow
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


class TestResourceGroupFilter:
    """Tests for ResourceGroupFilterGQL.build_conditions()."""

    def test_name_filter(self) -> None:
        f = ResourceGroupFilterGQL(name=StringFilter(contains="gpu"))
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile(conditions[0])
        assert "scaling_groups" in sql
        assert "name" in sql

    def test_description_filter(self) -> None:
        f = ResourceGroupFilterGQL(description=StringFilter(contains="production"))
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile(conditions[0])
        assert "description" in sql

    def test_is_active_true_filter(self) -> None:
        f = ResourceGroupFilterGQL(is_active=True)
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile(conditions[0])
        assert "is_active" in sql

    def test_is_active_false_filter(self) -> None:
        f = ResourceGroupFilterGQL(is_active=False)
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile(conditions[0])
        assert "is_active" in sql

    def test_is_public_filter(self) -> None:
        f = ResourceGroupFilterGQL(is_public=True)
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile(conditions[0])
        assert "is_public" in sql

    def test_combined_filters(self) -> None:
        f = ResourceGroupFilterGQL(
            name=StringFilter(contains="gpu"),
            is_active=True,
            is_public=False,
        )
        conditions = f.build_conditions()
        assert len(conditions) == 3

    def test_empty_filter_returns_empty_list(self) -> None:
        f = ResourceGroupFilterGQL()
        conditions = f.build_conditions()
        assert conditions == []

    def test_description_with_name_combined(self) -> None:
        f = ResourceGroupFilterGQL(
            name=StringFilter(equals="default"),
            description=StringFilter(contains="test"),
        )
        conditions = f.build_conditions()
        assert len(conditions) == 2

    def test_or_logical_operator(self) -> None:
        f = ResourceGroupFilterGQL(
            OR=[
                ResourceGroupFilterGQL(is_active=True),
                ResourceGroupFilterGQL(is_public=True),
            ],
        )
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile(conditions[0])
        assert "OR" in sql

    def test_not_logical_operator(self) -> None:
        f = ResourceGroupFilterGQL(
            NOT=[ResourceGroupFilterGQL(is_active=False)],
        )
        conditions = f.build_conditions()
        assert len(conditions) == 1


class TestResourceGroupOrderBy:
    """Tests for ResourceGroupOrderByGQL.to_query_order()."""

    def test_name_ascending(self) -> None:
        order = ResourceGroupOrderByGQL(
            field=ResourceGroupOrderFieldGQL.NAME,
            direction=OrderDirection.ASC,
        )
        result = order.to_query_order()
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "name" in sql
        assert "ASC" in sql.upper()

    def test_name_descending(self) -> None:
        order = ResourceGroupOrderByGQL(
            field=ResourceGroupOrderFieldGQL.NAME,
            direction=OrderDirection.DESC,
        )
        result = order.to_query_order()
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "name" in sql
        assert "DESC" in sql.upper()

    def test_created_at_ascending(self) -> None:
        order = ResourceGroupOrderByGQL(
            field=ResourceGroupOrderFieldGQL.CREATED_AT,
            direction=OrderDirection.ASC,
        )
        result = order.to_query_order()
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "created_at" in sql
        assert "ASC" in sql.upper()

    def test_created_at_descending(self) -> None:
        order = ResourceGroupOrderByGQL(
            field=ResourceGroupOrderFieldGQL.CREATED_AT,
            direction=OrderDirection.DESC,
        )
        result = order.to_query_order()
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "created_at" in sql
        assert "DESC" in sql.upper()

    def test_is_active_ascending(self) -> None:
        order = ResourceGroupOrderByGQL(
            field=ResourceGroupOrderFieldGQL.IS_ACTIVE,
            direction=OrderDirection.ASC,
        )
        result = order.to_query_order()
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "is_active" in sql
        assert "ASC" in sql.upper()

    def test_is_active_descending(self) -> None:
        order = ResourceGroupOrderByGQL(
            field=ResourceGroupOrderFieldGQL.IS_ACTIVE,
            direction=OrderDirection.DESC,
        )
        result = order.to_query_order()
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "is_active" in sql
        assert "DESC" in sql.upper()
