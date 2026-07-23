"""Test dispersed agent selector implementation."""

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
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.dispersed import (
    DispersedAgentSelector,
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


class TestDispersedAgentSelector:
    """Test dispersed agent selector behavior."""

    @pytest.fixture
    def selector(self) -> DispersedAgentSelector:
        """Create a dispersed selector with default priority."""
        return DispersedAgentSelector(agent_selection_resource_priority=["cpu", "mem"])

    def test_selects_agent_with_most_resources(
        self,
        selector: DispersedAgentSelector,
        agents_with_varied_occupancy: list[AgentInfo],
    ) -> None:
        """Dispersed selector prefers agents with more remaining resources."""
        resource_req = _req({"cpu": "1", "mem": "2048"})

        selected = selector.select_tracker_by_strategy(
            _trackers(agents_with_varied_occupancy), resource_req
        )

        assert selected.original_agent.agent_id == AgentId("agent-high")

    def test_prefers_fewer_unutilized_capabilities(
        self,
        selector: DispersedAgentSelector,
        agents_dispersed_gpu_vs_cpu: list[AgentInfo],
    ) -> None:
        """With equal remaining resources, fewer unutilized capabilities win."""
        resource_req = _req({"cpu": "2", "mem": "4096", "cuda.shares": "0"})

        selected = selector.select_tracker_by_strategy(
            _trackers(agents_dispersed_gpu_vs_cpu), resource_req
        )

        assert selected.original_agent.agent_id == AgentId("agent-cpu-only")

    def test_respects_resource_priority_order(
        self,
        agents_for_memory_priority: list[AgentInfo],
    ) -> None:
        """Resource priorities are respected in order."""
        selector = DispersedAgentSelector(agent_selection_resource_priority=["mem", "cpu"])
        resource_req = _req({"cpu": "1", "mem": "1024"})

        selected = selector.select_tracker_by_strategy(
            _trackers(agents_for_memory_priority), resource_req
        )

        # high-mem-low-cpu has more memory remaining (higher priority slot)
        assert selected.original_agent.agent_id == AgentId("high-mem-low-cpu")

    def test_tie_breaking_with_identical_resources(
        self,
        selector: DispersedAgentSelector,
        agents_with_identical_resources: list[AgentInfo],
    ) -> None:
        """Tie-breaking is consistent when agents have identical resources."""
        resource_req = _req({"cpu": "1", "mem": "2048"})
        trackers = _trackers(agents_with_identical_resources)

        selected = selector.select_tracker_by_strategy(trackers, resource_req)

        for _ in range(10):
            result = selector.select_tracker_by_strategy(trackers, resource_req)
            assert result is selected

    def test_handles_mixed_resource_types(
        self,
        selector: DispersedAgentSelector,
        agents_mixed_resource_types: list[AgentInfo],
    ) -> None:
        """CPU-only requests avoid agents holding unutilized accelerators."""
        resource_req = _req({
            "cpu": "4",
            "mem": "8192",
            "cuda.shares": "0",
            "tpu": "0",
        })

        selected = selector.select_tracker_by_strategy(
            _trackers(agents_mixed_resource_types), resource_req
        )

        # cpu-agent has no unutilized accelerator capability
        assert selected.original_agent.agent_id == AgentId("cpu-agent")

    def test_dispersed_opposite_of_concentrated(
        self,
        selector: DispersedAgentSelector,
        agents_concentrated_vs_dispersed: list[AgentInfo],
    ) -> None:
        """Dispersed and concentrated pick opposite ends of the occupancy scale."""
        resource_req = _req({"cpu": "1", "mem": "1024"})
        trackers = _trackers(agents_concentrated_vs_dispersed)

        dispersed_pick = selector.select_tracker_by_strategy(trackers, resource_req)
        concentrated_pick = ConcentratedAgentSelector(
            agent_selection_resource_priority=["cpu", "mem"]
        ).select_tracker_by_strategy(trackers, resource_req)

        assert dispersed_pick.original_agent.agent_id == AgentId("agent-2")
        assert concentrated_pick.original_agent.agent_id == AgentId("agent-1")
