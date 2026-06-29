"""Tests for AgentSelectionError.build_suggestion() and shortage computation."""

from __future__ import annotations

import uuid
from decimal import Decimal

from ai.backend.common.types import AgentId, KernelId, ResourceSlot
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.exceptions import (
    ContainerLimitExceededError,
    InsufficientResourcesError,
    NoAgentsInResourceGroupError,
    NoAvailableAgentError,
    NoCompatibleAgentError,
    SuggestionKind,
)


def _insufficient(
    agent_id: str,
    requested: dict[str, str],
    available: dict[str, str],
) -> InsufficientResourcesError:
    requested_slots = ResourceSlot({k: Decimal(v) for k, v in requested.items()})
    available_slots = ResourceSlot({k: Decimal(v) for k, v in available.items()})
    return InsufficientResourcesError(
        agent_id=AgentId(agent_id),
        requested_slots=requested_slots,
        available_slots=available_slots,
        occupied_slots=ResourceSlot({}),
        insufficient_resources={},
    )


class TestInsufficientResourcesDeficit:
    def test_deficit_keeps_only_positive_slots(self) -> None:
        err = _insufficient(
            "agent-a",
            requested={"cpu": "4", "mem": "8192"},
            available={"cpu": "1", "mem": "10000"},  # mem is sufficient
        )
        # cpu short by 3; mem is not short -> excluded
        assert err.deficit() == ResourceSlot({"cpu": Decimal("3")})


class TestNoCompatibleAgentSuggestion:
    def test_change_arch_lists_available(self) -> None:
        err = NoCompatibleAgentError(
            required_architecture="aarch64",
            available_architectures=["x86_64"],
        )
        suggestion = err.build_suggestion()
        assert suggestion.kind == SuggestionKind.CHANGE_ARCH
        assert suggestion.available_archs == ["x86_64"]
        assert suggestion.required_reduction is None


class TestNoAgentsInResourceGroupSuggestion:
    def test_none(self) -> None:
        err = NoAgentsInResourceGroupError("default")
        assert err.build_suggestion().kind == SuggestionKind.NONE


class TestNoAvailableAgentSuggestion:
    def test_reduce_resource_picks_node_axis_min(self) -> None:
        kernel_id = KernelId(uuid.uuid4())
        err = NoAvailableAgentError(
            kernel_ids=[kernel_id],
            required_architecture="x86_64",
            requested_slots=ResourceSlot({"cpu": Decimal("4")}),
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
        suggestion = err.build_suggestion()
        assert suggestion.kind == SuggestionKind.REDUCE_RESOURCE
        # node-axis MIN -> the smaller reduction (agent-b's deficit)
        assert suggestion.required_reduction == ResourceSlot({"cpu": Decimal("1")})

    def test_all_container_limited_yields_reduce_container(self) -> None:
        kernel_id = KernelId(uuid.uuid4())
        err = NoAvailableAgentError(
            kernel_ids=[kernel_id],
            required_architecture="x86_64",
            requested_slots=ResourceSlot({"cpu": Decimal("4")}),
            agent_errors={
                AgentId("agent-a"): ContainerLimitExceededError(
                    agent_id=AgentId("agent-a"),
                    current_count=10,
                    max_count=10,
                ),
            },
        )
        suggestion = err.build_suggestion()
        assert suggestion.kind == SuggestionKind.REDUCE_CONTAINER
        assert suggestion.required_reduction is None

    def test_designated_failure_lists_agents(self) -> None:
        kernel_id = KernelId(uuid.uuid4())
        err = NoAvailableAgentError(
            kernel_ids=[kernel_id],
            required_architecture="x86_64",
            requested_slots=ResourceSlot({"cpu": Decimal("4")}),
            agent_errors={
                AgentId("designated-a"): _insufficient(
                    "designated-a", requested={"cpu": "4"}, available={"cpu": "1"}
                ),
            },
            designated_agent_ids=[AgentId("designated-a")],
        )
        suggestion = err.build_suggestion()
        assert suggestion.kind == SuggestionKind.CHANGE_DESIGNATED_AGENT
        assert suggestion.available_agent_ids == [AgentId("designated-a")]
        # a reduction is still offered since the designated agent only lacks resources
        assert suggestion.required_reduction == ResourceSlot({"cpu": Decimal("1")})
