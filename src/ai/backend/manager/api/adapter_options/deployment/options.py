"""Shared conversion helpers between the ``DeploymentOptions`` DTO
surface (list-of-entries) and the data-layer :class:`DeploymentOptions`
domain object (dict-keyed).

Used by every adapter that reads or writes deployment options — the
per-deployment path and the per-resource-group default path.
"""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.deployment_options import (
    DeploymentHandlerOptionsInfo,
    DeploymentHandlerOptionsInput,
    DeploymentOptionsInfo,
    DeploymentOptionsInput,
)
from ai.backend.common.dto.manager.v2.session_options import (
    HandlerOptionsEntryInfo,
    HandlerOptionsInfo,
)
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.data.deployment.types import (
    DeploymentHandlerOptions,
    DeploymentOptions,
)
from ai.backend.manager.data.session.options import HandlerOptions

__all__ = (
    "deployment_options_to_info",
    "deployment_options_from_input",
)


def _handler_options_to_info(
    options: DeploymentHandlerOptions,
) -> DeploymentHandlerOptionsInfo:
    entries = [
        HandlerOptionsEntryInfo(
            handler_name=name,
            timeout_sec=opts.timeout,
            max_retry_count=opts.max_retry_count,
        )
        for name, opts in options.by_handler.items()
    ]
    # Keep the output order deterministic so clients see a stable view
    # across successive reads.
    entries.sort(key=lambda e: e.handler_name)
    return DeploymentHandlerOptionsInfo(
        default=HandlerOptionsInfo(
            timeout_sec=options.default.timeout,
            max_retry_count=options.default.max_retry_count,
        ),
        by_handler=entries,
    )


def deployment_options_to_info(options: DeploymentOptions) -> DeploymentOptionsInfo:
    """Project the domain model to the API response DTO."""
    return DeploymentOptionsInfo(
        handler_options=_handler_options_to_info(options.handler_options),
    )


def _handler_options_from_input(
    options: DeploymentHandlerOptionsInput,
    valid_handler_names: frozenset[str],
) -> DeploymentHandlerOptions:
    by_handler: dict[str, HandlerOptions] = {}
    for entry in options.by_handler:
        if entry.handler_name in by_handler:
            raise InvalidAPIParameters(
                f"Duplicate handler_name in handler_options.by_handler: {entry.handler_name!r}"
            )
        if entry.handler_name not in valid_handler_names:
            raise InvalidAPIParameters(
                f"Unknown handler_name {entry.handler_name!r};"
                f" valid names: {sorted(valid_handler_names)}"
            )
        by_handler[entry.handler_name] = HandlerOptions(
            timeout=entry.timeout_sec,
            max_retry_count=entry.max_retry_count,
        )
    return DeploymentHandlerOptions(
        default=HandlerOptions(
            timeout=options.default.timeout_sec,
            max_retry_count=options.default.max_retry_count,
        ),
        by_handler=by_handler,
    )


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
    return DeploymentOptions(
        handler_options=_handler_options_from_input(options.handler_options, valid_handler_names),
    )
