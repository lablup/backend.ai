"""``AgentDetailData`` sums the slot rows read beside the agent."""

from __future__ import annotations

import uuid
from decimal import Decimal

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.agent_resource import AgentResourceID
from ai.backend.common.types import AgentId
from ai.backend.manager.data.agent.types import AgentData, AgentDetailData, AgentStatus
from ai.backend.manager.data.resource_slot.types import AgentResourceData


def _agent() -> AgentData:
    return AgentData(
        uuid=AgentUUID(uuid.uuid4()),
        id=AgentId("i-agent"),
        status=AgentStatus.ALIVE,
        status_changed=None,
        region="local",
        resource_group="default",
        schedulable=True,
        addr="tcp://127.0.0.1:6001",
        public_host=None,
        first_contact=None,
        lost_at=None,
        version="test",
        architecture="x86_64",
        compute_plugins={},
        public_key=None,
        auto_terminate_abusing_kernel=False,
    )


def _resource(slot_name: str, capacity: str, used: str) -> AgentResourceData:
    return AgentResourceData(
        id=AgentResourceID(uuid.uuid4()),
        agent_id="i-agent",
        slot_name=slot_name,
        capacity=Decimal(capacity),
        reserved=Decimal(0),
        used=Decimal(used),
    )


def test_slots_are_summed_from_the_rows_in_their_order() -> None:
    detail = AgentDetailData(
        agent=_agent(),
        resources=[_resource("mem", "1024", "512"), _resource("cpu", "4", "1")],
        permissions=[],
    )

    assert list(detail.available_slots().items()) == [("mem", Decimal(1024)), ("cpu", Decimal(4))]
    assert list(detail.occupied_slots().items()) == [("mem", Decimal(512)), ("cpu", Decimal(1))]


def test_no_rows_means_empty_slots() -> None:
    detail = AgentDetailData(agent=_agent(), resources=[], permissions=[])

    assert dict(detail.available_slots()) == {}
    assert dict(detail.occupied_slots()) == {}
