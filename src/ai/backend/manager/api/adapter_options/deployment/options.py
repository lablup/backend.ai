"""Shared conversion helpers between the ``DeploymentOptions`` DTO
surface (list-of-entries) and the data-layer :class:`DeploymentOptions`
domain object (dict-keyed).

Used by every adapter that reads or writes deployment options — the
per-deployment path and the per-resource-group default path.
"""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.deployment_options import (
    DeploymentOptionsInfo,
    DeploymentOptionsInput,
    DeploymentTimeoutsInfo,
    DeploymentTimeoutsInput,
    HandlerTimeoutEntryInfo,
)
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.data.deployment.types import (
    DeploymentOptions,
    DeploymentTimeouts,
)

__all__ = (
    "deployment_options_to_info",
    "deployment_options_from_input",
)


def _timeouts_to_info(timeouts: DeploymentTimeouts) -> DeploymentTimeoutsInfo:
    entries = [
        HandlerTimeoutEntryInfo(handler_name=name, timeout_sec=seconds)
        for name, seconds in timeouts.by_handler.items()
    ]
    # Keep the output order deterministic so clients see a stable view
    # across successive reads.
    entries.sort(key=lambda e: e.handler_name)
    return DeploymentTimeoutsInfo(default=timeouts.default, by_handler=entries)


def deployment_options_to_info(options: DeploymentOptions) -> DeploymentOptionsInfo:
    """Project the domain model to the API response DTO."""
    return DeploymentOptionsInfo(timeouts=_timeouts_to_info(options.timeouts))


def _timeouts_from_input(
    timeouts: DeploymentTimeoutsInput,
    valid_handler_names: frozenset[str],
) -> DeploymentTimeouts:
    by_handler: dict[str, int | None] = {}
    for entry in timeouts.by_handler:
        if entry.handler_name in by_handler:
            raise InvalidAPIParameters(
                f"Duplicate handler_name in timeouts.by_handler: {entry.handler_name!r}"
            )
        if entry.handler_name not in valid_handler_names:
            raise InvalidAPIParameters(
                f"Unknown handler_name {entry.handler_name!r};"
                f" valid names: {sorted(valid_handler_names)}"
            )
        by_handler[entry.handler_name] = entry.timeout_sec
    return DeploymentTimeouts(default=timeouts.default, by_handler=by_handler)


def deployment_options_from_input(
    options: DeploymentOptionsInput,
    *,
    valid_handler_names: frozenset[str],
) -> DeploymentOptions:
    """Validate and project an incoming API payload into the domain
    model.

    ``valid_handler_names`` is the runtime set of handlers registered on
    the deployment coordinator; any ``by_handler`` key outside this set
    is rejected as :class:`InvalidAPIParameters`. Duplicate keys are
    likewise rejected.
    """
    return DeploymentOptions(timeouts=_timeouts_from_input(options.timeouts, valid_handler_names))
