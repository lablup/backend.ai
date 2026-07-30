"""
Exceptions for agent selection in sokovan scheduler.

An exclusion filter that leaves no candidates is an absolute failure
(``NoCompatibleAgentError``) and propagates as-is; a stateful filter that
leaves none is resolvable later (``NoAvailableAgentError``), so the
computation layer converts it into a ``PlacementFailure`` value and only
the batch wrapper turns those back into an error.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import BinarySize
from ai.backend.manager.sokovan.scheduler.exceptions import SchedulingError

from .types import PlacementFailure


def _humanize_slot(slot_name: ResourceSlotName, value: Decimal) -> str:
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


class NoAgentsInResourceGroupError(AgentSelectionError, web.HTTPServiceUnavailable):
    """Raised when the resource group has no candidate agents at all.

    A precondition violation, not a placement outcome: with no candidates
    there is nothing to compute against.
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


class NoCompatibleAgentError(AgentSelectionError, web.HTTPBadRequest):
    """Raised inside an exclusion filter's recorder step when no candidates
    survive it.

    An absolute failure: no state change (preemption included) can make the
    request placeable, so this propagates instead of becoming a
    :class:`PlacementFailure`. What the filter rejected is a property of the
    request — a designated agent that does not exist, an architecture no
    agent serves — so the caller has to change the request, hence 400 rather
    than the 503 its sibling returns when the group holds no agents at all.
    """

    error_type = "https://api.backend.ai/probs/no-compatible-agents"
    error_title = "No compatible agents for the request."

    filter_name: str
    failure_reason: str

    def __init__(self, filter_name: str, failure_reason: str) -> None:
        self.filter_name = filter_name
        self.failure_reason = failure_reason
        super().__init__(f"no agents passed the '{filter_name}' filter: {failure_reason}")

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class NoAvailableAgentError(AgentSelectionError):
    """Raised inside a stateful filter's recorder step when no candidates
    survive it.

    Resolvable later (resources free up or get reclaimed), so the
    computation layer turns this into a :class:`PlacementFailure` using the
    carried filter name and per-slot shortfall.
    """

    error_type = "https://api.backend.ai/probs/no-available-agents"
    error_title = "Unavailable : No agents can be allocated at this time."

    filter_name: str
    missing_slots: Mapping[ResourceSlotName, Decimal]
    missing_containers: int

    def __init__(
        self,
        filter_name: str,
        missing_slots: Mapping[ResourceSlotName, Decimal],
        missing_containers: int,
    ) -> None:
        self.filter_name = filter_name
        self.missing_slots = missing_slots
        self.missing_containers = missing_containers
        super().__init__(f"no agents passed the '{filter_name}' filter")

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class BatchAgentSelectionFailedError(AgentSelectionError):
    """The batch wrapper's rendering of computed placement failures.

    Carries the structured ``failures`` and composes the human-readable
    message used as the session's scheduling-failure reason.
    """

    error_type = "https://api.backend.ai/probs/batch-agent-selection-failed"
    error_title = "Some kernels could not be placed on any agent."

    failures: Sequence[PlacementFailure]

    def __init__(self, failures: Sequence[PlacementFailure]) -> None:
        self.failures = failures
        super().__init__(self._build_message())

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SCHEDULE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )

    def _build_message(self) -> str:
        lines = [f"{len(self.failures)} requirement(s) could not be placed:"]
        for failure in self.failures:
            req = failure.resource_requirement
            slot_str = " ".join(
                f"{name}={_humanize_slot(name, value)}"
                for name, value in req.requested_slots.slots.items()
                if value
            )
            lines.append(
                f"- requirement #{failure.requirement_index} "
                f"(containers={req.container_count}, arch={req.required_architecture}, "
                f"slots={slot_str}): no agents passed the '{failure.filter_name}' filter"
            )
            if failure.missing_slots:
                lines.extend(
                    f"  - {name}: missing={_humanize_slot(name, amount)}"
                    for name, amount in failure.missing_slots.items()
                )
            if failure.missing_containers:
                lines.append(f"  - containers: missing={failure.missing_containers}")
        return "\n".join(lines)
