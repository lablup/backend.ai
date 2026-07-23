"""Edge case tests for agent selection."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from decimal import Decimal

import pytest

from ai.backend.common.identifier.architecture import ArchName
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import AgentId, SessionId
from ai.backend.manager.data.session.options import AgentSelectionPolicy
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.concentrated import (
    ConcentratedAgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.dispersed import (
    DispersedAgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.exceptions import (
    BatchAgentSelectionFailedError,
    NoAvailableAgentError,
    NoCompatibleAgentError,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.legacy import LegacyAgentSelector
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.roundrobin import (
    RoundRobinAgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
    AgentSelectionCriteria,
    AgentSelector,
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


def _criteria(requirements: list[ResourceRequirements]) -> AgentSelectionCriteria:
    return AgentSelectionCriteria(
        session_id=SessionId(uuid.uuid4()),
        resource_group_id=ResourceGroupID(uuid.UUID(int=0)),
        requirements=requirements,
        agent_selection_policy=AgentSelectionPolicy.STRICT,
        designated_agent_ids=None,
    )


def _trackers(agents: list[AgentInfo]) -> list[AgentStateTracker]:
    return [AgentStateTracker(original_agent=agent) for agent in agents]


class TestSelectorEdgeCases:
    """Edge cases across strategies and the batch selection path."""

    def test_zero_resource_values(
        self,
        agents_with_varied_occupancy: list[AgentInfo],
    ) -> None:
        """An all-zero request is satisfiable by any agent."""
        selector = ConcentratedAgentSelector(agent_selection_resource_priority=["cpu", "mem"])
        resource_req = _req({"cpu": "0", "mem": "0"})

        selected = selector.select_tracker_by_strategy(
            _trackers(agents_with_varied_occupancy), resource_req
        )
        assert selected is not None

    async def test_missing_resource_type_fails_selection(
        self,
        agents_with_varied_occupancy: list[AgentInfo],
    ) -> None:
        """Requesting a slot no agent has is treated as zero availability."""
        criteria = _criteria([_req({"cpu": "1", "npu": "1"})])
        selector = AgentSelector(
            ConcentratedAgentSelector(agent_selection_resource_priority=["cpu", "mem"])
        )

        with pytest.raises(BatchAgentSelectionFailedError) as exc_info:
            await selector.select_agents_for_batch_requirements(
                _trackers(agents_with_varied_occupancy), criteria, NO_LIMIT
            )
        assert isinstance(exc_info.value.errors[0], NoAvailableAgentError)

    async def test_unknown_architecture_fails_with_arch_error(
        self,
        agents_with_varied_occupancy: list[AgentInfo],
    ) -> None:
        """An architecture no agent provides raises NoCompatibleAgentError."""
        criteria = _criteria([_req({"cpu": "1"}, arch="riscv64")])
        selector = AgentSelector(
            ConcentratedAgentSelector(agent_selection_resource_priority=["cpu", "mem"])
        )

        with pytest.raises(BatchAgentSelectionFailedError) as exc_info:
            await selector.select_agents_for_batch_requirements(
                _trackers(agents_with_varied_occupancy), criteria, NO_LIMIT
            )
        error = exc_info.value.errors[0]
        assert isinstance(error, NoCompatibleAgentError)
        assert error.build_remediation_hint().available_archs == ["x86_64"]

    def test_extremely_large_resource_values(
        self,
        agents_normal_vs_huge: list[AgentInfo],
    ) -> None:
        """Huge capacities do not break the strategy comparison."""
        selector = DispersedAgentSelector(agent_selection_resource_priority=["cpu", "mem"])
        resource_req = _req({"cpu": "1", "mem": "1024"})

        selected = selector.select_tracker_by_strategy(
            _trackers(agents_normal_vs_huge), resource_req
        )
        assert selected.original_agent.agent_id == AgentId("huge")

    def test_single_agent_all_strategies(
        self,
        single_agent: list[AgentInfo],
    ) -> None:
        """Every strategy returns the only candidate."""
        resource_req = _req({"cpu": "1", "mem": "1024"})
        strategies = [
            ConcentratedAgentSelector(agent_selection_resource_priority=["cpu", "mem"]),
            DispersedAgentSelector(agent_selection_resource_priority=["cpu", "mem"]),
            LegacyAgentSelector(agent_selection_resource_priority=["cpu", "mem"]),
            RoundRobinAgentSelector(),
        ]

        for strategy in strategies:
            selected = strategy.select_tracker_by_strategy(_trackers(single_agent), resource_req)
            assert selected.original_agent.agent_id == AgentId("lonely-agent")

    async def test_all_agents_fully_occupied(
        self,
        agents_all_fully_occupied: list[AgentInfo],
    ) -> None:
        """When no agent has remaining capacity the batch fails."""
        criteria = _criteria([_req({"cpu": "1", "mem": "1024"})])
        selector = AgentSelector(
            ConcentratedAgentSelector(agent_selection_resource_priority=["cpu", "mem"])
        )

        with pytest.raises(BatchAgentSelectionFailedError):
            await selector.select_agents_for_batch_requirements(
                _trackers(agents_all_fully_occupied), criteria, NO_LIMIT
            )

    def test_priority_with_nonexistent_resources(
        self,
        agents_with_varied_occupancy: list[AgentInfo],
    ) -> None:
        """Priority entries for slots not requested are simply ignored."""
        selector = ConcentratedAgentSelector(
            agent_selection_resource_priority=["nonexistent", "cpu", "mem"]
        )
        resource_req = _req({"cpu": "1", "mem": "1024"})

        selected = selector.select_tracker_by_strategy(
            _trackers(agents_with_varied_occupancy), resource_req
        )
        assert selected.original_agent.agent_id == AgentId("agent-low")

    def test_special_resource_names(
        self,
        agents_with_special_resource_names: list[AgentInfo],
    ) -> None:
        """Slot names with special characters flow through the strategies."""
        selector = ConcentratedAgentSelector(agent_selection_resource_priority=["cpu", "mem"])
        resource_req = _req({
            "cpu": "1",
            "mem": "1024",
            "custom.resource-name_123": "10",
            "another/special@resource": "5",
        })

        selected = selector.select_tracker_by_strategy(
            _trackers(agents_with_special_resource_names), resource_req
        )
        assert selected.original_agent.agent_id == AgentId("special")
