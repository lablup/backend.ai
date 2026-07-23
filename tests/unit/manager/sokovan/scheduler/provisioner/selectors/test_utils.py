"""Test utility functions for agent selectors."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from decimal import Decimal

from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.utils import (
    count_unutilized_capabilities,
    order_slots_by_priority,
)
from ai.backend.manager.views.sokovan.agent import AgentInfo
from ai.backend.manager.views.sokovan.workload import ResourceRequest

AgentInfoFactory = Callable[..., AgentInfo]


def _request(slots: Mapping[str, str]) -> ResourceRequest:
    return ResourceRequest(
        slots={ResourceSlotName(name): Decimal(amount) for name, amount in slots.items()}
    )


class TestCountUnutilizedCapabilities:
    def test_no_unused_capabilities(self, agent_info_factory: AgentInfoFactory) -> None:
        """All the agent's resource types are requested with non-zero amounts."""
        agent = agent_info_factory(
            agent_id="all-utilized",
            available_slots={
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
                "cuda.shares": Decimal("4"),
            },
        )
        request = _request({"cpu": "2", "mem": "4096", "cuda.shares": "1"})

        assert count_unutilized_capabilities(agent, request) == 0

    def test_with_unused_capabilities(self, agent_info_factory: AgentInfoFactory) -> None:
        """Zero-requested slots with free capacity count as unutilized."""
        agent = agent_info_factory(
            agent_id="unutilized-accelerators",
            available_slots={
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
                "cuda.shares": Decimal("4"),
                "tpu": Decimal("2"),
            },
        )
        request = _request({"cpu": "2", "mem": "4096", "cuda.shares": "0", "tpu": "0"})

        assert count_unutilized_capabilities(agent, request) == 2

    def test_fully_occupied_capability_not_counted(
        self, agent_info_factory: AgentInfoFactory
    ) -> None:
        """A zero-requested slot whose capacity is fully used is not unutilized."""
        agent = agent_info_factory(
            agent_id="gpu-fully-occupied",
            available_slots={
                "cpu": Decimal("8"),
                "mem": Decimal("16384"),
                "cuda.shares": Decimal("4"),
            },
            occupied_slots={"cuda.shares": Decimal("4")},
        )
        request = _request({"cpu": "2", "mem": "4096", "cuda.shares": "0"})

        assert count_unutilized_capabilities(agent, request) == 0


class TestOrderSlotsByPriority:
    def test_basic_priority_order(self) -> None:
        request = _request({"cpu": "1", "mem": "1024", "cuda.shares": "1"})
        result = order_slots_by_priority(request, ["cuda.shares", "cpu", "mem"])
        assert result == [
            ResourceSlotName("cuda.shares"),
            ResourceSlotName("cpu"),
            ResourceSlotName("mem"),
        ]

    def test_missing_priorities_appended_sorted(self) -> None:
        request = _request({"cpu": "1", "mem": "1024", "tpu": "1", "cuda.shares": "1"})
        result = order_slots_by_priority(request, ["cpu"])
        assert result == [
            ResourceSlotName("cpu"),
            ResourceSlotName("cuda.shares"),
            ResourceSlotName("mem"),
            ResourceSlotName("tpu"),
        ]

    def test_empty_priority_list(self) -> None:
        request = _request({"mem": "1024", "cpu": "1"})
        result = order_slots_by_priority(request, [])
        assert result == [ResourceSlotName("cpu"), ResourceSlotName("mem")]

    def test_nonexistent_priorities_ignored(self) -> None:
        request = _request({"cpu": "1"})
        result = order_slots_by_priority(request, ["rocm", "cuda.shares", "cpu"])
        assert result == [ResourceSlotName("cpu")]
