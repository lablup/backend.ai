"""Response DTOs for session options sub-models.

Mirrors ``request.py`` field-by-field. Used by the resource-group admin
read path that returns the currently-configured
``default_session_options`` and (eventually) the per-session detail
view that exposes the frozen SessionOptions snapshot.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.common import ResourceSlotEntryInfo
from ai.backend.common.dto.manager.v2.session.types import ClusterModeEnum
from ai.backend.common.dto.manager.v2.session_options.types import (
    AgentSelectionPolicyEnum,
    FailurePolicyEnum,
)
from ai.backend.common.identifier.image import ImageID


class HandlerTimeoutEntryInfo(BaseResponseModel):
    """A single ``(handler_name, timeout_sec)`` entry."""

    handler_name: str = Field(
        description=("Handler identifier matching `SessionLifecycleHandler.name()`."),
    )
    timeout_sec: int | None = Field(
        description=(
            "Timeout in seconds; `null` means this handler is unbounded "
            "regardless of the `default` timeout."
        ),
    )


class SessionTimeoutsInfo(BaseResponseModel):
    """Handler-keyed timeout policy snapshot."""

    default: int | None = Field(
        description=(
            "Fallback timeout in seconds applied to handlers not "
            "listed in `by_handler`; `null` means unbounded."
        ),
    )
    by_handler: list[HandlerTimeoutEntryInfo] = Field(
        description="Per-handler timeout overrides.",
    )


class ResourceOptsInfo(BaseResponseModel):
    """Qualitative resource hints snapshot."""

    shmem: str | None = Field(
        description=(
            "Shared-memory size as a human-readable string "
            "(e.g. '64m'). `null` means 'use the runtime default'."
        ),
    )


class KernelExecutionSpecInfo(BaseResponseModel):
    """Resolved kernel execution spec snapshot."""

    image_id: ImageID | None = Field(
        description=("Container image identifier, or `null` if not resolved."),
    )
    resources: list[ResourceSlotEntryInfo] | None = Field(
        description="Quantitative resource request entries.",
    )
    resource_opts: ResourceOptsInfo | None = Field(
        description="Qualitative resource hints.",
    )
    environ: dict[str, str] | None = Field(
        description="Environment variables injected into the kernel.",
    )
    startup_command: str | None = Field(
        description="Command executed after kernel bootstrap.",
    )
    bootstrap_script: str | None = Field(
        description="Shell script executed before `startup_command`.",
    )
    starts_at: datetime | None = Field(
        description="Earliest start time for the kernel.",
    )
    batch_timeout_sec: int | None = Field(
        description="Soft deadline for BATCH-session user payload.",
    )


class KernelGroupInfo(BaseResponseModel):
    """Role + replica bundle snapshot."""

    role: str = Field(description="Role label for the group.")
    replica_count: int = Field(description="Number of kernels in the group.")
    execution_spec: KernelExecutionSpecInfo = Field(description="Resolved execution spec.")
    failure_policy: FailurePolicyEnum = Field(
        description="Frozen failure policy for this group.",
    )
    depends_on_roles: list[str] = Field(
        description=(
            "Role labels this group waits on before starting (schema-"
            "level only until #70 enforces it)."
        ),
    )


class SchedulingTargetInfo(BaseResponseModel):
    """Scheduling placement constraints snapshot."""

    designated_agents: list[str] = Field(
        description=(
            "Agent identifiers the session was targeted at (empty = no explicit preference)."
        ),
    )
    agent_selection_policy: AgentSelectionPolicyEnum = Field(
        description="How `designated_agents` was enforced.",
    )


class DefaultSessionOptionsInfo(BaseResponseModel):
    """Resource-group default session options snapshot."""

    priority: int = Field(description="Default scheduling priority.")
    is_preemptible: bool = Field(description="Default preemption flag.")
    cluster_mode: ClusterModeEnum = Field(description="Default cluster mode.")
    default_failure_policy: FailurePolicyEnum = Field(
        description=(
            "Resource-group fallback `failure_policy`; applied to each "
            "kernel group whose `failure_policy` and the session's "
            "`default_failure_policy` are both unset."
        ),
    )
    default_kernel_execution_spec: KernelExecutionSpecInfo | None = Field(
        description=(
            "Baseline kernel execution spec. `null` if the resource "
            "group does not pre-configure one."
        ),
    )
    timeouts: SessionTimeoutsInfo = Field(
        description="Default timeout policy.",
    )
    agent_selection_policy: AgentSelectionPolicyEnum = Field(
        description="Default agent selection policy.",
    )
