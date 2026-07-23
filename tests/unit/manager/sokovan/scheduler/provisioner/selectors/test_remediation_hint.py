"""Tests for build_remediation_hint() / RemediationHint merging and shortage computation."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from decimal import Decimal

from ai.backend.common.identifier.architecture import ArchName
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import AgentId
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.exceptions import (
    ContainerLimitExceededError,
    InsufficientResourcesError,
    NoAgentsInResourceGroupError,
    NoAvailableAgentError,
    NoCompatibleAgentError,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.types import ResourceRequirements
from ai.backend.manager.views.sokovan.workload import ResourceRequest


def _slots(slots: Mapping[str, str]) -> dict[ResourceSlotName, Decimal]:
    return {ResourceSlotName(name): Decimal(amount) for name, amount in slots.items()}


def _requirement(arch: str = "x86_64") -> ResourceRequirements:
    return ResourceRequirements(
        requested_slots=ResourceRequest(slots=_slots({"cpu": "4"})),
        required_architecture=ArchName(arch),
        container_count=1,
    )


def _insufficient(
    agent_id: str,
    requested: Mapping[str, str],
    available: Mapping[str, str],
) -> InsufficientResourcesError:
    return InsufficientResourcesError(
        agent_id=AgentId(agent_id),
        requested_slots=_slots(requested),
        available_slots=_slots(available),
        insufficient_resources={},
    )


class TestInsufficientResourcesContribution:
    def test_required_reduction_keeps_only_positive_slots(self) -> None:
        err = _insufficient(
            "agent-a",
            requested={"cpu": "4", "mem": "8192"},
            available={"cpu": "1", "mem": "10000"},  # mem is sufficient
        )
        suggestion = err.remediation_hint_contribution()
        # cpu short by 3; mem is not short -> excluded
        assert suggestion.required_reduction == _slots({"cpu": "3"})
        assert suggestion.required_container_reduction is None


class TestContainerLimitContribution:
    def test_sets_container_reduction(self) -> None:
        err = ContainerLimitExceededError(
            agent_id=AgentId("agent-a"), current_count=10, max_count=10
        )
        suggestion = err.remediation_hint_contribution()
        # current 10 >= max 10 -> free 1 to admit one more
        assert suggestion.required_container_reduction == 1
        assert suggestion.required_reduction is None


class TestNoCompatibleAgentSuggestion:
    def test_change_arch_lists_available(self) -> None:
        err = NoCompatibleAgentError(
            resource_requirement=_requirement(arch="aarch64"),
            requirement_index=0,
            available_architectures=["x86_64"],
        )
        suggestion = err.build_remediation_hint()
        assert suggestion.available_archs == ["x86_64"]
        assert suggestion.required_reduction is None
        assert suggestion.available_agent_ids is None


class TestNoAgentsInResourceGroupSuggestion:
    def test_empty_suggestion(self) -> None:
        suggestion = NoAgentsInResourceGroupError(
            ResourceGroupID(uuid.UUID(int=0))
        ).build_remediation_hint()
        assert suggestion.available_archs is None
        assert suggestion.available_agent_ids is None
        assert suggestion.required_reduction is None
        assert suggestion.required_container_reduction is None


class TestNoAvailableAgentSuggestion:
    def test_merges_node_axis_min_reduction(self) -> None:
        err = NoAvailableAgentError(
            resource_requirement=_requirement(),
            requirement_index=0,
            agent_errors={
                AgentId("agent-a"): _insufficient(
                    "agent-a",
                    requested={"cpu": "4"},
                    available={"cpu": "1"},  # deficit 3
                ),
                AgentId("agent-b"): _insufficient(
                    "agent-b",
                    requested={"cpu": "4"},
                    available={"cpu": "3"},  # deficit 1
                ),
            },
        )
        suggestion = err.build_remediation_hint()
        # node-axis MIN -> the smaller reduction (agent-b's deficit)
        assert suggestion.required_reduction == _slots({"cpu": "1"})
        assert suggestion.required_container_reduction is None

    def test_merges_resource_and_container_reductions(self) -> None:
        err = NoAvailableAgentError(
            resource_requirement=_requirement(),
            requirement_index=0,
            agent_errors={
                AgentId("agent-a"): _insufficient(
                    "agent-a", requested={"cpu": "4"}, available={"cpu": "1"}
                ),
                AgentId("agent-b"): ContainerLimitExceededError(
                    agent_id=AgentId("agent-b"), current_count=12, max_count=10
                ),
            },
        )
        suggestion = err.build_remediation_hint()
        # both remediations are surfaced simultaneously (no single discriminator)
        assert suggestion.required_reduction == _slots({"cpu": "3"})
        assert suggestion.required_container_reduction == 3  # 12 - 10 + 1

    def test_surfaces_available_agent_ids(self) -> None:
        err = NoAvailableAgentError(
            resource_requirement=_requirement(),
            requirement_index=0,
            agent_errors={
                AgentId("designated-a"): _insufficient(
                    "designated-a", requested={"cpu": "4"}, available={"cpu": "1"}
                ),
            },
            available_agent_ids=[AgentId("agent-x")],
            designated_agent_ids=[AgentId("designated-a")],
        )
        suggestion = err.build_remediation_hint()
        # the available alternatives are surfaced so a handler can compare them
        # against the (failing) designated agents
        assert suggestion.available_agent_ids == [AgentId("agent-x")]
        assert suggestion.required_reduction == _slots({"cpu": "3"})

    def test_requirement_index_is_carried(self) -> None:
        err = NoAvailableAgentError(
            resource_requirement=_requirement(),
            requirement_index=2,
            agent_errors={},
        )
        assert err.requirement_index == 2
        assert err.resource_requirement.required_architecture == ArchName("x86_64")
