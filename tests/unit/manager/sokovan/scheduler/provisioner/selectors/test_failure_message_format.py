"""Format-level tests for scheduling failure messages (BA-6149).

These tests pin down the user-facing layout of error messages so that future
refactors do not accidentally regress to ";"-joined single-line aggregates.
Golden assertions compare entire messages to lock down the exact layout.
"""

from __future__ import annotations

import json
import uuid
from decimal import Decimal
from uuid import UUID

import pytest

from ai.backend.common.types import (
    AgentId,
    ClusterMode,
    KernelId,
    ResourceSlot,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.concentrated import (
    ConcentratedAgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.exceptions import (
    ArchitectureIncompatibleError,
    ContainerLimitExceededError,
    InsufficientResourcesError,
    NoAgentsInResourceGroupError,
    NoAvailableAgentError,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
    AgentInfo,
    AgentSelectionConfig,
    AgentSelectionCriteria,
    AgentSelector,
    KernelResourceSpec,
    SessionMetadata,
)
from ai.backend.manager.sokovan.scheduler.provisioner.validators.exceptions import (
    ConcurrencyLimitExceeded,
    DependenciesNotSatisfied,
    MultipleValidationErrors,
)


class TestInsufficientResourcesErrorFormat:
    """InsufficientResourcesError must use a header + indented bullet list."""

    def test_multi_resource_shortfall_uses_newlines(self) -> None:
        error = InsufficientResourcesError(
            agent_id=AgentId("agent-a"),
            requested_slots=ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8192")}),
            available_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2048")}),
            occupied_slots=ResourceSlot({}),
            insufficient_resources={
                "cpu": ("4", "1"),
                "mem": ("8192", "2048"),
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
            AgentInfo(
                agent_id=AgentId("agent-a"),
                agent_addr="agent-a:6001",
                architecture="x86_64",
                available_slots=ResourceSlot({
                    "cpu": Decimal("1"),
                    "mem": Decimal("2048"),
                }),
                occupied_slots=ResourceSlot({"cpu": Decimal("0"), "mem": Decimal("0")}),
                scaling_group="default",
                container_count=0,
            ),
            AgentInfo(
                agent_id=AgentId("agent-b"),
                agent_addr="agent-b:6001",
                architecture="x86_64",
                available_slots=ResourceSlot({
                    "cpu": Decimal("8"),
                    "mem": Decimal("16384"),
                }),
                occupied_slots=ResourceSlot({"cpu": Decimal("0"), "mem": Decimal("0")}),
                scaling_group="default",
                container_count=10,  # at container limit
            ),
        ]

    async def test_multi_agent_failure_message_layout(
        self,
        heterogeneous_failing_agents: list[AgentInfo],
    ) -> None:
        kernel_id = uuid.uuid4()
        criteria = AgentSelectionCriteria(
            session_metadata=SessionMetadata(
                session_id=SessionId(uuid.uuid4()),
                session_type=SessionTypes.INTERACTIVE,
                scaling_group="default",
                cluster_mode=ClusterMode.SINGLE_NODE,
            ),
            kernel_requirements={
                kernel_id: KernelResourceSpec(
                    requested_slots=ResourceSlot({
                        "cpu": Decimal("4"),
                        "mem": Decimal("8192"),
                    }),
                    required_architecture="x86_64",
                ),
            },
        )
        config = AgentSelectionConfig(max_container_count=10)
        selector = AgentSelector(
            ConcentratedAgentSelector(agent_selection_resource_priority=["cpu", "mem"]),
        )

        with pytest.raises(NoAvailableAgentError) as exc_info:
            await selector.select_agents_for_batch_requirements(
                heterogeneous_failing_agents,
                criteria,
                config,
            )

        # Inspect the raw payload we constructed (not the aiohttp title wrapper),
        # since SchedulingFailure.msg is derived from str(e) but the format
        # contract lives in extra_msg.
        message = exc_info.value.extra_msg or ""
        lines = message.splitlines()
        assert lines[0].startswith("no available agents for kernels [")
        assert "arch=x86_64" in lines[0]
        assert any(line.startswith("- ") for line in lines[1:])
        assert "; " not in message
        # No "Nx ErrorType" count-prefix aggregation.
        for line in lines[1:]:
            stripped = line.lstrip("- ")
            if stripped and stripped[0].isdigit():
                # e.g. "3x Insufficient..." would have a digit then "x ".
                head = stripped[:4]
                assert "x " not in head, f"unexpected count-prefix in: {line!r}"


class TestNoAvailableAgentHeaderFormat:
    """The header's requested-slots summary must be human-readable."""

    def test_header_humanizes_byte_slots(self) -> None:
        error = NoAvailableAgentError(
            kernel_ids=[KernelId(uuid.uuid4())],
            required_architecture="aarch64",
            requested_slots=ResourceSlot({
                "cpu": Decimal("1000"),
                "mem": Decimal("1073741824"),
            }),
            agent_errors={},
        )

        header = (error.extra_msg or "").splitlines()[0]
        assert "cpu=1000" in header
        assert "mem=1g" in header
        assert "1073741824" not in header


class TestDesignatedAgentFailureFormat:
    """Designated-agent failure path must list each candidate reason on its own line."""

    @pytest.fixture
    def two_designated_candidates(self) -> list[AgentInfo]:
        # The designated-only-incompatible path requires at least one
        # non-designated compatible agent so the early "no available agents"
        # branch does not short-circuit before reaching the designated check.
        return [
            AgentInfo(
                agent_id=AgentId("designated-a"),
                agent_addr="designated-a:6001",
                architecture="x86_64",
                available_slots=ResourceSlot({
                    "cpu": Decimal("1"),
                    "mem": Decimal("1024"),
                }),
                occupied_slots=ResourceSlot({"cpu": Decimal("0"), "mem": Decimal("0")}),
                scaling_group="default",
                container_count=0,
            ),
            AgentInfo(
                agent_id=AgentId("designated-b"),
                agent_addr="designated-b:6001",
                architecture="x86_64",
                available_slots=ResourceSlot({
                    "cpu": Decimal("8"),
                    "mem": Decimal("16384"),
                }),
                occupied_slots=ResourceSlot({"cpu": Decimal("0"), "mem": Decimal("0")}),
                scaling_group="default",
                container_count=10,  # at container limit
            ),
            AgentInfo(
                agent_id=AgentId("non-designated-ok"),
                agent_addr="non-designated-ok:6001",
                architecture="x86_64",
                available_slots=ResourceSlot({
                    "cpu": Decimal("16"),
                    "mem": Decimal("65536"),
                }),
                occupied_slots=ResourceSlot({"cpu": Decimal("0"), "mem": Decimal("0")}),
                scaling_group="default",
                container_count=0,
            ),
        ]

    async def test_each_designated_reason_is_on_its_own_line(
        self,
        two_designated_candidates: list[AgentInfo],
    ) -> None:
        kernel_id = uuid.uuid4()
        criteria = AgentSelectionCriteria(
            session_metadata=SessionMetadata(
                session_id=SessionId(uuid.uuid4()),
                session_type=SessionTypes.INTERACTIVE,
                scaling_group="default",
                cluster_mode=ClusterMode.SINGLE_NODE,
            ),
            kernel_requirements={
                kernel_id: KernelResourceSpec(
                    requested_slots=ResourceSlot({
                        "cpu": Decimal("4"),
                        "mem": Decimal("8192"),
                    }),
                    required_architecture="x86_64",
                ),
            },
        )
        config = AgentSelectionConfig(max_container_count=10)
        selector = AgentSelector(
            ConcentratedAgentSelector(agent_selection_resource_priority=["cpu", "mem"]),
        )

        with pytest.raises(NoAvailableAgentError) as exc_info:
            await selector.select_agents_for_batch_requirements(
                two_designated_candidates,
                criteria,
                config,
                designated_agent_ids=[
                    AgentId("designated-a"),
                    AgentId("designated-b"),
                ],
            )

        message = exc_info.value.extra_msg or ""
        assert message.startswith("no designated agent is compatible for kernels [")
        assert "designated agent 'designated-a'" in message
        assert "designated agent 'designated-b'" in message
        # Earlier bug: `error_messages_list` was populated but never used, and
        # `" ".join(error_messages)` joined defaultdict keys into an empty string.
        # The reasons must actually appear, separated by newlines, not "; ".
        assert "; " not in message
        assert "\n" in message


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
        # Each enumerated error starts with the unified '- ' prefix.
        assert any(line.startswith("- ConcurrencyLimitExceeded:") for line in lines[1:])
        assert any(line.startswith("- DependenciesNotSatisfied:") for line in lines[1:])
        # No legacy "  1. " / "  2. " numbered prefix.
        assert "  1. " not in message
        assert "  2. " not in message


class TestSchedulingFailureMsgRoundTripsAsJson:
    """status_data JSON round-trip must preserve newline-formatted messages."""

    def test_newlines_survive_json_serialization(self) -> None:
        error = InsufficientResourcesError(
            agent_id=AgentId("agent-a"),
            requested_slots=ResourceSlot({"cpu": Decimal("4")}),
            available_slots=ResourceSlot({"cpu": Decimal("1")}),
            occupied_slots=ResourceSlot({}),
            insufficient_resources={"cpu": ("4", "1")},
        )
        original = error.extra_msg or ""
        # Simulate the SchedulingFailure.msg → JSON path.
        encoded = json.dumps({"msg": original})
        decoded = json.loads(encoded)
        assert decoded["msg"] == original
        assert "\n" in decoded["msg"]


class TestArchitectureMessageStaysSinglePhrase:
    """Short single-phrase joins (', '-separated) should not be touched."""

    def test_architecture_incompatible_still_uses_comma_join(self) -> None:
        err = ArchitectureIncompatibleError(
            agent_id=AgentId("agent-a"),
            agent_arch="aarch64",
            required_arch="x86_64",
        )
        # The message is a single phrase; ", " join (if present in upstream
        # listings) is appropriate. The exception itself should not contain
        # any "; " aggregator.
        assert "; " not in (err.extra_msg or "")


class TestContainerLimitMessageIsSinglePhrase:
    def test_container_limit_message(self) -> None:
        err = ContainerLimitExceededError(
            agent_id=AgentId("agent-a"),
            current_count=10,
            max_count=10,
        )
        assert "; " not in (err.extra_msg or "")


# ============================================================================
# Golden assertions — full message equality, not just substring presence.
# Each test below pins the entire user-visible message text. To keep the
# comparison deterministic, kernel UUIDs are fixed and slot dicts hold a
# single key so iteration order is not a factor.
# ============================================================================


_GOLDEN_KERNEL_ID = KernelId(UUID("00000000-0000-0000-0000-000000000001"))


class TestGoldenInsufficientResourcesError:
    def test_single_resource_shortfall_full_message(self) -> None:
        error = InsufficientResourcesError(
            agent_id=AgentId("agent-a"),
            requested_slots=ResourceSlot({"cpu": Decimal("4")}),
            available_slots=ResourceSlot({"cpu": Decimal("1")}),
            occupied_slots=ResourceSlot({}),
            insufficient_resources={"cpu": ("4", "1")},
        )
        expected = "Agent agent-a has insufficient resources:\n  - cpu: requested=4, available=1"
        assert error.extra_msg == expected

    def test_multi_resource_shortfall_full_message(self) -> None:
        error = InsufficientResourcesError(
            agent_id=AgentId("agent-a"),
            requested_slots=ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8192")}),
            available_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2048")}),
            occupied_slots=ResourceSlot({}),
            # dict literal preserves insertion order in Python 3.7+
            insufficient_resources={
                "cpu": ("4", "1"),
                "mem": ("8 GiB", "2 GiB"),
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


class TestGoldenArchitectureIncompatibleError:
    def test_full_message(self) -> None:
        err = ArchitectureIncompatibleError(
            agent_id=AgentId("agent-a"),
            agent_arch="aarch64",
            required_arch="x86_64",
        )
        assert err.extra_msg == (
            "Agent agent-a architecture 'aarch64' does not match required architecture 'x86_64'"
        )


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
            AgentInfo(
                agent_id=AgentId("agent-a"),
                agent_addr="agent-a:6001",
                architecture="x86_64",
                available_slots=ResourceSlot({"cpu": Decimal("1")}),
                occupied_slots=ResourceSlot({"cpu": Decimal("0")}),
                scaling_group="default",
                container_count=0,
            ),
            AgentInfo(
                agent_id=AgentId("agent-b"),
                agent_addr="agent-b:6001",
                architecture="x86_64",
                available_slots=ResourceSlot({"cpu": Decimal("8")}),
                occupied_slots=ResourceSlot({"cpu": Decimal("0")}),
                scaling_group="default",
                container_count=10,  # at container limit
            ),
        ]

    async def test_all_agents_failing_full_extra_msg(
        self,
        agents_with_two_failure_modes: list[AgentInfo],
    ) -> None:
        criteria = AgentSelectionCriteria(
            session_metadata=SessionMetadata(
                session_id=SessionId(uuid.uuid4()),
                session_type=SessionTypes.INTERACTIVE,
                scaling_group="default",
                cluster_mode=ClusterMode.SINGLE_NODE,
            ),
            kernel_requirements={
                _GOLDEN_KERNEL_ID: KernelResourceSpec(
                    requested_slots=ResourceSlot({"cpu": Decimal("4")}),
                    required_architecture="x86_64",
                ),
            },
        )
        config = AgentSelectionConfig(max_container_count=10)
        selector = AgentSelector(
            ConcentratedAgentSelector(agent_selection_resource_priority=["cpu"]),
        )

        with pytest.raises(NoAvailableAgentError) as exc_info:
            await selector.select_agents_for_batch_requirements(
                agents_with_two_failure_modes,
                criteria,
                config,
            )

        expected = (
            f"no available agents for kernels [{_GOLDEN_KERNEL_ID}]"
            " (arch=x86_64, slots=cpu=4):\n"
            "- Agent agent-a has insufficient resources:\n"
            "    - cpu: requested=4, available=1\n"
            "- Agent agent-b container limit exceeded: current=10, max=10"
        )
        assert exc_info.value.extra_msg == expected


class TestGoldenNoDesignatedAgentCompatible:
    """End-to-end golden test for the designated-agent failure path."""

    @pytest.fixture
    def designated_agents_plus_fallback(self) -> list[AgentInfo]:
        # The designated-only-incompatible branch requires at least one
        # non-designated compatible agent so the early "no available agents"
        # branch does not short-circuit before reaching it.
        return [
            AgentInfo(
                agent_id=AgentId("designated-a"),
                agent_addr="designated-a:6001",
                architecture="x86_64",
                available_slots=ResourceSlot({"cpu": Decimal("1")}),
                occupied_slots=ResourceSlot({"cpu": Decimal("0")}),
                scaling_group="default",
                container_count=0,
            ),
            AgentInfo(
                agent_id=AgentId("designated-b"),
                agent_addr="designated-b:6001",
                architecture="x86_64",
                available_slots=ResourceSlot({"cpu": Decimal("8")}),
                occupied_slots=ResourceSlot({"cpu": Decimal("0")}),
                scaling_group="default",
                container_count=10,
            ),
            AgentInfo(
                agent_id=AgentId("non-designated-ok"),
                agent_addr="non-designated-ok:6001",
                architecture="x86_64",
                available_slots=ResourceSlot({"cpu": Decimal("16")}),
                occupied_slots=ResourceSlot({"cpu": Decimal("0")}),
                scaling_group="default",
                container_count=0,
            ),
        ]

    async def test_full_extra_msg_when_designated_incompatible(
        self,
        designated_agents_plus_fallback: list[AgentInfo],
    ) -> None:
        criteria = AgentSelectionCriteria(
            session_metadata=SessionMetadata(
                session_id=SessionId(uuid.uuid4()),
                session_type=SessionTypes.INTERACTIVE,
                scaling_group="default",
                cluster_mode=ClusterMode.SINGLE_NODE,
            ),
            kernel_requirements={
                _GOLDEN_KERNEL_ID: KernelResourceSpec(
                    requested_slots=ResourceSlot({"cpu": Decimal("4")}),
                    required_architecture="x86_64",
                ),
            },
        )
        config = AgentSelectionConfig(max_container_count=10)
        selector = AgentSelector(
            ConcentratedAgentSelector(agent_selection_resource_priority=["cpu"]),
        )

        with pytest.raises(NoAvailableAgentError) as exc_info:
            await selector.select_agents_for_batch_requirements(
                designated_agents_plus_fallback,
                criteria,
                config,
                designated_agent_ids=[
                    AgentId("designated-a"),
                    AgentId("designated-b"),
                ],
            )

        expected = (
            f"no designated agent is compatible for kernels [{_GOLDEN_KERNEL_ID}]"
            " (arch=x86_64, slots=cpu=4):\n"
            "- designated agent 'designated-a': Agent designated-a"
            " has insufficient resources:\n"
            "    - cpu: requested=4, available=1\n"
            "- designated agent 'designated-b': Agent designated-b"
            " container limit exceeded: current=10, max=10"
        )
        assert exc_info.value.extra_msg == expected


class TestGoldenNoAvailableAgentDirectConstruction:
    """Drive NoAvailableAgentError's constructor directly with structured inputs.

    These tests do not pre-format any newline-containing strings on the caller
    side; the exception class itself is responsible for laying out the message.
    """

    def test_compat_failures_with_mixed_inner_errors(self) -> None:
        kernel_id = KernelId(UUID("00000000-0000-0000-0000-000000000002"))
        err = NoAvailableAgentError(
            kernel_ids=[kernel_id],
            required_architecture="x86_64",
            requested_slots=ResourceSlot({"cpu": Decimal("4")}),
            agent_errors={
                AgentId("agent-a"): InsufficientResourcesError(
                    agent_id=AgentId("agent-a"),
                    requested_slots=ResourceSlot({"cpu": Decimal("4")}),
                    available_slots=ResourceSlot({"cpu": Decimal("1")}),
                    occupied_slots=ResourceSlot({}),
                    insufficient_resources={"cpu": ("4", "1")},
                ),
                AgentId("agent-b"): ContainerLimitExceededError(
                    agent_id=AgentId("agent-b"),
                    current_count=10,
                    max_count=10,
                ),
            },
        )
        expected = (
            f"no available agents for kernels [{kernel_id}]"
            " (arch=x86_64, slots=cpu=4):\n"
            "- Agent agent-a has insufficient resources:\n"
            "    - cpu: requested=4, available=1\n"
            "- Agent agent-b container limit exceeded: current=10, max=10"
        )
        assert err.extra_msg == expected

    def test_designated_failures_reports_missing_designations(self) -> None:
        kernel_id = KernelId(UUID("00000000-0000-0000-0000-000000000003"))
        # Only 'designated-a' has a recorded failure; 'designated-b' was not
        # even considered (e.g. filtered out by arch). The constructor must
        # synthesize the 'not found in compatible agents' message for it.
        err = NoAvailableAgentError(
            kernel_ids=[kernel_id],
            required_architecture="x86_64",
            requested_slots=ResourceSlot({"cpu": Decimal("2")}),
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
            f"no designated agent is compatible for kernels [{kernel_id}]"
            " (arch=x86_64, slots=cpu=2):\n"
            "- designated agent 'designated-a': Agent designated-a"
            " container limit exceeded: current=5, max=5\n"
            "- designated agent 'designated-b': not found in compatible agents"
        )
        assert err.extra_msg == expected


class TestGoldenNoAgentsInResourceGroupError:
    def test_full_message(self) -> None:
        err = NoAgentsInResourceGroupError("default")
        assert err.extra_msg == "No agents available in resource group 'default'"
