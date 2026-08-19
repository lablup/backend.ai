"""Test round-robin agent selector implementation."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from ai.backend.common.identifier.architecture import ArchName
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import AgentId
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.roundrobin import (
    RoundRobinAgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.tracker import AgentStateTracker
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.types import ResourceRequirements
from ai.backend.manager.views.sokovan.agent import AgentInfo
from ai.backend.manager.views.sokovan.workload import ResourceRequest


def _req(
    slots: Mapping[str, str] | None = None,
    arch: str = "x86_64",
    containers: int = 1,
) -> ResourceRequirements:
    if slots is None:
        slots = {"cpu": "1", "mem": "1024"}
    return ResourceRequirements(
        requested_slots=ResourceRequest(
            slots={ResourceSlotName(name): Decimal(amount) for name, amount in slots.items()}
        ),
        required_architecture=ArchName(arch),
        container_count=containers,
    )


def _trackers(agents: list[AgentInfo]) -> list[AgentStateTracker]:
    return [AgentStateTracker(original_agent=agent) for agent in agents]


class TestRoundRobinAgentSelector:
    """Test round-robin agent selector behavior."""

    def test_sequential_selection(
        self,
        agents_for_roundrobin_sequential: list[AgentInfo],
    ) -> None:
        """Selections rotate through the ID-sorted agents in order."""
        selector = RoundRobinAgentSelector()
        trackers = _trackers(agents_for_roundrobin_sequential)
        resource_req = _req()

        picks = [
            selector.select_tracker_by_strategy(trackers, resource_req).original_agent.agent_id
            for _ in range(3)
        ]

        assert picks == [AgentId("agent-a"), AgentId("agent-b"), AgentId("agent-c")]

    def test_index_wrapping(
        self,
        agents_for_roundrobin_sequential: list[AgentInfo],
    ) -> None:
        """The rotation index wraps around the candidate count."""
        selector = RoundRobinAgentSelector()
        trackers = _trackers(agents_for_roundrobin_sequential)
        resource_req = _req()

        picks = [
            selector.select_tracker_by_strategy(trackers, resource_req).original_agent.agent_id
            for _ in range(6)
        ]

        assert picks[:3] == picks[3:]

    def test_consistent_ordering_by_agent_id(
        self,
        agents_for_roundrobin_unsorted: list[AgentInfo],
    ) -> None:
        """Candidates are sorted by agent ID regardless of the input order."""
        selector = RoundRobinAgentSelector()
        trackers = _trackers(agents_for_roundrobin_unsorted)
        resource_req = _req()

        picks = [
            selector.select_tracker_by_strategy(trackers, resource_req).original_agent.agent_id
            for _ in range(3)
        ]

        assert picks == [AgentId("alpha"), AgentId("beta"), AgentId("zebra")]

    def test_single_agent(
        self,
        single_agent: list[AgentInfo],
    ) -> None:
        """A single candidate is always selected."""
        selector = RoundRobinAgentSelector()
        trackers = _trackers(single_agent)
        resource_req = _req()

        for _ in range(3):
            selected = selector.select_tracker_by_strategy(trackers, resource_req)
            assert selected.original_agent.agent_id == AgentId("lonely-agent")

    def test_ignores_resource_availability(
        self,
        agents_for_roundrobin_varied_resources: list[AgentInfo],
    ) -> None:
        """The strategy does not consider remaining resources at all."""
        selector = RoundRobinAgentSelector()
        trackers = _trackers(agents_for_roundrobin_varied_resources)
        resource_req = _req()

        picks = {
            selector.select_tracker_by_strategy(trackers, resource_req).original_agent.agent_id
            for _ in range(2)
        }

        # Both agents get a turn although their free resources differ wildly
        assert picks == {AgentId("agent-empty"), AgentId("agent-full")}

    def test_fairness_over_multiple_selections(
        self,
        agents_for_roundrobin_fairness: list[AgentInfo],
    ) -> None:
        """Repeated selections distribute evenly across the candidates."""
        selector = RoundRobinAgentSelector()
        trackers = _trackers(agents_for_roundrobin_fairness)
        resource_req = _req()

        counts: dict[AgentId, int] = {}
        for _ in range(20):
            selected = selector.select_tracker_by_strategy(trackers, resource_req)
            agent_id = selected.original_agent.agent_id
            counts[agent_id] = counts.get(agent_id, 0) + 1

        assert all(count == 4 for count in counts.values())
        assert len(counts) == 5
