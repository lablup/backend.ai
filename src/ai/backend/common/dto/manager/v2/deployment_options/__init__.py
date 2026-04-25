"""Shared DTOs for deployment options (timeouts, etc.).

These core sub-models are used by both the per-deployment
``endpoints.options`` surface and the per-resource-group
``scaling_groups.default_deployment_options`` surface. Domain-specific
Replace* inputs / payloads live in each domain's own request/response
modules (see ``deployment`` and ``resource_group``) to avoid cross-DTO
circular imports.
"""

from ai.backend.common.dto.manager.v2.deployment_options.request import (
    DeploymentOptionsInput,
    DeploymentTimeoutsInput,
    HandlerTimeoutEntryInput,
)
from ai.backend.common.dto.manager.v2.deployment_options.response import (
    DeploymentOptionsInfo,
    DeploymentTimeoutsInfo,
    HandlerTimeoutEntryInfo,
)

__all__ = (
    "DeploymentOptionsInfo",
    "DeploymentOptionsInput",
    "DeploymentTimeoutsInfo",
    "DeploymentTimeoutsInput",
    "HandlerTimeoutEntryInfo",
    "HandlerTimeoutEntryInput",
)
