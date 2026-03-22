"""Unit tests for AgentV2 GraphQL filter and order-by types."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.agent.request import AgentFilter, AgentOrder
from ai.backend.common.dto.manager.v2.agent.types import (
    AgentOrderField,
    AgentStatusEnum,
    AgentStatusFilter,
    OrderDirection,
)
from ai.backend.manager.api.gql.agent.types import (
    AgentFilterGQL,
    AgentOrderByGQL,
    AgentOrderFieldGQL,
    AgentStatusFilterGQL,
)
from ai.backend.manager.api.gql.base import OrderDirection as GQLOrderDirection
from ai.backend.manager.api.gql.base import StringFilter


class TestAgentFilter:
    """Tests for AgentFilterGQL.to_pydantic()."""

    def test_id_filter(self) -> None:
        f = AgentFilterGQL(id=StringFilter(contains="agent-01"))
        result = f.to_pydantic()
        assert isinstance(result, AgentFilter)
        assert result.id is not None
        assert result.id.contains == "agent-01"

    def test_status_in_filter(self) -> None:
        f = AgentFilterGQL(
            status=AgentStatusFilterGQL(in_=[AgentStatusEnum.ALIVE, AgentStatusEnum.LOST]),
        )
        result = f.to_pydantic()
        assert isinstance(result, AgentFilter)
        assert result.status is not None
        assert isinstance(result.status, AgentStatusFilter)
        assert result.status.in_ is not None
        assert AgentStatusEnum.ALIVE in result.status.in_
        assert AgentStatusEnum.LOST in result.status.in_

    def test_status_equals_filter(self) -> None:
        f = AgentFilterGQL(
            status=AgentStatusFilterGQL(equals=AgentStatusEnum.ALIVE),
        )
        result = f.to_pydantic()
        assert isinstance(result, AgentFilter)
        assert result.status is not None
        assert result.status.equals == AgentStatusEnum.ALIVE

    def test_schedulable_filter(self) -> None:
        f = AgentFilterGQL(schedulable=True)
        result = f.to_pydantic()
        assert isinstance(result, AgentFilter)
        assert result.schedulable is True

    def test_scaling_group_filter(self) -> None:
        f = AgentFilterGQL(scaling_group=StringFilter(equals="default"))
        result = f.to_pydantic()
        assert isinstance(result, AgentFilter)
        assert result.scaling_group is not None
        assert result.scaling_group.equals == "default"

    def test_combined_filters(self) -> None:
        f = AgentFilterGQL(
            id=StringFilter(contains="agent"),
            schedulable=True,
            scaling_group=StringFilter(equals="gpu"),
        )
        result = f.to_pydantic()
        assert isinstance(result, AgentFilter)
        assert result.id is not None
        assert result.schedulable is True
        assert result.scaling_group is not None

    def test_empty_filter(self) -> None:
        f = AgentFilterGQL()
        result = f.to_pydantic()
        assert isinstance(result, AgentFilter)
        assert result.id is None
        assert result.status is None
        assert result.schedulable is None
        assert result.scaling_group is None

    def test_and_filter(self) -> None:
        f = AgentFilterGQL(
            AND=[
                AgentFilterGQL(id=StringFilter(contains="agent-01")),
                AgentFilterGQL(schedulable=True),
            ]
        )
        result = f.to_pydantic()
        assert isinstance(result, AgentFilter)
        assert result.AND is not None
        assert len(result.AND) == 2

    def test_or_filter(self) -> None:
        f = AgentFilterGQL(
            OR=[
                AgentFilterGQL(id=StringFilter(contains="agent-01")),
                AgentFilterGQL(id=StringFilter(contains="agent-02")),
            ]
        )
        result = f.to_pydantic()
        assert isinstance(result, AgentFilter)
        assert result.OR is not None
        assert len(result.OR) == 2

    def test_not_filter(self) -> None:
        f = AgentFilterGQL(
            NOT=[
                AgentFilterGQL(schedulable=False),
            ]
        )
        result = f.to_pydantic()
        assert isinstance(result, AgentFilter)
        assert result.NOT is not None
        assert len(result.NOT) == 1


class TestAgentOrderBy:
    """Tests for AgentOrderByGQL.to_pydantic()."""

    def test_id_ascending(self) -> None:
        order = AgentOrderByGQL(
            field=AgentOrderFieldGQL.ID,
            direction=GQLOrderDirection.ASC,
        )
        result = order.to_pydantic()
        assert isinstance(result, AgentOrder)
        assert result.field == AgentOrderField.ID
        assert result.direction == OrderDirection.ASC

    def test_status_ascending(self) -> None:
        order = AgentOrderByGQL(
            field=AgentOrderFieldGQL.STATUS,
            direction=GQLOrderDirection.ASC,
        )
        result = order.to_pydantic()
        assert isinstance(result, AgentOrder)
        assert result.field == AgentOrderField.STATUS
        assert result.direction == OrderDirection.ASC

    def test_status_descending(self) -> None:
        order = AgentOrderByGQL(
            field=AgentOrderFieldGQL.STATUS,
            direction=GQLOrderDirection.DESC,
        )
        result = order.to_pydantic()
        assert isinstance(result, AgentOrder)
        assert result.field == AgentOrderField.STATUS
        assert result.direction == OrderDirection.DESC

    def test_first_contact_ascending(self) -> None:
        order = AgentOrderByGQL(
            field=AgentOrderFieldGQL.FIRST_CONTACT,
            direction=GQLOrderDirection.ASC,
        )
        result = order.to_pydantic()
        assert isinstance(result, AgentOrder)
        assert result.field == AgentOrderField.FIRST_CONTACT
        assert result.direction == OrderDirection.ASC

    def test_scaling_group_descending(self) -> None:
        order = AgentOrderByGQL(
            field=AgentOrderFieldGQL.SCALING_GROUP,
            direction=GQLOrderDirection.DESC,
        )
        result = order.to_pydantic()
        assert isinstance(result, AgentOrder)
        assert result.field == AgentOrderField.SCALING_GROUP
        assert result.direction == OrderDirection.DESC

    def test_schedulable_ascending(self) -> None:
        order = AgentOrderByGQL(
            field=AgentOrderFieldGQL.SCHEDULABLE,
            direction=GQLOrderDirection.ASC,
        )
        result = order.to_pydantic()
        assert isinstance(result, AgentOrder)
        assert result.field == AgentOrderField.SCHEDULABLE
        assert result.direction == OrderDirection.ASC
