"""Request DTOs for deployment options sub-models."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel


class HandlerTimeoutEntryInput(BaseRequestModel):
    """A single ``(handler_name, timeout_sec)`` entry.

    Structured as a list-of-entries rather than a raw map so GraphQL
    and typed SDK clients can validate each entry individually.
    """

    handler_name: str = Field(
        min_length=1,
        description="Handler identifier (e.g. 'deploying-provisioning').",
    )
    timeout_sec: int | None = Field(
        default=None,
        ge=1,
        description="Timeout in seconds. Null means 'no timeout' for this handler.",
    )


class DeploymentTimeoutsInput(BaseRequestModel):
    """Handler-keyed timeout policy.

    ``default`` is the fallback applied to any handler not listed in
    ``by_handler``; leave ``null`` to make the default unbounded.
    """

    default: int | None = Field(
        default=None,
        ge=1,
        description="Fallback timeout in seconds; null means unbounded.",
    )
    by_handler: list[HandlerTimeoutEntryInput] = Field(
        default_factory=list,
        description=(
            "Per-handler timeout overrides. Duplicate handler_name entries are"
            " rejected by the server."
        ),
    )


class DeploymentOptionsInput(BaseRequestModel):
    """Per-deployment (or per-resource-group default) options payload."""

    timeouts: DeploymentTimeoutsInput = Field(
        description="Handler timeout policy.",
    )
