"""Shared DTOs for session options (timeouts, kernel spec, ...).

These sub-models are used by both the per-session ``sessions.options``
surface (via ``EnqueueSessionInput.options``) and the per-resource-group
``scaling_groups.default_session_options`` surface. Domain-specific
Replace* inputs / payloads live in each domain's own request/response
modules (see ``session`` and ``resource_group``) to avoid cross-DTO
circular imports.
"""

from ai.backend.common.dto.manager.v2.session_options.request import (
    DefaultSessionOptionsInput,
    HandlerTimeoutEntryInput,
    KernelExecutionSpecInput,
    KernelGroupInput,
    ResourceOptsInput,
    SchedulingTargetInput,
    SessionOptionsInput,
    SessionTimeoutsInput,
)
from ai.backend.common.dto.manager.v2.session_options.response import (
    DefaultSessionOptionsInfo,
    HandlerTimeoutEntryInfo,
    KernelExecutionSpecInfo,
    KernelGroupInfo,
    ResourceOptsInfo,
    SchedulingTargetInfo,
    SessionTimeoutsInfo,
)
from ai.backend.common.dto.manager.v2.session_options.types import (
    AgentSelectionPolicyEnum,
    FailurePolicyEnum,
)

__all__ = (
    "AgentSelectionPolicyEnum",
    "DefaultSessionOptionsInfo",
    "DefaultSessionOptionsInput",
    "FailurePolicyEnum",
    "HandlerTimeoutEntryInfo",
    "HandlerTimeoutEntryInput",
    "KernelExecutionSpecInfo",
    "KernelExecutionSpecInput",
    "KernelGroupInfo",
    "KernelGroupInput",
    "ResourceOptsInfo",
    "ResourceOptsInput",
    "SchedulingTargetInfo",
    "SchedulingTargetInput",
    "SessionOptionsInput",
    "SessionTimeoutsInfo",
    "SessionTimeoutsInput",
)
