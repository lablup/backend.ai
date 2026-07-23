"""Test batch agent selection (``AgentSelector.select_agents_for_batch_requirements``)."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from decimal import Decimal

import pytest

from ai.backend.common.identifier.architecture import ArchName
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import AgentId, ClusterMode, SessionId
from ai.backend.manager.data.session.options import AgentSelectionPolicy
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.concentrated import (
    ConcentratedAgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.dispersed import (
    DispersedAgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.exceptions import (
    BatchAgentSelectionFailedError,
    NoAgentsInResourceGroupError,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
    AgentSelectionCriteria,
    AgentSelector,
    PlacementPlan,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.tracker import AgentStateTracker
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.types import ResourceRequirements
from ai.backend.manager.views.sokovan.agent import AgentInfo, AgentLimit
from ai.backend.manager.views.sokovan.workload import ResourceRequest

NO_LIMIT = AgentLimit(max_container_count=None)


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


def _criteria(
    requirements: list[ResourceRequirements],
    *,
    policy: AgentSelectionPolicy = AgentSelectionPolicy.STRICT,
    designated_agent_ids: list[AgentId] | None = None,
) -> AgentSelectionCriteria:
    return AgentSelectionCriteria(
        session_id=SessionId(uuid.uuid4()),
        resource_group_id=ResourceGroupID(uuid.UUID(int=0)),
        requirements=requirements,
        agent_selection_policy=policy,
        designated_agent_ids=designated_agent_ids,
    )


def _trackers(agents: list[AgentInfo]) -> list[AgentStateTracker]:
    return [AgentStateTracker(original_agent=agent) for agent in agents]


def _concentrated() -> AgentSelector:
    return AgentSelector(
        ConcentratedAgentSelector(agent_selection_resource_priority=["cpu", "mem"])
    )


class TestAgentSelectionWithResources:
    """Test agent selection using ResourceRequirements."""

    async def test_single_node_selection_with_aggregated_resources(
        self,
        agents_for_resource_requirements_test: list[AgentInfo],
    ) -> None:
        """Single-node placement aggregates the per-kernel requirements."""
        plan = PlacementPlan.from_items(
            [
                _req({"cpu": "4", "mem": "8192"}),
                _req({"cpu": "2", "mem": "4096"}),
            ],
            ClusterMode.SINGLE_NODE,
        )
        criteria = _criteria(plan.requirements())

        # Total requested: 6 CPU, 12288 mem -> only agent-high fits
        selections = await _concentrated().select_agents_for_batch_requirements(
            _trackers(agents_for_resource_requirements_test), criteria, NO_LIMIT
        )

        assert len(selections) == 1
        assert selections[0].selected_agent.agent_id == AgentId("agent-high")

    async def test_multi_node_selection_individual_resources(
        self,
        agents_for_resource_requirements_test: list[AgentInfo],
    ) -> None:
        """Multi-node placement keeps one selection per kernel requirement."""
        plan = PlacementPlan.from_items(
            [
                _req({"cpu": "1", "mem": "2048"}),
                _req({"cpu": "3", "mem": "6144"}),
            ],
            ClusterMode.MULTI_NODE,
        )
        criteria = _criteria(plan.requirements())
        selector = AgentSelector(
            DispersedAgentSelector(agent_selection_resource_priority=["cpu", "mem"])
        )

        selections = await selector.select_agents_for_batch_requirements(
            _trackers(agents_for_resource_requirements_test), criteria, NO_LIMIT
        )

        assert len(selections) == 2
        assert all(sel.selected_agent.agent_id is not None for sel in selections)

    async def test_designated_agent_strict_fails_without_capacity(
        self,
        agents_for_designated_agent_test: list[AgentInfo],
    ) -> None:
        """STRICT designation fails when the designated agent lacks resources."""
        criteria = _criteria(
            [_req({"cpu": "4", "mem": "8192"})],
            policy=AgentSelectionPolicy.STRICT,
            designated_agent_ids=[AgentId("designated")],
        )

        with pytest.raises(BatchAgentSelectionFailedError) as exc_info:
            await _concentrated().select_agents_for_batch_requirements(
                _trackers(agents_for_designated_agent_test), criteria, NO_LIMIT
            )

        assert len(exc_info.value.errors) == 1
        message = exc_info.value.errors[0].extra_msg or ""
        assert "no designated agent is compatible" in message
        assert "designated agent 'designated'" in message
        assert "insufficient resources" in message
        # Aggregated detail lines must be split with newlines, not "; ".
        assert "; " not in message
        assert "\n" in message

    async def test_designated_agent_preferred_falls_back(
        self,
        agents_for_designated_agent_test: list[AgentInfo],
    ) -> None:
        """PREFERRED designation falls back to other compatible agents."""
        criteria = _criteria(
            [_req({"cpu": "4", "mem": "8192"})],
            policy=AgentSelectionPolicy.PREFERRED,
            designated_agent_ids=[AgentId("designated")],
        )

        selections = await _concentrated().select_agents_for_batch_requirements(
            _trackers(agents_for_designated_agent_test), criteria, NO_LIMIT
        )

        assert len(selections) == 1
        assert selections[0].selected_agent.agent_id == AgentId("other")

    async def test_designated_agent_with_capacity_is_selected(
        self,
        agents_for_designated_agent_test: list[AgentInfo],
    ) -> None:
        """A designated agent with capacity takes precedence over the strategy."""
        criteria = _criteria(
            [_req({"cpu": "1", "mem": "1024"})],
            policy=AgentSelectionPolicy.STRICT,
            designated_agent_ids=[AgentId("designated")],
        )

        selections = await _concentrated().select_agents_for_batch_requirements(
            _trackers(agents_for_designated_agent_test), criteria, NO_LIMIT
        )

        assert len(selections) == 1
        assert selections[0].selected_agent.agent_id == AgentId("designated")

    async def test_container_limit_with_resource_requirements(
        self,
        agents_for_container_limit_test: list[AgentInfo],
    ) -> None:
        """Agents at the container limit are excluded from selection."""
        criteria = _criteria([_req({"cpu": "2", "mem": "4096"})])

        selections = await _concentrated().select_agents_for_batch_requirements(
            _trackers(agents_for_container_limit_test),
            criteria,
            AgentLimit(max_container_count=10),
        )

        assert len(selections) == 1
        assert selections[0].selected_agent.agent_id == AgentId("available")

    async def test_architecture_requirement_is_enforced(
        self,
        agents_for_architecture_test: list[AgentInfo],
    ) -> None:
        """Only agents matching the required architecture are considered."""
        criteria = _criteria([_req({"cpu": "2", "mem": "4096"}, arch="aarch64")])

        selections = await _concentrated().select_agents_for_batch_requirements(
            _trackers(agents_for_architecture_test), criteria, NO_LIMIT
        )

        assert len(selections) == 1
        assert selections[0].selected_agent.agent_id == AgentId("arm")

    async def test_empty_requirements_returns_empty(
        self,
        agents_for_resource_requirements_test: list[AgentInfo],
    ) -> None:
        """A session with no kernels yields an empty selection list."""
        criteria = _criteria([])

        selections = await _concentrated().select_agents_for_batch_requirements(
            _trackers(agents_for_resource_requirements_test), criteria, NO_LIMIT
        )

        assert selections == []

    async def test_no_trackers_raises_resource_group_error(self) -> None:
        """An empty agent pool raises NoAgentsInResourceGroupError."""
        criteria = _criteria([_req({"cpu": "1", "mem": "1024"})])

        with pytest.raises(NoAgentsInResourceGroupError):
            await _concentrated().select_agents_for_batch_requirements([], criteria, NO_LIMIT)

    async def test_success_commits_allocations_into_trackers(
        self,
        agents_for_designated_agent_test: list[AgentInfo],
    ) -> None:
        """A successful batch folds the allocation into the tracker state."""
        trackers = _trackers(agents_for_designated_agent_test)
        criteria = _criteria([_req({"cpu": "4", "mem": "8192"})])

        selections = await _concentrated().select_agents_for_batch_requirements(
            trackers, criteria, NO_LIMIT
        )

        selected_id = selections[0].selected_agent.agent_id
        selected_tracker = next(t for t in trackers if t.original_agent.agent_id == selected_id)
        assert selected_tracker.committed_slots[ResourceSlotName("cpu")] == Decimal("4")
        assert selected_tracker.committed_containers == 1
        assert selected_tracker.pending_slots == {}

    async def test_failure_rolls_back_pending_allocations(
        self,
        agents_for_resource_requirements_test: list[AgentInfo],
    ) -> None:
        """All-or-nothing: a partially placeable batch leaves trackers unchanged."""
        trackers = _trackers(agents_for_resource_requirements_test)
        criteria = _criteria([
            _req({"cpu": "1", "mem": "1024"}),  # placeable
            _req({"cpu": "100", "mem": "999999"}),  # impossible
        ])

        with pytest.raises(BatchAgentSelectionFailedError):
            await _concentrated().select_agents_for_batch_requirements(trackers, criteria, NO_LIMIT)

        for tracker in trackers:
            assert tracker.pending_slots == {}
            assert tracker.committed_slots == {}
            assert tracker.committed_containers == 0
