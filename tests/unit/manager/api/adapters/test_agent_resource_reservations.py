"""The agent's slot connection keeps the reservation filter it hands to the search."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
import strawberry

from ai.backend.common.data.entity.agent_resource import AgentResourceID
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    AdminSearchAgentResourcesPayload,
)
from ai.backend.manager.api.adapters.resource_slot.adapter import ResourceSlotAdapter
from ai.backend.manager.api.gql.agent.types import AgentV2GQL
from ai.backend.manager.api.gql.base import DecimalFilter
from ai.backend.manager.api.gql.resource_slot.types import AgentResourceSlotFilterGQL
from ai.backend.manager.data.resource_slot.types import AgentResourceData


@pytest.fixture
def resource_data() -> AgentResourceData:
    return AgentResourceData(
        id=AgentResourceID(uuid4()),
        agent_id="agent-test",
        slot_name="cpu",
        capacity=Decimal("8"),
        reserved=Decimal("1.5"),
        prereserved=Decimal("0.5"),
        used=Decimal("2"),
    )


@pytest.fixture
def info(resource_data: AgentResourceData) -> MagicMock:
    info = MagicMock()
    info.context.adapters.resource_slot.search_agent_resources = AsyncMock(
        return_value=AdminSearchAgentResourcesPayload(
            items=[ResourceSlotAdapter._agent_resource_data_to_node(resource_data)],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
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
