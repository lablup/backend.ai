"""Test concentrated agent selector implementation."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

import pytest

from ai.backend.common.identifier.architecture import ArchName
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import AgentId
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.concentrated import (
    ConcentratedAgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.tracker import AgentStateTracker
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.types import ResourceRequirements
from ai.backend.manager.views.sokovan.agent import AgentInfo
from ai.backend.manager.views.sokovan.workload import ResourceRequest


def _req(
    slots: Mapping[str, str],
    arch: str = "x86_64",
    containers: int = 1,
) -> ResourceRequirements:
    return ResourceRequirements(
        requested_slots=ResourceRequest(
            slots={ResourceSlotName(name): Decimal(amount) for name, amount in slots.items()}
        ),
        required_architecture=ArchName(arch),
        container_count=containers,
    )


def _trackers(agents: list[AgentInfo]) -> list[AgentStateTracker]:
    return [AgentStateTracker(original_agent=agent) for agent in agents]


class TestConcentratedAgentSelector:
    """Test concentrated agent selector behavior."""

    @pytest.fixture
    def selector(self) -> ConcentratedAgentSelector:
        """Create a concentrated selector with default priority."""
        return ConcentratedAgentSelector(agent_selection_resource_priority=["cpu", "mem"])

    def test_selects_agent_with_least_resources(
        self,
        selector: ConcentratedAgentSelector,
        agents_with_varied_occupancy: list[AgentInfo],
    ) -> None:
        """Concentrated selector prefers agents with less remaining resources."""
        resource_req = _req({"cpu": "1", "mem": "2048"})

        selected = selector.select_tracker_by_strategy(
            _trackers(agents_with_varied_occupancy), resource_req
        )

        assert selected.original_agent.agent_id == AgentId("agent-low")

    def test_prefers_fewer_unutilized_capabilities(
        self,
        selector: ConcentratedAgentSelector,
        agents_gpu_vs_cpu_only: list[AgentInfo],
    ) -> None:
        """Agents with fewer unutilized resource types win."""
        # Request only CPU and memory (explicitly no GPU)
        resource_req = _req({"cpu": "2", "mem": "4096", "cuda.shares": "0"})

        selected = selector.select_tracker_by_strategy(
            _trackers(agents_gpu_vs_cpu_only), resource_req
        )

        # agent-cpu-only has no unutilized GPU capability
        assert selected.original_agent.agent_id == AgentId("agent-cpu-only")

    def test_respects_resource_priority_order(
        self,
        agents_for_memory_priority: list[AgentInfo],
    ) -> None:
        """Resource priorities are respected in order."""
        selector = ConcentratedAgentSelector(agent_selection_resource_priority=["mem", "cpu"])
        resource_req = _req({"cpu": "1", "mem": "1024"})

        selected = selector.select_tracker_by_strategy(
            _trackers(agents_for_memory_priority), resource_req
        )

        # low-mem-high-cpu has less memory remaining (higher priority slot)
        assert selected.original_agent.agent_id == AgentId("low-mem-high-cpu")

    def test_tie_breaking_with_identical_resources(
        self,
        selector: ConcentratedAgentSelector,
        agents_with_identical_resources: list[AgentInfo],
    ) -> None:
        """Tie-breaking is consistent when agents have identical resources."""
        resource_req = _req({"cpu": "1", "mem": "2048"})
        trackers = _trackers(agents_with_identical_resources)

        selected = selector.select_tracker_by_strategy(trackers, resource_req)
        assert selected.original_agent.agent_id in {
            AgentId("agent-a"),
            AgentId("agent-b"),
            AgentId("agent-c"),
        }

        for _ in range(10):
            result = selector.select_tracker_by_strategy(trackers, resource_req)
            assert result is selected

    def test_handles_agents_with_gpu_resources(
        self,
        selector: ConcentratedAgentSelector,
        agents_with_gpu_resources: list[AgentInfo],
    ) -> None:
        """Selection works with GPU slots in the request."""
        resource_req = _req({"cpu": "2", "mem": "4096", "cuda.shares": "1"})

        selected = selector.select_tracker_by_strategy(
            _trackers(agents_with_gpu_resources), resource_req
        )

        # gpu-busy has less remaining resources
        assert selected.original_agent.agent_id == AgentId("gpu-busy")

    def test_custom_resource_priority(
        self,
        agents_for_gpu_priority: list[AgentInfo],
    ) -> None:
        """A GPU-first priority order drives the selection."""
        selector = ConcentratedAgentSelector(
            agent_selection_resource_priority=["cuda.shares", "cpu", "mem"]
        )
        resource_req = _req({"cpu": "1", "mem": "2048", "cuda.shares": "0.5"})

        selected = selector.select_tracker_by_strategy(
            _trackers(agents_for_gpu_priority), resource_req
        )

        # low-gpu has less GPU remaining, which is the highest priority slot
        assert selected.original_agent.agent_id == AgentId("low-gpu")

    def test_pending_allocation_changes_selection(
        self,
        selector: ConcentratedAgentSelector,
        agents_with_varied_occupancy: list[AgentInfo],
    ) -> None:
        """In-batch allocations tracked on a tracker affect subsequent picks."""
        resource_req = _req({"cpu": "1", "mem": "2048"})
        trackers = _trackers(agents_with_varied_occupancy)

        # Fill up agent-low in-batch so agent-medium becomes the least-remaining
        low = next(t for t in trackers if t.original_agent.agent_id == AgentId("agent-low"))
        low.apply_diff(
            ResourceRequest(
                slots={
                    ResourceSlotName("cpu"): Decimal("2"),
                    ResourceSlotName("mem"): Decimal("4096"),
                }
            ),
            containers=1,
        )

        remaining_low = low.remaining_slots()
        assert remaining_low[ResourceSlotName("cpu")] == Decimal("0")

        candidates = [t for t in trackers if t is not low]
        selected = selector.select_tracker_by_strategy(candidates, resource_req)
        assert selected.original_agent.agent_id == AgentId("agent-medium")
