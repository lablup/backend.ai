"""Agent reservation amounts survive the REST and GraphQL conversions."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
import strawberry
from pydantic import ValidationError

from ai.backend.common.data.entity.agent_resource import AgentResourceID
from ai.backend.common.dto.manager.v2.resource_slot.request import AgentResourceFilter
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    AdminSearchAgentResourcesPayload,
    AgentResourceNode,
)
from ai.backend.common.dto.manager.v2.resource_slot.types import AgentResourceOrderField
from ai.backend.manager.api.adapters.resource_slot.adapter import ResourceSlotAdapter
from ai.backend.manager.api.gql.agent.types import AgentV2GQL
from ai.backend.manager.api.gql.base import DecimalFilter
from ai.backend.manager.api.gql.resource_slot.types import (
    AgentResourceSlotFilterGQL,
    AgentResourceSlotGQL,
    AgentResourceSlotOrderByGQL,
    AgentResourceSlotOrderFieldGQL,
)
from ai.backend.manager.data.resource_slot.types import AgentResourceData


@pytest.fixture(params=[("0", "0"), ("1.23456789", "0.00000001")])
def resource_data(request: pytest.FixtureRequest) -> AgentResourceData:
    reserved, prereserved = request.param
    return AgentResourceData(
        id=AgentResourceID(uuid4()),
        agent_id="agent-test",
        slot_name="cpu",
        capacity=Decimal("8"),
        reserved=Decimal(reserved),
        prereserved=Decimal(prereserved),
        used=Decimal("2"),
    )


@pytest.fixture
def node(resource_data: AgentResourceData) -> AgentResourceNode:
    return ResourceSlotAdapter._agent_resource_data_to_node(resource_data)


@pytest.fixture
def info(node: AgentResourceNode) -> MagicMock:
    info = MagicMock()
    info.context.adapters.resource_slot.search_agent_resources = AsyncMock(
        return_value=AdminSearchAgentResourcesPayload(
            items=[node], total_count=1, has_next_page=False, has_previous_page=False
        )
    )
    return info


@pytest.fixture
def agent() -> AgentV2GQL:
    return AgentV2GQL(
        id=strawberry.ID("agent-test"),
        entity_id=uuid4(),
        uuid=uuid4(),
        resource_info=MagicMock(),
        status_info=MagicMock(),
        system_info=MagicMock(),
        network_info=MagicMock(),
        permissions=[],
        scaling_group="default",
    )


class TestAgentResourceReservations:
    def test_rest_response_preserves_precision(
        self, resource_data: AgentResourceData, node: AgentResourceNode
    ) -> None:
        restored = AgentResourceNode.model_validate_json(node.model_dump_json())
        assert restored.reserved == str(resource_data.reserved)
        assert restored.prereserved == str(resource_data.prereserved)

    def test_graphql_node_preserves_precision(
        self, resource_data: AgentResourceData, node: AgentResourceNode
    ) -> None:
        gql_node = AgentResourceSlotGQL.from_pydantic(node)
        assert gql_node.reserved == resource_data.reserved
        assert gql_node.prereserved == resource_data.prereserved

    async def test_agent_resource_connection_keeps_filter_and_amounts(
        self, agent: AgentV2GQL, info: MagicMock, resource_data: AgentResourceData
    ) -> None:
        connection = await agent.resource_slots(
            info,
            filter=AgentResourceSlotFilterGQL(
                reserved=DecimalFilter(equals=resource_data.reserved),
                prereserved=DecimalFilter(equals=resource_data.prereserved),
            ),
        )
        assert connection is not None
        assert connection.edges[0].node.reserved == resource_data.reserved
        assert connection.edges[0].node.prereserved == resource_data.prereserved
        search_input = info.context.adapters.resource_slot.search_agent_resources.call_args.args[0]
        assert search_input.filter.agent_id.equals == "agent-test"
        assert search_input.filter.reserved.equals == resource_data.reserved
        assert search_input.filter.prereserved.equals == resource_data.prereserved

    @pytest.mark.parametrize(
        ("gql_field", "dto_field"),
        [
            (AgentResourceSlotOrderFieldGQL.RESERVED, AgentResourceOrderField.RESERVED),
            (AgentResourceSlotOrderFieldGQL.PRERESERVED, AgentResourceOrderField.PRERESERVED),
        ],
    )
    def test_graphql_order_maps_to_rest_field(
        self, gql_field: AgentResourceSlotOrderFieldGQL, dto_field: AgentResourceOrderField
    ) -> None:
        assert AgentResourceSlotOrderByGQL(field=gql_field).to_pydantic().field == dto_field

    @pytest.mark.parametrize("field", ["reserved", "prereserved"])
    def test_invalid_decimal_is_rejected(self, field: str) -> None:
        with pytest.raises(ValidationError):
            AgentResourceFilter.model_validate({field: {"equals": "not-a-number"}})
