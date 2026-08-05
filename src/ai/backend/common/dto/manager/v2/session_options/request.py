"""Request DTOs for session options sub-models.

These Input shapes are shared by:

  - ``EnqueueSessionInput.options`` (per-session request — fields may
    be null, in which case the resolver falls back to the resource
    group default then to the field default).
  - ``ReplaceResourceGroupDefaultSessionOptionsInput.options`` (admin
    replace payload — all fields are expected to be present; the
    service layer performs additional validation).

The shapes intentionally mirror
``data/session/options.py`` so adapter code is a field-by-field
mapping rather than a reshape.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.v2.common import (
    BinarySizeInput,
    MountItemInput,
    ResourceSlotEntryInput,
)
from ai.backend.common.dto.manager.v2.session.types import ClusterModeEnum
from ai.backend.common.dto.manager.v2.session_options.types import (
    AgentSelectionPolicyEnum,
    FailurePolicyEnum,
)
from ai.backend.common.identifier.image import ImageID


class HandlerOptionsInput(BaseRequestModel):
    """Per-handler scheduler policy fields (no handler name).

    Used as the ``default`` slot inside ``SessionHandlerOptionsInput``.
    Field-level ``null`` means "no limit" — the corresponding
    classification simply does not fire (timeout-elapsed or retry-
    exhausted) on that dimension.
    """

    timeout_sec: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Phase timeout in seconds. `null` disables the timeout — "
            "the phase may run indefinitely."
        ),
    )
    max_retry_count: int | None = Field(
        default=None,
        ge=0,
        description=(
            "Per-phase retry budget. `null` on the wire means "
            "'no override' and inherits the data-layer default "
            "(currently `5`); set explicitly to disable the retry "
            "limit (`give_up` never fires)."
        ),
    )


class HandlerOptionsEntryInput(HandlerOptionsInput):
    """A single ``(handler_name, options)`` entry.

    Structured as a list entry rather than a dict value so GraphQL and
    typed SDK clients can validate each pair individually. The server
    rejects duplicate ``handler_name`` within the same ``by_handler``
    list.
    """

    handler_name: str = Field(
        min_length=1,
        description=(
            "Handler identifier obtained from "
            "`SessionLifecycleHandler.name()` (e.g. 'schedule-sessions', "
            "'start-sessions'). See the scheduler handler catalog API "
            "for the authoritative list."
        ),
    )


class SessionHandlerOptionsInput(BaseRequestModel):
    """Handler-keyed scheduler policy for one session.

    Resolution per handler name: `by_handler[name]` if present,
    otherwise `default`. Within a chosen entry, any field-level `null`
    falls back to the corresponding field on `default`.
    """

    default: HandlerOptionsInput = Field(
        default_factory=HandlerOptionsInput,
        description=(
            "Fallback per-handler policy applied to any scheduler "
            "handler not overridden by `by_handler`."
        ),
    )
    by_handler: list[HandlerOptionsEntryInput] = Field(
        default_factory=list,
        description=(
            "Per-handler overrides. Each entry binds a handler name to a `HandlerOptions` payload."
        ),
    )


class ResourceOptsInput(BaseRequestModel):
    """Qualitative resource hints applied to each kernel in the group.

    Kept separate from quantitative resource slots (CPU/memory/GPU):
    these fields are pure hints the runtime may consult independently
    of the scheduler's admission calculus.
    """

    shmem: BinarySizeInput | None = Field(
        default=None,
        description=(
            "Shared-memory size for the kernel container. Accepts byte "
            "counts or human-readable strings like '64m', '1g'. "
            "Fallback chain: request → resource-group default → "
            "`DEFAULT_SHARED_MEMORY_SIZE`."
        ),
    )


class KernelExecutionSpecInput(BaseRequestModel):
    """Per-kernel execution spec shared by all replicas of one group.

    Every field is optional. The resolver fills gaps from
    `ScalingGroupRow.default_session_options.default_kernel_execution_spec`
    before a session is enqueued; any remaining gaps are surfaced as
    validation errors (e.g. an image must ultimately be resolved).
    """

    image_id: ImageID | None = Field(
        default=None,
        description=(
            "Container image identifier. When omitted, adapters may "
            "resolve it from the `(image_canonical, architecture)` "
            "pair carried alongside in the request envelope."
        ),
    )
    resources: list[ResourceSlotEntryInput] | None = Field(
        default=None,
        description=(
            "Quantitative resource request (cpu, mem, accelerators) "
            "as a list of `{resource_type, quantity}` entries. Subject "
            "to the caller's resource policy after scheduler "
            "admission."
        ),
    )
    resource_opts: ResourceOptsInput | None = Field(
        default=None,
        description="Qualitative resource hints (shared memory, ...).",
    )
    environ: dict[str, str] | None = Field(
        default=None,
        description=(
            "Environment variables injected on top of image labels "
            "and the keypair bootstrap environ at container start."
        ),
    )
    mounts: list[MountItemInput] | None = Field(
        default=None,
        description=(
            "VFolder mounts for the kernel. Resolved to typed entries "
            "by the adapter layer. Per-kernel override support lives "
            "in task #33."
        ),
    )
    startup_command: str | None = Field(
        default=None,
        description=(
            "Command executed after kernel bootstrap. `null` falls "
            "back to the image's declared CMD."
        ),
    )
    bootstrap_script: str | None = Field(
        default=None,
        description=(
            "Shell script executed before `startup_command`. `null` skips the bootstrap step."
        ),
    )
    starts_at: datetime | None = Field(
        default=None,
        description=(
            "Earliest start time for this kernel. `null` means start "
            "immediately on schedule. Role-ordered startup is expressed "
            "by staggered `starts_at` values across kernel groups."
        ),
    )
    batch_timeout_sec: int | None = Field(
        default=None,
        ge=0,
        description=(
            "BATCH-session soft deadline in seconds for the whole run. "
            "Independent of `SessionHandlerOptionsInput.by_handler`, "
            "which tracks scheduler-loop handlers rather than user "
            "payload execution."
        ),
    )


class KernelGroupInput(BaseRequestModel):
    """A role + replica bundle carrying one `KernelExecutionSpecInput`.

    Single-kernel sessions map to one group with `role='main'` and
    `replica_count=1`. Multi-node / multi-role sessions add further
    groups (e.g. `role='worker'`, `replica_count=N`).
    """

    role: str = Field(
        min_length=1,
        description=(
            "Free-form role label. Used for generating `cluster_role` / "
            "`cluster_hostname` in the preparer and as the identifier "
            "that other groups' `depends_on_roles` may reference. "
            "`'main'` conventionally marks the leader kernel."
        ),
    )
    replica_count: int = Field(
        ge=1,
        description=(
            "Number of kernels to create for this role. Each replica "
            "receives its own `cluster_idx` within the group."
        ),
    )
    execution_spec: KernelExecutionSpecInput | None = Field(
        default=None,
        description=(
            "Per-group execution spec override. When `null`, the group "
            "inherits `SessionOptionsInput.default_kernel_execution_spec` "
            "(or the resource group's default) unchanged."
        ),
    )
    failure_policy: FailurePolicyEnum | None = Field(
        default=None,
        description=(
            "Group-level failure policy. `null` inherits "
            "`SessionOptionsInput.default_failure_policy` at resolve "
            "time. The chosen policy is frozen onto the session "
            "snapshot at enqueue."
        ),
    )
    depends_on_roles: list[str] = Field(
        default_factory=list,
        description=(
            "Role labels of other kernel groups in the same session "
            "that must reach a ready state before this group starts. "
            "Scheduler enforcement ships in a follow-up task (#70)."
        ),
    )


class SchedulingTargetInput(BaseRequestModel):
    """Scheduler placement constraints for the session."""

    designated_agents: list[str] | None = Field(
        default=None,
        description=(
            "Explicit agent identifiers the caller prefers. `null` or "
            "empty means 'no explicit preference'."
        ),
    )
    agent_selection_policy: AgentSelectionPolicyEnum | None = Field(
        default=None,
        description=(
            "How `designated_agents` is enforced. `null` inherits the resource group default."
        ),
    )


class SessionOptionsInput(BaseRequestModel):
    """Per-session options payload carried inside `EnqueueSessionInput`.

    Every field is optional. Missing fields are filled in by the
    resolver using the resource group's `default_session_options`, then
    the Python field defaults.
    """

    priority: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description=(
            "Scheduling priority; higher values win at schedule time. "
            "Persists to `SessionRow.priority` so existing WHERE/"
            "ORDER BY queries against the column keep working."
        ),
    )
    is_preemptible: bool | None = Field(
        default=None,
        description=(
            "Whether higher-priority incoming sessions may preempt "
            "this session once running. Persists to "
            "`SessionRow.is_preemptible`."
        ),
    )
    cluster_mode: ClusterModeEnum | None = Field(
        default=None,
        description=(
            "Placement constraint: `SINGLE_NODE` forces every kernel "
            "onto the same agent; `MULTI_NODE` allows spread. Persists "
            "to `SessionRow.cluster_mode`."
        ),
    )
    default_failure_policy: FailurePolicyEnum | None = Field(
        default=None,
        description=(
            "Session-wide fallback used when a `KernelGroupInput` "
            "omits its own `failure_policy`. `null` defers to the "
            "resource group's default. Not persisted by itself — each "
            "group's final policy is resolved and frozen at enqueue."
        ),
    )
    default_kernel_execution_spec: KernelExecutionSpecInput | None = Field(
        default=None,
        description=(
            "Shared baseline execution spec applied to every kernel "
            "group unless the group provides its own `spec`. When "
            "`null`, the resource group's default is used; if neither "
            "supplies a spec, required fields must come from the group "
            "itself."
        ),
    )
    kernel_groups: list[KernelGroupInput] | None = Field(
        default=None,
        description=(
            "Explicit kernel-group layout. `null` or empty auto-"
            "generates one group of `role='main'`, `replica_count=1` "
            "from `default_kernel_execution_spec`."
        ),
    )
    scheduling_target: SchedulingTargetInput | None = Field(
        default=None,
        description="Scheduler placement constraints.",
    )
    handler_options: SessionHandlerOptionsInput | None = Field(
        default=None,
        description="Handler-keyed scheduler policy for this session.",
    )


class DefaultSessionOptionsInput(BaseRequestModel):
    """Resource-group default session options (admin replace payload).

    Unlike `SessionOptionsInput`, this shape intentionally omits
    per-session-only fields (`kernel_groups`,
    `scheduling_target.designated_agents`) — those are inherently
    request-time decisions.
    """

    priority: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Default scheduling priority for new sessions.",
    )
    is_preemptible: bool | None = Field(
        default=None,
        description="Default preemption flag for new sessions.",
    )
    cluster_mode: ClusterModeEnum | None = Field(
        default=None,
        description="Default `cluster_mode` for new sessions.",
    )
    default_failure_policy: FailurePolicyEnum | None = Field(
        default=None,
        description=(
            "Resource-group fallback `failure_policy`. Used when "
            "neither the session request nor a kernel group supplies "
            "one. The final per-group value is frozen onto the session "
            "at enqueue."
        ),
    )
    default_kernel_execution_spec: KernelExecutionSpecInput | None = Field(
        default=None,
        description=(
            "Default kernel execution spec baseline. Supplies missing "
            "fields (shmem, environ, ...) into every kernel group that "
            "does not override them."
        ),
    )
    handler_options: SessionHandlerOptionsInput | None = Field(
        default=None,
        description="Default handler-keyed scheduler policy.",
    )
    agent_selection_policy: AgentSelectionPolicyEnum | None = Field(
        default=None,
        description=("Default value for `SchedulingTargetInput.agent_selection_policy`."),
    )
