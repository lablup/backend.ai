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
from ai.backend.common.types import AgentId, AgentSelectionStrategy, SessionId
from ai.backend.manager.data.session.options import AgentSelectionPolicy
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.exceptions import (
    BatchAgentSelectionFailedError,
    NoAgentsInResourceGroupError,
    NoCompatibleAgentError,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.pool import (
    create_agent_selector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
    AgentSelectionCriteria,
    AgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.tracker import AgentStateTracker
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.types import (
    PlacementFailure,
    ResourceRequirements,
)
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
        job_priority=0,
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
        job_priority=0,
    )


def _trackers(agents: list[AgentInfo]) -> list[AgentStateTracker]:
    return [AgentStateTracker(original_agent=agent) for agent in agents]


def _selector() -> AgentSelector:
    return create_agent_selector(["cpu"])


class TestBatchAgentSelectionFailedErrorFormat:
    """The batch error must list per-requirement failures line-by-line."""

    def test_multi_failure_message_layout(self) -> None:
        error = BatchAgentSelectionFailedError([
            PlacementFailure(
                requirement_index=0,
                resource_requirement=_req({"cpu": "4"}),
                filter_name="resource",
                missing_slots=_slots({"cpu": "2"}),
                missing_containers=0,
            ),
            PlacementFailure(
                requirement_index=1,
                resource_requirement=_req({"cpu": "1"}),
                filter_name="container-limit",
                missing_slots={},
                missing_containers=2,
            ),
        ])
        message = error.extra_msg or ""
        lines = message.splitlines()
        assert lines[0] == "2 requirement(s) could not be placed:"
        assert sum(line.startswith("- requirement #") for line in lines) == 2
        assert "; " not in message


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
        error = BatchAgentSelectionFailedError([
            PlacementFailure(
                requirement_index=0,
                resource_requirement=_req({"cpu": "4"}),
                filter_name="resource",
                missing_slots=_slots({"cpu": "3"}),
                missing_containers=0,
            ),
        ])
        original = error.extra_msg or ""
        encoded = json.dumps({"msg": original})
        decoded = json.loads(encoded)
        assert decoded["msg"] == original
        assert "\n" in decoded["msg"]


# ============================================================================
# Golden assertions — full message equality, not just substring presence.
# ============================================================================


class TestGoldenResourceShortfall:
    """End-to-end golden test that exercises the selector path."""

    @pytest.fixture
    def agents_too_small(self) -> list[AgentInfo]:
        return [
            _agent("agent-a", {"cpu": "1"}),
            _agent("agent-b", {"cpu": "2"}),
        ]

    async def test_all_agents_failing_full_extra_msg(
        self,
        agents_too_small: list[AgentInfo],
    ) -> None:
        criteria = _criteria([_req({"cpu": "4"})])

        with pytest.raises(BatchAgentSelectionFailedError) as exc_info:
            await _selector().select_agents_for_batch_requirements(
                AgentSelectionStrategy.CONCENTRATED,
                _trackers(agents_too_small),
                criteria,
                AgentLimit(max_container_count=10),
            )

        # The shortfall is measured against the best-fitting agent (agent-b).
        expected = (
            "1 requirement(s) could not be placed:\n"
            "- requirement #0 (containers=1, arch=x86_64, slots=cpu=4):"
            " no agents passed the 'resource' filter\n"
            "  - cpu: missing=2"
        )
        assert exc_info.value.extra_msg == expected


class TestGoldenDesignatedAgentAbsent:
    """End-to-end golden test for the strict-designation failure path."""

    @pytest.fixture
    def pool_without_designated_agents(self) -> list[AgentInfo]:
        return [_agent("non-designated-ok", {"cpu": "16"})]

    async def test_full_extra_msg_when_designated_absent(
        self,
        pool_without_designated_agents: list[AgentInfo],
    ) -> None:
        """The strict-designation filter emptying the pool is an absolute
        failure, so it propagates directly instead of a batch aggregate."""
        criteria = _designated_criteria(
            [_req({"cpu": "4"})],
            designated_agent_ids=[AgentId("designated-a"), AgentId("designated-b")],
        )

        with pytest.raises(NoCompatibleAgentError) as exc_info:
            await _selector().select_agents_for_batch_requirements(
                AgentSelectionStrategy.CONCENTRATED,
                _trackers(pool_without_designated_agents),
                criteria,
                AgentLimit(max_container_count=10),
            )

        assert exc_info.value.filter_name == "designated-strict"
        assert exc_info.value.extra_msg == "no agents passed the 'designated-strict' filter"


class TestGoldenBatchErrorDirectConstruction:
    """Drive BatchAgentSelectionFailedError's constructor with structured inputs."""

    def test_humanizes_mem_in_header_and_shortfall(self) -> None:
        error = BatchAgentSelectionFailedError([
            PlacementFailure(
                requirement_index=1,
                resource_requirement=_req({"cpu": "1000", "mem": "2147483648"}, arch="aarch64"),
                filter_name="resource",
                missing_slots=_slots({"mem": "1073741824"}),
                missing_containers=0,
            ),
        ])
        expected = (
            "1 requirement(s) could not be placed:\n"
            "- requirement #1 (containers=1, arch=aarch64, slots=cpu=1000 mem=2 GiB):"
            " no agents passed the 'resource' filter\n"
            "  - mem: missing=1 GiB"
        )
        assert error.extra_msg == expected

    def test_container_limit_failure_reports_containers_to_free(self) -> None:
        # The container limit empties the pool without any slot being short;
        # the message reports how many containers must be freed instead.
        error = BatchAgentSelectionFailedError([
            PlacementFailure(
                requirement_index=0,
                resource_requirement=_req({"cpu": "1"}),
                filter_name="container-limit",
                missing_slots={},
                missing_containers=1,
            ),
        ])
        expected = (
            "1 requirement(s) could not be placed:\n"
            "- requirement #0 (containers=1, arch=x86_64, slots=cpu=1):"
            " no agents passed the 'container-limit' filter\n"
            "  - containers: missing=1"
        )
        assert error.extra_msg == expected


class TestGoldenNoAgentsInResourceGroupError:
    def test_full_message(self) -> None:
        err = NoAgentsInResourceGroupError(ResourceGroupID(uuid.UUID(int=0)))
        assert (
            err.extra_msg
            == "No agents available in resource group '00000000-0000-0000-0000-000000000000'"
        )
