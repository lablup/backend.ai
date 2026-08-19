"""Integration-style comparisons across selector strategies."""

from __future__ import annotations

import time
from collections.abc import Mapping
from decimal import Decimal

from ai.backend.common.identifier.architecture import ArchName
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import AgentId
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.concentrated import (
    ConcentratedAgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.dispersed import (
    DispersedAgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.legacy import LegacyAgentSelector
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


class TestSelectorIntegration:
    """Compare strategies over the same candidate pools."""

    def test_strategy_comparison_basic(
        self,
        agents_for_strategy_comparison: list[AgentInfo],
    ) -> None:
        """Concentrated and dispersed pick opposite occupancy extremes."""
        resource_req = _req({"cpu": "1", "mem": "2048"})
        trackers = _trackers(agents_for_strategy_comparison)

        concentrated_pick = ConcentratedAgentSelector(
            agent_selection_resource_priority=["cpu", "mem"]
        ).select_tracker_by_strategy(trackers, resource_req)
        dispersed_pick = DispersedAgentSelector(
            agent_selection_resource_priority=["cpu", "mem"]
        ).select_tracker_by_strategy(trackers, resource_req)
        legacy_pick = LegacyAgentSelector(
            agent_selection_resource_priority=["cpu", "mem"]
        ).select_tracker_by_strategy(trackers, resource_req)

        assert concentrated_pick.original_agent.agent_id == AgentId("agent-1")
        assert dispersed_pick.original_agent.agent_id == AgentId("agent-3")
        # Legacy prefers more remaining resources like dispersed
        assert legacy_pick.original_agent.agent_id == AgentId("agent-3")

    def test_mixed_resource_types_comparison(
        self,
        agents_mixed_resource_types: list[AgentInfo],
    ) -> None:
        """All strategies avoid agents holding unutilized accelerators."""
        resource_req = _req({
            "cpu": "2",
            "mem": "4096",
            "cuda.shares": "0",
            "tpu": "0",
        })
        trackers = _trackers(agents_mixed_resource_types)

        for strategy in (
            ConcentratedAgentSelector(agent_selection_resource_priority=["cpu", "mem"]),
            DispersedAgentSelector(agent_selection_resource_priority=["cpu", "mem"]),
            LegacyAgentSelector(agent_selection_resource_priority=["cpu", "mem"]),
        ):
            selected = strategy.select_tracker_by_strategy(trackers, resource_req)
            assert selected.original_agent.agent_id == AgentId("cpu-agent")

    def test_large_scale_performance(
        self,
        agents_for_large_scale_performance: list[AgentInfo],
    ) -> None:
        """Selection over 100 agents stays fast and deterministic."""
        resource_req = _req({"cpu": "2", "mem": "4096"})
        trackers = _trackers(agents_for_large_scale_performance)
        selector = ConcentratedAgentSelector(agent_selection_resource_priority=["cpu", "mem"])

        started = time.perf_counter()
        first = selector.select_tracker_by_strategy(trackers, resource_req)
        for _ in range(10):
            assert selector.select_tracker_by_strategy(trackers, resource_req) is first
        elapsed = time.perf_counter() - started

        assert elapsed < 5.0
