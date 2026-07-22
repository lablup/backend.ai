"""
Exceptions for agent selection in sokovan scheduler.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from decimal import Decimal
from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import AgentId, BinarySize, SlotName
from ai.backend.manager.sokovan.scheduler.exceptions import SchedulingError

from .types import RemediationHint, ResourceRequirements


def _humanize_slot(slot_name: SlotName, value: Decimal) -> str:
    # Format mem as human readable (e.g., "2 GiB" instead of raw bytes)
    if slot_name == "mem":
        return str(BinarySize(value))
    return str(value)


class AgentSelectionError(SchedulingError):
    """Base exception for agent selection errors."""

    error_type = "https://api.backend.ai/probs/agent-selection-failed"
    error_title = "Agent selection failed."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )

    @abstractmethod
    def build_remediation_hint(self) -> RemediationHint:
        """Return a structured remediation hint for this selection failure.

        Every selection error must describe what the caller could change
        (reduce resources / change architecture / revise designated agents),
        so a dry-run can surface it without parsing the human-readable message.
        """
        raise NotImplementedError


class RequirementSelectionError(AgentSelectionError):
    """A per-requirement selection failure that knows its requirement.

    ``requirement_index`` is the position of the failed requirement in the
    criteria, so callers can map the failure back to their own bookkeeping
    (e.g. the kernel group a requirement was built from).
    """

    @property
    @abstractmethod
    def resource_requirement(self) -> ResourceRequirements:
        raise NotImplementedError

    @property
    @abstractmethod
    def requirement_index(self) -> int:
        raise NotImplementedError


class NoAgentsInResourceGroupError(AgentSelectionError, web.HTTPServiceUnavailable):
    """Raised when the resource group has no candidate agents at all.

    Distinct from :class:`NoAvailableAgentError`, which aggregates *per-kernel*
    compatibility failures across known candidates.
    """

    error_type = "https://api.backend.ai/probs/no-agents-in-resource-group"
    error_title = "Unavailable : Resource group has no candidate agents."

    _resource_group_id: ResourceGroupID

    def __init__(self, resource_group_id: ResourceGroupID) -> None:
        self._resource_group_id = resource_group_id
        super().__init__(f"No agents available in resource group '{resource_group_id}'")

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )

    @override
    def build_remediation_hint(self) -> RemediationHint:
        # The resource group has no candidate agents at all; nothing the caller
        # can adjust on the request itself fixes this.
        return RemediationHint()


class NoAvailableAgentError(RequirementSelectionError):
    """Raised when no agents can satisfy a kernel-group's resource requirement.

    The constructor accepts the structured inputs that describe *which*
    kernels failed and *why* each candidate agent was rejected, and composes
    the multi-line, bullet-formatted message itself.
    """

    error_type = "https://api.backend.ai/probs/no-available-agents"
    error_title = "Unavailable : No agents can be allocated at this time."

    _resource_requirement: ResourceRequirements
    _requirement_index: int
    _agent_errors: Mapping[AgentId, TrackerCompatibilityError]
    _available_agent_ids: Sequence[AgentId]
    _designated_agent_ids: Sequence[AgentId] | None

    def __init__(
        self,
        *,
        resource_requirement: ResourceRequirements,
        requirement_index: int,
        agent_errors: Mapping[AgentId, TrackerCompatibilityError],
        available_agent_ids: Sequence[AgentId] = (),
        designated_agent_ids: Sequence[AgentId] | None = None,
    ) -> None:
        self._resource_requirement = resource_requirement
        self._requirement_index = requirement_index
        self._agent_errors = agent_errors
        self._available_agent_ids = available_agent_ids
        self._designated_agent_ids = designated_agent_ids
        super().__init__(self._build_message())

    @property
    @override
    def resource_requirement(self) -> ResourceRequirements:
        return self._resource_requirement

    @property
    @override
    def requirement_index(self) -> int:
        return self._requirement_index

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )

    @override
    def build_remediation_hint(self) -> RemediationHint:
        # Merge each candidate node's own remediation. No isinstance branching:
        # every TrackerCompatibilityError contributes its partial RemediationHint.
        partials = [err.remediation_hint_contribution() for err in self._agent_errors.values()]
        reductions = [p.required_reduction for p in partials if p.required_reduction is not None]
        container_reductions = [
            p.required_container_reduction
            for p in partials
            if p.required_container_reduction is not None
        ]
        return RemediationHint(
            # The compatible agents the caller could use (e.g. to compare against
            # the designated agents that failed).
            available_agent_ids=list(self._available_agent_ids) or None,
            required_reduction=(
                min(reductions, key=lambda slot: sum(slot.values())) if reductions else None
            ),
            required_container_reduction=(
                min(container_reductions) if container_reductions else None
            ),
        )

    def _build_message(self) -> str:
        header = self._format_header()
        if self._designated_agent_ids is None:
            prefix = "no available agents"
            # Use extra_msg directly so the inner BackendAIError's `title (msg)`
            # wrapping does not leak into our aggregated layout.
            reasons: Iterable[str] = (err.extra_msg or "" for err in self._agent_errors.values())
        else:
            prefix = "no designated agent is compatible"
            reasons = self._designated_reasons()
        details = self._format_reason_lines(reasons)
        return f"{prefix} for {header}:\n{details}"

    def _format_header(self) -> str:
        req = self._resource_requirement
        slot_str = " ".join(
            f"{k}={_humanize_slot(k, v)}" for k, v in req.requested_slots.slots.items() if v
        )
        return (
            f"the request (containers={req.container_count}, "
            f"arch={req.required_architecture}, slots={slot_str})"
        )

    def _designated_reasons(self) -> list[str]:
        reasons: list[str] = []
        for agent_id in self._designated_agent_ids or ():
            err = self._agent_errors.get(agent_id)
            reason = (err.extra_msg or "") if err is not None else "not found in compatible agents"
            reasons.append(f"designated agent '{agent_id}': {reason}")
        return reasons

    @staticmethod
    def _format_reason_lines(reasons: Iterable[str]) -> str:
        """Format reasons as a '- '-prefixed bullet list with continuation indent.

        Multi-line inner messages keep their internal indentation so the agent →
        detail hierarchy stays visually clear in the rendered output.
        """
        lines: list[str] = []
        for reason in reasons:
            msg_lines = reason.splitlines() or [""]
            first, *rest = msg_lines
            lines.append(f"- {first}")
            lines.extend(f"  {line}" for line in rest)
        return "\n".join(lines)


class NoCompatibleAgentError(RequirementSelectionError):
    """Raised when no agent matches the required architecture.

    Carries the structured architecture context so a dry-run can suggest which
    architectures the request could target instead.
    """

    error_type = "https://api.backend.ai/probs/no-compatible-agents"
    error_title = "No agents meet the resource requirements."

    _resource_requirement: ResourceRequirements
    _requirement_index: int
    _available_architectures: Sequence[str]

    def __init__(
        self,
        *,
        resource_requirement: ResourceRequirements,
        requirement_index: int,
        available_architectures: Sequence[str],
    ) -> None:
        self._resource_requirement = resource_requirement
        self._requirement_index = requirement_index
        self._available_architectures = available_architectures
        super().__init__(
            f"No agents with required architecture "
            f"'{resource_requirement.required_architecture}'. "
            f"Available architectures: {', '.join(available_architectures)}"
        )

    @property
    @override
    def resource_requirement(self) -> ResourceRequirements:
        return self._resource_requirement

    @property
    @override
    def requirement_index(self) -> int:
        return self._requirement_index

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )

    @override
    def build_remediation_hint(self) -> RemediationHint:
        return RemediationHint(available_archs=list(self._available_architectures))


class BatchAgentSelectionFailedError(SchedulingError):
    """Aggregates per-requirement placement failures of a single batch selection.

    Carries the structured ``errors`` so a dry-run can map each failed
    requirement (via ``requirement_index``) to its remediation hint by
    catching this error, instead of inspecting selections.
    """

    error_type = "https://api.backend.ai/probs/batch-agent-selection-failed"
    error_title = "Some kernels could not be placed on any agent."

    errors: Sequence[RequirementSelectionError]

    def __init__(self, errors: Sequence[RequirementSelectionError]) -> None:
        self.errors = errors
        super().__init__(self._build_message())

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )

    def _build_message(self) -> str:
        header = f"{len(self.errors)} requirement(s) could not be placed"
        body = "\n".join((err.extra_msg or str(err)) for err in self.errors)
        return f"{header}:\n{body}"


# Per-agent compatibility check exceptions. These inherit from BackendAIError so
# every concrete subclass is forced to declare an `error_code` — otherwise a new
# compatibility error could silently leak with an undefined RFC-7807 code.
class TrackerCompatibilityError(BackendAIError, ABC):
    """Base exception for tracker compatibility checks."""

    error_type = "https://api.backend.ai/probs/agent-compatibility-failed"
    error_title = "Agent compatibility check failed."

    @abstractmethod
    def remediation_hint_contribution(self) -> RemediationHint:
        """Return this single node's remediation contribution.

        ``NoAvailableAgentError`` merges these partials across all candidate
        nodes, so each compatibility error decides only its own remediation.
        """
        raise NotImplementedError


class InsufficientResourcesError(TrackerCompatibilityError):
    """Raised when agent does not have sufficient resources available."""

    error_type = "https://api.backend.ai/probs/agent-insufficient-resources"
    error_title = "Agent has insufficient resources."

    _agent_id: AgentId
    _requested_slots: Mapping[SlotName, Decimal]
    _available_slots: Mapping[SlotName, Decimal]
    _insufficient_resources: dict[SlotName, tuple[str, str]]

    def __init__(
        self,
        agent_id: AgentId,
        requested_slots: Mapping[SlotName, Decimal],
        available_slots: Mapping[SlotName, Decimal],
        insufficient_resources: dict[SlotName, tuple[str, str]],
    ) -> None:
        self._agent_id = agent_id
        self._requested_slots = requested_slots
        self._available_slots = available_slots
        self._insufficient_resources = insufficient_resources

        # Build detailed message: one resource shortfall per indented line so that
        # upstream aggregators (e.g. NoAvailableAgentError) can newline-join cleanly.
        resource_lines = [
            f"  - {resource_name}: requested={requested}, available={available}"
            for resource_name, (requested, available) in insufficient_resources.items()
        ]
        details_msg = "\n".join(resource_lines)

        super().__init__(f"Agent {agent_id} has insufficient resources:\n{details_msg}")

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )

    @override
    def remediation_hint_contribution(self) -> RemediationHint:
        # Per-slot shortage on this agent: max(0, requested - available).
        reduction = {
            slot_name: shortage
            for slot_name, requested in self._requested_slots.items()
            if (shortage := requested - self._available_slots.get(slot_name, Decimal(0)))
            > Decimal(0)
        }
        return RemediationHint(required_reduction=reduction)


class ContainerLimitExceededError(TrackerCompatibilityError):
    """Raised when agent has reached its maximum container count limit."""

    error_type = "https://api.backend.ai/probs/agent-container-limit-exceeded"
    error_title = "Agent has reached its container limit."

    _agent_id: AgentId
    _current_count: int
    _max_count: int

    def __init__(
        self,
        agent_id: AgentId,
        current_count: int,
        max_count: int,
    ) -> None:
        self._agent_id = agent_id
        self._current_count = current_count
        self._max_count = max_count
        super().__init__(
            f"Agent {agent_id} container limit exceeded: current={current_count}, max={max_count}"
        )

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )

    @override
    def remediation_hint_contribution(self) -> RemediationHint:
        # Containers to free so one more can be admitted (current is at/over max).
        return RemediationHint(
            required_container_reduction=self._current_count - self._max_count + 1
        )
