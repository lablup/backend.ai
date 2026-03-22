"""Tests for ai.backend.common.dto.manager.v2.agent.request module."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.agent.request import (
    AgentFilter,
    AgentOrder,
    AgentPathParam,
    SearchAgentsInput,
)
from ai.backend.common.dto.manager.v2.agent.types import (
    AgentOrderField,
    AgentStatusEnum,
    AgentStatusFilter,
    OrderDirection,
)


class TestAgentPathParam:
    """Tests for AgentPathParam model."""

    def test_valid_creation(self) -> None:
        param = AgentPathParam(agent_id="i-1234567890abcdef")
        assert param.agent_id == "i-1234567890abcdef"

    def test_missing_agent_id_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            AgentPathParam.model_validate({})

    def test_round_trip(self) -> None:
        param = AgentPathParam(agent_id="agent-xyz")
        json_str = param.model_dump_json()
        restored = AgentPathParam.model_validate_json(json_str)
        assert restored.agent_id == "agent-xyz"


class TestAgentFilter:
    """Tests for AgentFilter model."""

    def test_all_none_defaults(self) -> None:
        f = AgentFilter()
        assert f.status is None
        assert f.scaling_group is None

    def test_with_status_filter(self) -> None:
        status_filter = AgentStatusFilter(equals=AgentStatusEnum.ALIVE)
        f = AgentFilter(status=status_filter)
        assert f.status is not None
        assert f.status.equals == AgentStatusEnum.ALIVE

    def test_with_status_in_filter(self) -> None:
        status_filter = AgentStatusFilter(in_=[AgentStatusEnum.ALIVE, AgentStatusEnum.RESTARTING])
        f = AgentFilter(status=status_filter)
        assert f.status is not None
        assert f.status.in_ == [AgentStatusEnum.ALIVE, AgentStatusEnum.RESTARTING]

    def test_round_trip(self) -> None:
        status_filter = AgentStatusFilter(equals=AgentStatusEnum.ALIVE)
        f = AgentFilter(status=status_filter)
        json_str = f.model_dump_json()
        restored = AgentFilter.model_validate_json(json_str)
        assert restored.status is not None
        assert restored.status.equals == AgentStatusEnum.ALIVE


class TestAgentOrder:
    """Tests for AgentOrder model."""

    def test_creation_with_field(self) -> None:
        order = AgentOrder(field=AgentOrderField.ID)
        assert order.field == AgentOrderField.ID
        assert order.direction == OrderDirection.ASC

    def test_creation_with_desc_direction(self) -> None:
        order = AgentOrder(field=AgentOrderField.STATUS, direction=OrderDirection.DESC)
        assert order.field == AgentOrderField.STATUS
        assert order.direction == OrderDirection.DESC

    def test_round_trip(self) -> None:
        order = AgentOrder(field=AgentOrderField.SCALING_GROUP, direction=OrderDirection.ASC)
        json_str = order.model_dump_json()
        restored = AgentOrder.model_validate_json(json_str)
        assert restored.field == AgentOrderField.SCALING_GROUP
        assert restored.direction == OrderDirection.ASC


class TestSearchAgentsInput:
    """Tests for SearchAgentsInput model."""

    def test_defaults(self) -> None:
        inp = SearchAgentsInput()
        assert inp.filter is None
        assert inp.order is None
        assert inp.limit > 0
        assert inp.offset == 0

    def test_with_status_filter(self) -> None:
        status_filter = AgentStatusFilter(equals=AgentStatusEnum.ALIVE)
        agent_filter = AgentFilter(status=status_filter)
        inp = SearchAgentsInput(filter=agent_filter)
        assert inp.filter is not None
        assert inp.filter.status is not None
        assert inp.filter.status.equals == AgentStatusEnum.ALIVE

    def test_with_order_list(self) -> None:
        orders = [AgentOrder(field=AgentOrderField.ID, direction=OrderDirection.ASC)]
        inp = SearchAgentsInput(order=orders, limit=20, offset=5)
        assert inp.order is not None
        assert len(inp.order) == 1
        assert inp.order[0].field == AgentOrderField.ID
        assert inp.limit == 20
        assert inp.offset == 5

    def test_with_filter_and_order(self) -> None:
        status_filter = AgentStatusFilter(equals=AgentStatusEnum.ALIVE)
        agent_filter = AgentFilter(status=status_filter)
        orders = [AgentOrder(field=AgentOrderField.STATUS, direction=OrderDirection.DESC)]
        inp = SearchAgentsInput(filter=agent_filter, order=orders, limit=50, offset=0)
        assert inp.filter is not None
        assert inp.order is not None
        assert inp.limit == 50

    def test_invalid_limit_zero_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            SearchAgentsInput(limit=0)

    def test_invalid_offset_negative_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            SearchAgentsInput(offset=-1)

    def test_round_trip(self) -> None:
        status_filter = AgentStatusFilter(in_=[AgentStatusEnum.ALIVE])
        agent_filter = AgentFilter(status=status_filter)
        inp = SearchAgentsInput(filter=agent_filter, limit=10, offset=0)
        json_str = inp.model_dump_json()
        restored = SearchAgentsInput.model_validate_json(json_str)
        assert restored.filter is not None
        assert restored.filter.status is not None
        assert restored.filter.status.in_ == [AgentStatusEnum.ALIVE]
        assert restored.limit == 10
