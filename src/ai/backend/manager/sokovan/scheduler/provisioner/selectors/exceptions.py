"""
Exceptions for agent selection in sokovan scheduler.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from decimal import Decimal

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.common.types import AgentId, KernelId, ResourceSlot
from ai.backend.manager.data.sokovan import SchedulingPredicate
from ai.backend.manager.sokovan.scheduler.exceptions import SchedulingError

from .types import Suggestion, SuggestionKind


class AgentSelectionError(SchedulingError):
    """Base exception for agent selection errors."""

    error_type = "https://api.backend.ai/probs/agent-selection-failed"
    error_title = "Agent selection failed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )

    def failed_predicates(self) -> list[SchedulingPredicate]:
        """Return list of failed predicates for this error."""
        return [SchedulingPredicate(name=type(self).__name__, msg=str(self))]

    @abstractmethod
    def build_suggestion(self) -> Suggestion:
        """Return a structured remediation hint for this selection failure.

        Every selection error must describe what the caller could change
        (reduce resources / change architecture / revise designated agents),
        so a dry-run can surface it without parsing the human-readable message.
        """
        raise NotImplementedError


class NoAgentsInResourceGroupError(AgentSelectionError):
    """Raised when the resource group has no candidate agents at all.

    Distinct from :class:`NoAvailableAgentError`, which aggregates *per-kernel*
    compatibility failures across known candidates.
    """

    error_type = "https://api.backend.ai/probs/no-agents-in-resource-group"
    error_title = "Unavailable : Resource group has no candidate agents."

    _resource_group: str

    def __init__(self, resource_group: str) -> None:
        self._resource_group = resource_group
        super().__init__(f"No agents available in resource group '{resource_group}'")

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )

    def build_suggestion(self) -> Suggestion:
        # The resource group has no candidate agents at all; nothing the caller
        # can adjust on the request itself fixes this.
        return Suggestion(kind=SuggestionKind.NONE)


class NoAvailableAgentError(AgentSelectionError):
    """Raised when no agents can satisfy a kernel-group's resource requirement.

    The constructor accepts the structured inputs that describe *which*
    kernels failed and *why* each candidate agent was rejected, and composes
    the multi-line, bullet-formatted message itself.
    """

    error_type = "https://api.backend.ai/probs/no-available-agents"
    error_title = "Unavailable : No agents can be allocated at this time."

    _kernel_ids: Sequence[KernelId]
    _required_architecture: str
    _requested_slots: ResourceSlot
    _agent_errors: Mapping[AgentId, TrackerCompatibilityError]
    _designated_agent_ids: Sequence[AgentId] | None

    def __init__(
        self,
        *,
        kernel_ids: Sequence[KernelId],
        required_architecture: str,
        requested_slots: ResourceSlot,
        agent_errors: Mapping[AgentId, TrackerCompatibilityError],
        designated_agent_ids: Sequence[AgentId] | None = None,
    ) -> None:
        self._kernel_ids = kernel_ids
        self._required_architecture = required_architecture
        self._requested_slots = requested_slots
        self._agent_errors = agent_errors
        self._designated_agent_ids = designated_agent_ids
        super().__init__(self._build_message())

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )

    def build_suggestion(self) -> Suggestion:
        # Node-axis MIN: the smallest per-slot reduction that makes the kernel fit
        # on its best-fitting candidate node. Only resource-shortage nodes can be
        # fixed by reducing slots; container-limited nodes are not considered here.
        reduction = self._min_required_reduction()
        if self._designated_agent_ids is not None:
            # The user pinned specific agents; surface them so the caller can revise
            # the designation. A reduction is still offered when those agents only
            # lack resources (reducing could let the request fit a designated agent).
            return Suggestion(
                kind=SuggestionKind.CHANGE_DESIGNATED_AGENT,
                available_agent_ids=list(self._designated_agent_ids),
                required_reduction=reduction,
            )
        if reduction is not None:
            return Suggestion(
                kind=SuggestionKind.REDUCE_RESOURCE,
                required_reduction=reduction,
            )
        if any(isinstance(err, ContainerLimitExceededError) for err in self._agent_errors.values()):
            # No node is short on slots; the blocker is the per-agent container limit.
            return Suggestion(kind=SuggestionKind.REDUCE_CONTAINER)
        return Suggestion(kind=SuggestionKind.NONE)

    def _min_required_reduction(self) -> ResourceSlot | None:
        """Pick the smallest whole deficit vector across resource-short nodes.

        Heuristic comparison key: sum of the deficit's slot values. The precise
        cross-node selection policy is refined by the dry-run service (BA-6601).
        """
        deficits = [
            err.deficit()
            for err in self._agent_errors.values()
            if isinstance(err, InsufficientResourcesError)
        ]
        if not deficits:
            return None
        return min(deficits, key=lambda slot: sum(slot.values()))

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
        kernel_id_list = ", ".join(str(k) for k in self._kernel_ids)
        humanized_slots = self._requested_slots.to_humanized({})
        slot_str = " ".join(
            f"{k}={humanized_slots[k]}" for k, v in self._requested_slots.items() if v
        )
        return f"kernels [{kernel_id_list}] (arch={self._required_architecture}, slots={slot_str})"

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


class NoCompatibleAgentError(AgentSelectionError):
    """Raised when no agent matches the required architecture.

    Carries the structured architecture context so a dry-run can suggest which
    architectures the request could target instead.
    """

    error_type = "https://api.backend.ai/probs/no-compatible-agents"
    error_title = "No agents meet the resource requirements."

    _required_architecture: str
    _available_architectures: Sequence[str]

    def __init__(
        self,
        *,
        required_architecture: str,
        available_architectures: Sequence[str],
    ) -> None:
        self._required_architecture = required_architecture
        self._available_architectures = available_architectures
        super().__init__(
            f"No agents with required architecture '{required_architecture}'. "
            f"Available architectures: {', '.join(available_architectures)}"
        )

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )

    def build_suggestion(self) -> Suggestion:
        return Suggestion(
            kind=SuggestionKind.CHANGE_ARCH,
            available_archs=list(self._available_architectures),
        )


class BatchAgentSelectionFailedError(SchedulingError):
    """Aggregates per-requirement placement failures of a single batch selection."""

    error_type = "https://api.backend.ai/probs/batch-agent-selection-failed"
    error_title = "Some kernels could not be placed on any agent."

    _errors: Sequence[AgentSelectionError]

    def __init__(self, errors: Sequence[AgentSelectionError]) -> None:
        self._errors = errors
        super().__init__(self._build_message())

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )

    def failed_predicates(self) -> list[SchedulingPredicate]:
        predicates: list[SchedulingPredicate] = []
        for err in self._errors:
            predicates.extend(err.failed_predicates())
        return predicates

    def _build_message(self) -> str:
        header = f"{len(self._errors)} requirement(s) could not be placed"
        body = "\n".join((err.extra_msg or str(err)) for err in self._errors)
        return f"{header}:\n{body}"


# Per-agent compatibility check exceptions. These inherit from BackendAIError so
# every concrete subclass is forced to declare an `error_code` — otherwise a new
# compatibility error could silently leak with an undefined RFC-7807 code.
class TrackerCompatibilityError(BackendAIError, ABC):
    """Base exception for tracker compatibility checks."""

    error_type = "https://api.backend.ai/probs/agent-compatibility-failed"
    error_title = "Agent compatibility check failed."


class ArchitectureIncompatibleError(TrackerCompatibilityError):
    """Raised when agent architecture does not match the required architecture."""

    error_type = "https://api.backend.ai/probs/agent-architecture-mismatch"
    error_title = "Agent architecture does not match the requirement."

    _agent_id: AgentId
    _agent_arch: str
    _required_arch: str

    def __init__(self, agent_id: AgentId, agent_arch: str, required_arch: str) -> None:
        self._agent_id = agent_id
        self._agent_arch = agent_arch
        self._required_arch = required_arch
        super().__init__(
            f"Agent {agent_id} architecture '{agent_arch}'"
            f" does not match required architecture '{required_arch}'"
        )

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.MISMATCH,
        )


class InsufficientResourcesError(TrackerCompatibilityError):
    """Raised when agent does not have sufficient resources available."""

    error_type = "https://api.backend.ai/probs/agent-insufficient-resources"
    error_title = "Agent has insufficient resources."

    _agent_id: AgentId
    _requested_slots: ResourceSlot
    _available_slots: ResourceSlot
    _occupied_slots: ResourceSlot
    _insufficient_resources: dict[str, tuple[str, str]]

    def __init__(
        self,
        agent_id: AgentId,
        requested_slots: ResourceSlot,
        available_slots: ResourceSlot,
        occupied_slots: ResourceSlot,
        insufficient_resources: dict[str, tuple[str, str]],
    ) -> None:
        self._agent_id = agent_id
        self._requested_slots = requested_slots
        self._available_slots = available_slots
        self._occupied_slots = occupied_slots
        self._insufficient_resources = insufficient_resources

        # Build detailed message: one resource shortfall per indented line so that
        # upstream aggregators (e.g. NoAvailableAgentError) can newline-join cleanly.
        resource_lines = [
            f"  - {resource_name}: requested={requested}, available={available}"
            for resource_name, (requested, available) in insufficient_resources.items()
        ]
        details_msg = "\n".join(resource_lines)

        super().__init__(f"Agent {agent_id} has insufficient resources:\n{details_msg}")

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )

    def deficit(self) -> ResourceSlot:
        """Per-slot shortage on this agent: max(0, requested - available)."""
        diff = self._requested_slots - self._available_slots
        return ResourceSlot({
            slot_name: amount for slot_name, amount in diff.items() if amount > Decimal(0)
        })


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

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )
