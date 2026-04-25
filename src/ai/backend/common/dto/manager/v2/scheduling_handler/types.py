"""Common types for scheduling handler DTO v2."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "SchedulingHandlerCategory",
    "SchedulingHandlerNode",
)


class SchedulingHandlerCategory(StrEnum):
    """Category of deployment-level handler for history separation.

    Mirrors :class:`ai.backend.manager.data.deployment.types.DeploymentHandlerCategory`
    values to keep the shared DTO layer independent from the manager package.
    """

    LIFECYCLE = "lifecycle"
    SCALING = "scaling"
    HEALTH = "health"


class SchedulingHandlerNode(BaseResponseModel):
    """Metadata describing a single deployment scheduling handler."""

    name: str = Field(description="Stable handler key used in deployment timeout maps.")
    category: SchedulingHandlerCategory = Field(
        description="Handler category classifying its scheduling axis."
    )
    description: str | None = Field(
        default=None,
        description=(
            "First line of the handler's docstring, if any. "
            "Null when the backing class has no docstring."
        ),
    )
