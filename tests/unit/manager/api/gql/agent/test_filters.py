"""Unit tests for AgentV2 GraphQL filter and order-by types."""

from __future__ import annotations

from ai.backend.manager.api.gql.agent.types import (
    AgentV2FilterGQL,
    AgentV2OrderByGQL,
    AgentV2OrderFieldGQL,
    AgentV2StatusFilterGQL,
)
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.data.agent.types import AgentStatus

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


class TestAgentFilter:
    """Tests for AgentV2FilterGQL.build_conditions()."""

    def test_id_filter(self) -> None:
        f = AgentV2FilterGQL(id=StringFilter(contains="agent-01"))
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile(conditions[0])
        assert "agents" in sql

    def test_status_in_filter(self) -> None:
        f = AgentV2FilterGQL(
            status=AgentV2StatusFilterGQL(in_=[AgentStatus.ALIVE, AgentStatus.LOST]),
        )
        conditions = f.build_conditions()
        assert len(conditions) == 1

    def test_status_equals_filter(self) -> None:
        f = AgentV2FilterGQL(
            status=AgentV2StatusFilterGQL(equals=AgentStatus.ALIVE),
        )
        conditions = f.build_conditions()
        assert len(conditions) == 1

    def test_schedulable_filter(self) -> None:
        f = AgentV2FilterGQL(schedulable=True)
        conditions = f.build_conditions()
        assert len(conditions) == 1

    def test_scaling_group_filter(self) -> None:
        f = AgentV2FilterGQL(scaling_group=StringFilter(equals="default"))
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile(conditions[0])
        assert "scaling_group" in sql

    def test_combined_filters(self) -> None:
        f = AgentV2FilterGQL(
            id=StringFilter(contains="agent"),
            schedulable=True,
            scaling_group=StringFilter(equals="gpu"),
        )
        conditions = f.build_conditions()
        assert len(conditions) == 3

    def test_empty_filter_returns_empty_list(self) -> None:
        f = AgentV2FilterGQL()
        conditions = f.build_conditions()
        assert conditions == []


class TestAgentOrderBy:
    """Tests for AgentV2OrderByGQL.to_query_order()."""

    def test_id_ascending(self) -> None:
        order = AgentV2OrderByGQL(
            field=AgentV2OrderFieldGQL.ID,
            direction=OrderDirection.ASC,
        )
        result = order.to_query_order()
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "ASC" in sql.upper()

    def test_status_ascending(self) -> None:
        order = AgentV2OrderByGQL(
            field=AgentV2OrderFieldGQL.STATUS,
            direction=OrderDirection.ASC,
        )
        result = order.to_query_order()
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "status" in sql
        assert "ASC" in sql.upper()

    def test_status_descending(self) -> None:
        order = AgentV2OrderByGQL(
            field=AgentV2OrderFieldGQL.STATUS,
            direction=OrderDirection.DESC,
        )
        result = order.to_query_order()
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "status" in sql
        assert "DESC" in sql.upper()

    def test_first_contact_ascending(self) -> None:
        order = AgentV2OrderByGQL(
            field=AgentV2OrderFieldGQL.FIRST_CONTACT,
            direction=OrderDirection.ASC,
        )
        result = order.to_query_order()
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "first_contact" in sql
        assert "ASC" in sql.upper()

    def test_scaling_group_descending(self) -> None:
        order = AgentV2OrderByGQL(
            field=AgentV2OrderFieldGQL.SCALING_GROUP,
            direction=OrderDirection.DESC,
        )
        result = order.to_query_order()
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "scaling_group" in sql
        assert "DESC" in sql.upper()

    def test_schedulable_ascending(self) -> None:
        order = AgentV2OrderByGQL(
            field=AgentV2OrderFieldGQL.SCHEDULABLE,
            direction=OrderDirection.ASC,
        )
        result = order.to_query_order()
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "schedulable" in sql
        assert "ASC" in sql.upper()
