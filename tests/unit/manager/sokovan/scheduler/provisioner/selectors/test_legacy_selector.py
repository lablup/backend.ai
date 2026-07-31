"""Test legacy agent selector implementation."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

import pytest

from ai.backend.common.identifier.architecture import ArchName
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import AgentId
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


class TestLegacyAgentSelector:
    """Test legacy agent selector behavior."""

    @pytest.fixture
    def selector(self) -> LegacyAgentSelector:
        """Create a legacy selector with default priority."""
        return LegacyAgentSelector(agent_selection_resource_priority=["cpu", "mem"])

    def test_prefers_fewer_unutilized_capabilities_first(
        self,
        selector: LegacyAgentSelector,
        agents_gpu_vs_cpu_only: list[AgentInfo],
    ) -> None:
        """Unutilized capability count dominates the sort key."""
        resource_req = _req({"cpu": "2", "mem": "4096", "cuda.shares": "0"})

        selected = selector.select_tracker_by_strategy(
            _trackers(agents_gpu_vs_cpu_only), resource_req
        )

        assert selected.original_agent.agent_id == AgentId("agent-cpu-only")

    def test_breaks_ties_with_resource_availability(
        self,
        selector: LegacyAgentSelector,
        agents_for_resource_tie_breaking: list[AgentInfo],
    ) -> None:
        """With equal capability counts, more remaining resources win."""
        resource_req = _req({"cpu": "1", "mem": "2048"})

        selected = selector.select_tracker_by_strategy(
            _trackers(agents_for_resource_tie_breaking), resource_req
        )

        assert selected.original_agent.agent_id == AgentId("agent-high-resources")

    def test_respects_resource_priority_order(
        self,
        agents_for_gpu_priority: list[AgentInfo],
    ) -> None:
        """The GPU-first priority order drives the tie-breaking."""
        selector = LegacyAgentSelector(
            agent_selection_resource_priority=["cuda.shares", "cpu", "mem"]
        )
        resource_req = _req({"cpu": "1", "mem": "2048", "cuda.shares": "0.5"})

        selected = selector.select_tracker_by_strategy(
            _trackers(agents_for_gpu_priority), resource_req
        )

        # Legacy prefers MORE remaining resources: high-gpu has 3 GPU remaining
        assert selected.original_agent.agent_id == AgentId("high-gpu")

    def test_handles_partially_utilized_resources(
        self,
        selector: LegacyAgentSelector,
        agents_gpu_partially_used: list[AgentInfo],
    ) -> None:
        """Any free capacity on a zero-requested slot counts as unutilized.

        Both agents therefore tie on the capability count, and the
        tie-break falls to remaining resources (gpu-unused has more GPU).
        """
        resource_req = _req({"cpu": "2", "mem": "4096", "cuda.shares": "0"})

        selected = selector.select_tracker_by_strategy(
            _trackers(agents_gpu_partially_used), resource_req
        )

        assert selected.original_agent.agent_id == AgentId("gpu-unused")

    def test_handles_custom_resource_types(
        self,
        agents_with_custom_accelerator: list[AgentInfo],
    ) -> None:
        """Custom accelerator slot names participate in the priority order."""
        selector = LegacyAgentSelector(
            agent_selection_resource_priority=["custom.accelerator", "cpu", "mem"]
        )
        resource_req = _req({
            "cpu": "2",
            "mem": "4096",
            "custom.accelerator": "1",
        })

        selected = selector.select_tracker_by_strategy(
            _trackers(agents_with_custom_accelerator), resource_req
        )

        # custom-rich has 8 custom.accelerator remaining vs custom-poor's 1
        assert selected.original_agent.agent_id == AgentId("custom-rich")
