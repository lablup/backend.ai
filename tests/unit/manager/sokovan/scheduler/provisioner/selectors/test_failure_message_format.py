"""Format-level tests for scheduling failure messages (BA-6149).

These tests pin down the user-facing layout of error messages so that future
refactors do not accidentally regress to ";"-joined single-line aggregates.
Golden assertions compare entire messages to lock down the exact layout.
"""

from __future__ import annotations

import json
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
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.exceptions import (
    BatchAgentSelectionFailedError,
    ContainerLimitExceededError,
    InsufficientResourcesError,
    NoAgentsInResourceGroupError,
    NoAvailableAgentError,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
    AgentSelectionCriteria,
    AgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.tracker import AgentStateTracker
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.types import ResourceRequirements
from ai.backend.manager.sokovan.scheduler.provisioner.validators.exceptions import (
    ConcurrencyLimitExceeded,
    DependenciesNotSatisfied,
    MultipleValidationErrors,
)
from ai.backend.manager.views.sokovan.agent import (
    AgentInfo,
    AgentLimit,
    AgentResource,
    SlotResource,
)
from ai.backend.manager.views.sokovan.workload import ResourceRequest


def _slots(slots: Mapping[str, str]) -> dict[ResourceSlotName, Decimal]:
    return {ResourceSlotName(name): Decimal(amount) for name, amount in slots.items()}


def _req(
    slots: Mapping[str, str],
    arch: str = "x86_64",
    containers: int = 1,
) -> ResourceRequirements:
    return ResourceRequirements(
        requested_slots=ResourceRequest(slots=_slots(slots)),
        required_architecture=ArchName(arch),
        container_count=containers,
    )


def _agent(
    agent_id: str,
    capacities: Mapping[str, str],
    container_count: int = 0,
) -> AgentInfo:
    return AgentInfo(
        agent_id=AgentId(agent_id),
        agent_addr=f"{agent_id}:6001",
        architecture=ArchName("x86_64"),
        resources=AgentResource(
            slots={
                ResourceSlotName(name): SlotResource(
                    capacity=Decimal(amount), reserved=Decimal(0), used=Decimal(0)
                )
                for name, amount in capacities.items()
            }
        ),
        container_count=container_count,
    )


def _criteria(requirements: list[ResourceRequirements]) -> AgentSelectionCriteria:
    return AgentSelectionCriteria(
        session_id=SessionId(uuid.uuid4()),
        resource_group_id=ResourceGroupID(uuid.UUID(int=0)),
        requirements=requirements,
        agent_selection_policy=AgentSelectionPolicy.STRICT,
        designated_agent_ids=None,
    )


def _designated_criteria(
    requirements: list[ResourceRequirements],
    designated_agent_ids: list[AgentId],
) -> AgentSelectionCriteria:
    return AgentSelectionCriteria(
        session_id=SessionId(uuid.uuid4()),
        resource_group_id=ResourceGroupID(uuid.UUID(int=0)),
        requirements=requirements,
        agent_selection_policy=AgentSelectionPolicy.STRICT,
        designated_agent_ids=designated_agent_ids,
    )


def _trackers(agents: list[AgentInfo]) -> list[AgentStateTracker]:
    return [AgentStateTracker(original_agent=agent) for agent in agents]


def _concentrated() -> AgentSelector:
    return AgentSelector(ConcentratedAgentSelector(agent_selection_resource_priority=["cpu"]))


class TestInsufficientResourcesErrorFormat:
    """InsufficientResourcesError must use a header + indented bullet list."""

    def test_multi_resource_shortfall_uses_newlines(self) -> None:
        error = InsufficientResourcesError(
            agent_id=AgentId("agent-a"),
            requested_slots=_slots({"cpu": "4", "mem": "8192"}),
            available_slots=_slots({"cpu": "1", "mem": "2048"}),
            insufficient_resources={
                ResourceSlotName("cpu"): ("4", "1"),
                ResourceSlotName("mem"): ("8192", "2048"),
            },
        )
        message = error.extra_msg or ""
        lines = message.splitlines()
        assert lines[0] == "Agent agent-a has insufficient resources:"
        assert "  - cpu: requested=4, available=1" in lines
        assert "  - mem: requested=8192, available=2048" in lines
        # No legacy "; " join must remain.
        assert "; " not in message


class TestNoAvailableAgentErrorAggregationFormat:
    """The NoAvailableAgentError aggregator must list per-agent reasons line-by-line."""

    @pytest.fixture
    def heterogeneous_failing_agents(self) -> list[AgentInfo]:
        return [
            _agent("agent-a", {"cpu": "1", "mem": "2048"}),
            _agent("agent-b", {"cpu": "8", "mem": "16384"}, container_count=10),
        ]

    async def test_multi_agent_failure_message_layout(
        self,
        heterogeneous_failing_agents: list[AgentInfo],
    ) -> None:
        criteria = _criteria([_req({"cpu": "4", "mem": "8192"})])

        with pytest.raises(BatchAgentSelectionFailedError) as exc_info:
            await _concentrated().select_agents_for_batch_requirements(
                _trackers(heterogeneous_failing_agents),
                criteria,
                AgentLimit(max_container_count=10),
            )
        assert len(exc_info.value.errors) == 1
        error = exc_info.value.errors[0]
        assert isinstance(error, NoAvailableAgentError)

        # Inspect the raw payload we constructed (not the aiohttp title wrapper),
        # since SchedulingFailure.msg is derived from str(e) but the format
        # contract lives in extra_msg.
        message = error.extra_msg or ""
        lines = message.splitlines()
        assert lines[0].startswith("no available agents for the request (")
        assert "arch=x86_64" in lines[0]
        assert any(line.startswith("- ") for line in lines[1:])
        assert "; " not in message


class TestNoAvailableAgentHeaderFormat:
    """The header's requested-slots summary must be human-readable."""

    def test_header_humanizes_byte_slots(self) -> None:
        error = NoAvailableAgentError(
            resource_requirement=_req(
                {"cpu": "1000", "mem": "1073741824"},
                arch="aarch64",
            ),
            requirement_index=0,
            agent_errors={},
        )

        header = (error.extra_msg or "").splitlines()[0]
        assert "cpu=1000" in header
        assert "mem=1 GiB" in header
        assert "1073741824" not in header


class TestMultipleValidationErrorsFormat:
    """MultipleValidationErrors must use the unified '- ' bullet prefix."""

    def test_uses_dash_prefix_and_newline_separation(self) -> None:
        errors = [
            ConcurrencyLimitExceeded(max_sessions=5, session_type="concurrent"),
            DependenciesNotSatisfied(pending_dependency_names=["dep-x (uuid)"]),
        ]
        aggregated = MultipleValidationErrors(errors)
        message = aggregated.extra_msg or ""
        lines = message.splitlines()
        assert lines[0] == "Multiple validation errors occurred:"
        assert any(line.startswith("- ConcurrencyLimitExceeded:") for line in lines[1:])
        assert any(line.startswith("- DependenciesNotSatisfied:") for line in lines[1:])


class TestSchedulingFailureMsgRoundTripsAsJson:
    """status_data JSON round-trip must preserve newline-formatted messages."""

    def test_newlines_survive_json_serialization(self) -> None:
        error = InsufficientResourcesError(
            agent_id=AgentId("agent-a"),
            requested_slots=_slots({"cpu": "4"}),
            available_slots=_slots({"cpu": "1"}),
            insufficient_resources={ResourceSlotName("cpu"): ("4", "1")},
        )
        original = error.extra_msg or ""
        encoded = json.dumps({"msg": original})
        decoded = json.loads(encoded)
        assert decoded["msg"] == original
        assert "\n" in decoded["msg"]


# ============================================================================
# Golden assertions — full message equality, not just substring presence.
# ============================================================================


class TestGoldenInsufficientResourcesError:
    def test_single_resource_shortfall_full_message(self) -> None:
        error = InsufficientResourcesError(
            agent_id=AgentId("agent-a"),
            requested_slots=_slots({"cpu": "4"}),
            available_slots=_slots({"cpu": "1"}),
            insufficient_resources={ResourceSlotName("cpu"): ("4", "1")},
        )
        expected = "Agent agent-a has insufficient resources:\n  - cpu: requested=4, available=1"
        assert error.extra_msg == expected

    def test_multi_resource_shortfall_full_message(self) -> None:
        error = InsufficientResourcesError(
            agent_id=AgentId("agent-a"),
            requested_slots=_slots({"cpu": "4", "mem": "8192"}),
            available_slots=_slots({"cpu": "1", "mem": "2048"}),
            insufficient_resources={
                ResourceSlotName("cpu"): ("4", "1"),
                ResourceSlotName("mem"): ("8 GiB", "2 GiB"),
            },
        )
        expected = (
            "Agent agent-a has insufficient resources:\n"
            "  - cpu: requested=4, available=1\n"
            "  - mem: requested=8 GiB, available=2 GiB"
        )
        assert error.extra_msg == expected


class TestGoldenContainerLimitExceededError:
    def test_full_message(self) -> None:
        err = ContainerLimitExceededError(
            agent_id=AgentId("agent-b"),
            current_count=10,
            max_count=10,
        )
        assert err.extra_msg == "Agent agent-b container limit exceeded: current=10, max=10"


class TestGoldenMultipleValidationErrors:
    def test_full_extra_msg_equals_expected(self) -> None:
        errors = [
            ConcurrencyLimitExceeded(max_sessions=5, session_type="concurrent"),
            DependenciesNotSatisfied(pending_dependency_names=["dep-x not finished"]),
        ]
        aggregated = MultipleValidationErrors(errors)
        expected = (
            "Multiple validation errors occurred:\n"
            "- ConcurrencyLimitExceeded: You cannot run more than 5 concurrent sessions\n"
            "- DependenciesNotSatisfied: Waiting dependency sessions to finish"
            " as success. (dep-x not finished)"
        )
        assert aggregated.extra_msg == expected


class TestGoldenNoAvailableAgentError:
    """End-to-end golden test that exercises the selector path."""

    @pytest.fixture
    def agents_with_two_failure_modes(self) -> list[AgentInfo]:
        return [
            _agent("agent-a", {"cpu": "1"}),
            _agent("agent-b", {"cpu": "8"}, container_count=10),
        ]

    async def test_all_agents_failing_full_extra_msg(
        self,
        agents_with_two_failure_modes: list[AgentInfo],
    ) -> None:
        criteria = _criteria([_req({"cpu": "4"})])

        with pytest.raises(BatchAgentSelectionFailedError) as exc_info:
            await _concentrated().select_agents_for_batch_requirements(
                _trackers(agents_with_two_failure_modes),
                criteria,
                AgentLimit(max_container_count=10),
            )
        assert len(exc_info.value.errors) == 1
        error = exc_info.value.errors[0]
        assert isinstance(error, NoAvailableAgentError)

        expected = (
            "no available agents for the request"
            " (containers=1, arch=x86_64, slots=cpu=4):\n"
            "- Agent agent-a has insufficient resources:\n"
            "    - cpu: requested=4, available=1\n"
            "- Agent agent-b container limit exceeded: current=10, max=10"
        )
        assert error.extra_msg == expected


class TestGoldenNoDesignatedAgentCompatible:
    """End-to-end golden test for the designated-agent failure path."""

    @pytest.fixture
    def designated_agents_plus_fallback(self) -> list[AgentInfo]:
        # The designated-only-incompatible branch requires at least one
        # non-designated compatible agent so the early "no available agents"
        # branch does not short-circuit before reaching it.
        return [
            _agent("designated-a", {"cpu": "1"}),
            _agent("designated-b", {"cpu": "8"}, container_count=10),
            _agent("non-designated-ok", {"cpu": "16"}),
        ]

    async def test_full_extra_msg_when_designated_incompatible(
        self,
        designated_agents_plus_fallback: list[AgentInfo],
    ) -> None:
        criteria = _designated_criteria(
            [_req({"cpu": "4"})],
            designated_agent_ids=[AgentId("designated-a"), AgentId("designated-b")],
        )

        with pytest.raises(BatchAgentSelectionFailedError) as exc_info:
            await _concentrated().select_agents_for_batch_requirements(
                _trackers(designated_agents_plus_fallback),
                criteria,
                AgentLimit(max_container_count=10),
            )
        assert len(exc_info.value.errors) == 1
        error = exc_info.value.errors[0]
        assert isinstance(error, NoAvailableAgentError)

        expected = (
            "no designated agent is compatible for the request"
            " (containers=1, arch=x86_64, slots=cpu=4):\n"
            "- designated agent 'designated-a': Agent designated-a"
            " has insufficient resources:\n"
            "    - cpu: requested=4, available=1\n"
            "- designated agent 'designated-b': Agent designated-b"
            " container limit exceeded: current=10, max=10"
        )
        assert error.extra_msg == expected


class TestGoldenNoAvailableAgentDirectConstruction:
    """Drive NoAvailableAgentError's constructor directly with structured inputs."""

    def test_compat_failures_with_mixed_inner_errors(self) -> None:
        err = NoAvailableAgentError(
            resource_requirement=_req({"cpu": "4"}),
            requirement_index=0,
            agent_errors={
                AgentId("agent-a"): InsufficientResourcesError(
                    agent_id=AgentId("agent-a"),
                    requested_slots=_slots({"cpu": "4"}),
                    available_slots=_slots({"cpu": "1"}),
                    insufficient_resources={ResourceSlotName("cpu"): ("4", "1")},
                ),
                AgentId("agent-b"): ContainerLimitExceededError(
                    agent_id=AgentId("agent-b"),
                    current_count=10,
                    max_count=10,
                ),
            },
        )
        expected = (
            "no available agents for the request"
            " (containers=1, arch=x86_64, slots=cpu=4):\n"
            "- Agent agent-a has insufficient resources:\n"
            "    - cpu: requested=4, available=1\n"
            "- Agent agent-b container limit exceeded: current=10, max=10"
        )
        assert err.extra_msg == expected

    def test_designated_failures_reports_missing_designations(self) -> None:
        # Only 'designated-a' has a recorded failure; 'designated-b' was not
        # even considered (e.g. filtered out by arch). The constructor must
        # synthesize the 'not found in compatible agents' message for it.
        err = NoAvailableAgentError(
            resource_requirement=_req({"cpu": "2"}),
            requirement_index=0,
            agent_errors={
                AgentId("designated-a"): ContainerLimitExceededError(
                    agent_id=AgentId("designated-a"),
                    current_count=5,
                    max_count=5,
                ),
            },
            designated_agent_ids=[
                AgentId("designated-a"),
                AgentId("designated-b"),
            ],
        )
        expected = (
            "no designated agent is compatible for the request"
            " (containers=1, arch=x86_64, slots=cpu=2):\n"
            "- designated agent 'designated-a': Agent designated-a"
            " container limit exceeded: current=5, max=5\n"
            "- designated agent 'designated-b': not found in compatible agents"
        )
        assert err.extra_msg == expected


class TestGoldenNoAgentsInResourceGroupError:
    def test_full_message(self) -> None:
        err = NoAgentsInResourceGroupError(ResourceGroupID(uuid.UUID(int=0)))
        assert (
            err.extra_msg
            == "No agents available in resource group '00000000-0000-0000-0000-000000000000'"
        )
