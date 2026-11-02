"""Shared conversion helpers between the ``DeploymentOptions`` DTO
surface (list-of-entries) and the data-layer :class:`DeploymentOptions`
domain object (dict-keyed).

Used by every adapter that reads or writes deployment options — the
per-deployment path and the per-resource-group default path.
"""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.deployment_options.request import (
    DeploymentOptionsInput,
)
from ai.backend.common.dto.manager.v2.deployment_options.response import (
    DeploymentHandlerOptionsInfo,
    DeploymentOptionsInfo,
    HandlerOptionsEntryInfo,
    HandlerOptionsInfo,
)
from ai.backend.common.dto.manager.v2.session_options.types import AgentSelectionPolicyEnum
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.manager.data.deployment.types import (
    DeploymentHandlerOptions,
    DeploymentOptions,
)
from ai.backend.manager.data.session.options import AgentSelectionPolicy, HandlerOptions

__all__ = (
    "agent_selection_policy_from_input",
    "deployment_handler_options_from_input",
    "deployment_options_to_info",
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
        agent_selection_policy=AgentSelectionPolicyEnum(options.agent_selection_policy.value),
    )


def deployment_handler_options_from_input(
    options: DeploymentOptionsInput,
    *,
    valid_handler_names: frozenset[str],
) -> DeploymentHandlerOptions:
    """Project the handler options of the payload into the domain model.

    Rejects a duplicate or unregistered ``handler_name`` with :class:`InvalidAPIParameters`.
    """
    by_handler: dict[str, HandlerOptions] = {}
    for entry in options.handler_options.by_handler:
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
            timeout=options.handler_options.default.timeout_sec,
            max_retry_count=options.handler_options.default.max_retry_count,
        ),
        by_handler=by_handler,
    )


def agent_selection_policy_from_input(
    options: DeploymentOptionsInput,
) -> AgentSelectionPolicy | None:
    """The policy the payload replaces with; ``None`` keeps the stored one."""
    if options.agent_selection_policy is None:
        return None
    return AgentSelectionPolicy(options.agent_selection_policy.value)
