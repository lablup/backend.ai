"""Session options schema.

Mirrors the shape of ``data/deployment/types.py::DeploymentOptions`` and
``DeploymentHandlerOptions`` so the two subsystems share identical
handler-keyed scheduler-policy semantics. Every option in this module
is stored on either ``SessionRow`` individual columns or
``SessionRow.options`` JSONB (resp.
``ScalingGroupRow.default_session_options`` JSONB) and reassembled into
the dataclasses here at read time.

See ``SessionOptions`` docstring for the column vs JSONB split.
"""

from __future__ import annotations

import enum
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from pydantic import ConfigDict, Field

from ai.backend.common.identifier.image import ImageID
from ai.backend.common.types import (
    AgentId,
    BackendAISchema,
    BinarySizeField,
    ClusterMode,
    MountInfoEntry,
    ResourceSlotEntry,
)


class _OptionsBaseModel(BackendAISchema):
    """Base for session-options data types.

    ``arbitrary_types_allowed`` lets us use ``ResourceSlot`` (UserDict)
    and ``MountInfoEntry`` (itself a BaseModel) directly as field types
    without adapter glue. Mirrors ``data/deployment/types.ConfiguredModel``.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)


class InternalDataExtras(_OptionsBaseModel):
    """Request-envelope fields that feed ``KernelSpec.internal_data``.

    Carried directly on :class:`SessionSpecDraft` so the caller-supplied
    sudo toggle and model-definition overlay reach the preparer chain
    through the draft itself rather than controller kwargs. Separate
    from any DB-sourced inputs (dotfiles, ssh keypair) which the
    scheduler repository fetches separately at enqueue time.
    """

    sudo_session_enabled: bool = Field(
        default=False,
        description=("Enable sudo-backed user bootstrap inside the kernel container."),
    )
    model_definition_path: str | None = Field(
        default=None,
        description=(
            "Path (inside the model vfolder) to the deployment's model-"
            "definition YAML. Deployment-originated sessions populate "
            "this so the agent can locate the file without re-reading "
            "the mounted vfolder."
        ),
    )
    model_definition: Mapping[str, Any] | None = Field(
        default=None,
        description=(
            "Already-resolved model-definition payload. When set, the "
            "agent skips the on-disk YAML read entirely (task #32)."
        ),
    )


class FailurePolicy(enum.StrEnum):
    """Per-KernelGroup policy for how startup failures propagate to the
    session. Concrete enforcement lives in a follow-up task (#68); this
    enum only records the intent at enqueue time so a later default
    change on the resource group does not retroactively alter live
    sessions.
    """

    STRICT = "strict"
    """Any replica failure in this group fails the whole session."""

    BOOT_ALL = "boot-all"
    """All replicas must finish booting before the session transitions
    to RUNNING; a late failure still fails the session."""

    TOLERANT = "tolerant"
    """Session keeps running as long as at least one replica stays up;
    individual replica failures are logged but non-fatal."""


class AgentSelectionPolicy(enum.StrEnum):
    """Scheduling constraint for ``SchedulingTarget.designated_agents``."""

    STRICT = "strict"
    """Schedule only onto ``designated_agents``; fail the schedule if
    none are available."""

    PREFERRED = "preferred"
    """Prefer ``designated_agents`` but fall back to any eligible agent
    when they have no capacity."""


class HandlerOptions(_OptionsBaseModel):
    """Per-handler runtime policy entry.

    Carries every per-handler knob the scheduler coordinator consults
    when deciding what to do after a handler invocation. Each field's
    classification (expired / give_up) only fires when the field is
    set; ``None`` means "no limit on this dimension".

    - ``timeout``: maximum wall-clock seconds the session may stay in
      the phase a given handler operates on. Default ``None`` —
      operators opt in by setting per-handler timeouts.
    - ``max_retry_count``: maximum retry attempts before the
      coordinator gives up on the session for that phase. Default
      ``5`` mirrors the legacy ``SERVICE_MAX_RETRIES`` global so the
      coordinator continues to give up after five attempts without
      operator opt-in. Set to ``None`` explicitly to disable the
      retry limit for a handler.
    """

    timeout: int | None = Field(
        default=None,
        description=(
            "Phase timeout in seconds for the handler. `None` disables "
            "the timeout — the phase may run indefinitely."
        ),
    )
    max_retry_count: int | None = Field(
        default=5,
        description=(
            "Per-handler retry budget. The coordinator transitions the "
            "session through `give_up` once `phase_attempts` reaches "
            "this value. Default `5` matches the legacy "
            "`SERVICE_MAX_RETRIES` threshold; `None` disables the "
            "retry limit so `give_up` never fires for this handler."
        ),
    )

    def is_retry_exhausted(self, phase_attempts: int) -> bool:
        """Whether the retry budget has been spent for the given phase.

        Returns ``False`` when ``max_retry_count`` is ``None`` (no limit
        configured) so callers do not have to special-case the unbounded
        policy.
        """
        if self.max_retry_count is None:
            return False
        return phase_attempts >= self.max_retry_count

    def is_timed_out(self, phase_started_at: datetime | None, current_time: datetime) -> bool:
        """Whether the phase has run past the configured timeout.

        Returns ``False`` when ``timeout`` is ``None`` (no limit
        configured) or ``phase_started_at`` is ``None`` (the phase has
        not started yet) so callers do not have to special-case either.
        Both timestamps are expected to share the same tzinfo (typically
        sourced from PostgreSQL ``timestamptz`` columns).
        """
        if self.timeout is None or phase_started_at is None:
            return False
        elapsed = (current_time - phase_started_at).total_seconds()
        return elapsed > self.timeout


class SessionHandlerOptions(_OptionsBaseModel):
    """Handler-keyed scheduler policy.

    Mirrors ``DeploymentHandlerOptions``. Resolution for a given
    ``handler_name`` (= ``SessionLifecycleHandler.name()``): the entry
    in ``by_handler`` if present, otherwise ``default``. Each
    ``HandlerOptions`` field falls back to ``default``'s value when the
    per-handler override leaves it ``None``.
    """

    default: HandlerOptions = Field(
        default_factory=HandlerOptions,
        description=(
            "Fallback policy applied to any handler not overridden in "
            "`by_handler`. Picks up `HandlerOptions`' field defaults "
            "(timeout unbounded, max_retry_count=5)."
        ),
    )
    by_handler: dict[str, HandlerOptions] = Field(
        default_factory=dict,
        description=(
            "Per-handler overrides keyed by "
            "`SessionLifecycleHandler.name()`. Field-level `None` in "
            "an override falls back to the corresponding field on "
            "`default`."
        ),
    )

    def resolve(self, handler_name: str) -> HandlerOptions:
        override = self.by_handler.get(handler_name)
        if override is None:
            return self.default
        return HandlerOptions(
            timeout=override.timeout if override.timeout is not None else self.default.timeout,
            max_retry_count=(
                override.max_retry_count
                if override.max_retry_count is not None
                else self.default.max_retry_count
            ),
        )


class ResourceOpts(_OptionsBaseModel):
    """Per-kernel qualitative resource hints.

    Distinct from ``ResourceSlot`` which carries quantitative slots.
    """

    shmem: BinarySizeField | None = Field(
        default=None,
        description=(
            "Shared-memory size for the kernel container. Fallback "
            "chain: request -> resource-group default -> "
            "DEFAULT_SHARED_MEMORY_SIZE."
        ),
    )


class SchedulingTarget(_OptionsBaseModel):
    """Where and how the session may be placed.

    ``designated_agents`` maps to the ``SessionRow.designated_agent_ids``
    column while ``agent_selection_policy`` lives inside
    ``SessionRow.options`` JSONB. The resource group itself is kept on
    ``SessionRow.scaling_group_name`` so existing queries do not need
    a JSONB path operator.
    """

    designated_agents: list[AgentId] = Field(
        default_factory=list,
        description=(
            "Agent identifiers the session was explicitly targeted at. "
            "Empty means no explicit preference."
        ),
    )
    agent_selection_policy: AgentSelectionPolicy = Field(
        default=AgentSelectionPolicy.PREFERRED,
        description=(
            "How `designated_agents` is enforced at scheduling time "
            "(STRICT fails without capacity, PREFERRED falls back)."
        ),
    )


class KernelExecutionSpec(_OptionsBaseModel):
    """Per-kernel execution spec.

    Used both as the shared baseline in
    ``DefaultSessionOptions.default_kernel_execution_spec`` (merged
    into every group unless overridden) and as the per-group override on
    ``KernelGroup.execution_spec``. All fields are resolved; ``None`` on the
    optional fields carries real meaning (for example ``starts_at=None``
    = "start immediately on schedule").
    """

    image_id: ImageID = Field(
        description=(
            "Container image identifier resolved from canonical+arch "
            "or UUID at the request-adapter layer."
        ),
    )
    resources: list[ResourceSlotEntry] = Field(
        default_factory=list,
        description=(
            "Quantitative resource request (CPU, memory, accelerators) "
            "as a list of typed entries. Must fit the caller's resource "
            "policy after scheduler admission. Empty when the caller "
            "lets the resource group default or image minimum decide."
        ),
    )
    resource_opts: ResourceOpts = Field(
        default_factory=ResourceOpts,
        description="Qualitative resource hints such as shared memory.",
    )
    environ: Mapping[str, str] = Field(
        default_factory=dict,
        description=(
            "Environment variables injected on top of image labels and "
            "the keypair bootstrap environ at container start."
        ),
    )
    mounts: list[MountInfoEntry] = Field(
        default_factory=list,
        description=(
            "Per-kernel vfolder mount request list. Entry permissions "
            "may be ``None`` to let the resolver adopt the stored "
            "vfolder permission at enqueue time. The scheduler "
            "repository resolves each entry to a typed ``VFolderMount`` "
            "and stamps the result onto ``KernelSpec.vfolder_mounts`` "
            "— per-kernel override (task #33) is expressible by "
            "emitting different entries per kernel group."
        ),
    )
    startup_command: str | None = Field(
        default=None,
        description=(
            "Command executed after kernel bootstrap. `None` defers to the image's declared CMD."
        ),
    )
    bootstrap_script: str | None = Field(
        default=None,
        description=(
            "Shell script executed before `startup_command`. `None` skips the bootstrap step."
        ),
    )
    starts_at: datetime | None = Field(
        default=None,
        description=(
            "Earliest start time for this kernel. `None` means start "
            "immediately on schedule; role-ordered startup is expressed "
            "by staggered values across kernel groups."
        ),
    )
    batch_timeout_sec: int | None = Field(
        default=None,
        description=(
            "BATCH-session soft deadline in seconds for the user "
            "payload. Independent of `SessionHandlerOptions.by_handler` "
            "which tracks scheduler-loop handlers."
        ),
    )


class KernelGroup(_OptionsBaseModel):
    """A role + replica bundle sharing one ``KernelExecutionSpec``.

    Single-kernel sessions are one group with ``role='main',
    replica_count=1``. Multi-node / multi-role sessions add further
    groups (for example ``role='worker', replica_count=N``). Replica-
    level ``cluster_idx`` assignments happen in the preparer.
    """

    role: str = Field(
        description=(
            "Free-form role label. Drives `cluster_role` / "
            "`cluster_hostname` generation and is the target that "
            "other groups' `depends_on_roles` references. `'main'` "
            "conventionally marks the leader kernel."
        ),
    )
    replica_count: int = Field(
        ge=1,
        description=(
            "Number of kernels to create for this role. Each replica "
            "receives its own `cluster_idx` within the group."
        ),
    )
    execution_spec: KernelExecutionSpec = Field(
        description="Resolved execution spec shared by every replica.",
    )
    failure_policy: FailurePolicy = Field(
        default=FailurePolicy.STRICT,
        description=(
            "Group-level failure policy, frozen at enqueue time. "
            "Later resource-group default changes do not apply "
            "retroactively. Defaults to STRICT when neither the "
            "request nor a preparer rule supplies a value."
        ),
    )
    depends_on_roles: list[str] = Field(
        default_factory=list,
        description=(
            "Role labels of other kernel groups that must reach a "
            "ready state before this group may start. Enforcement "
            "lives in task #70."
        ),
    )


class DefaultSessionOptions(_OptionsBaseModel):
    """Baseline options used when a session create request omits fields.

    Stored as ``ScalingGroupRow.default_session_options`` JSONB. Fields
    that only make sense per session (``kernel_groups``,
    ``designated_agents``, ``cluster_size``) do not live here.
    ``default_kernel_execution_spec`` seeds
    ``KernelGroup.execution_spec`` when the request does not provide an
    explicit per-group spec.
    """

    priority: int = Field(
        default=10,
        description="Default scheduling priority for new sessions.",
    )
    is_preemptible: bool = Field(
        default=True,
        description="Default preemption flag for new sessions.",
    )
    cluster_mode: ClusterMode = Field(
        default=ClusterMode.SINGLE_NODE,
        description=(
            "SINGLE_NODE: place every kernel on the same agent. "
            "MULTI_NODE: allow kernels to be spread across agents."
        ),
    )
    default_failure_policy: FailurePolicy = Field(
        default=FailurePolicy.STRICT,
        description=(
            "Fallback `failure_policy` applied when a KernelGroup "
            "omits its own and the session request does not override "
            "it either. Frozen into each group at session enqueue — "
            "later changes here do not retroactively alter live "
            "sessions."
        ),
    )
    default_kernel_execution_spec: KernelExecutionSpec | None = Field(
        default=None,
        description=(
            "Baseline kernel execution spec. `None` means the resource "
            "group has no pre-configured default and the request must "
            "supply all required fields itself."
        ),
    )
    handler_options: SessionHandlerOptions = Field(
        default_factory=SessionHandlerOptions,
        description="Default handler-keyed scheduler policy (timeout + retry).",
    )
    agent_selection_policy: AgentSelectionPolicy = Field(
        default=AgentSelectionPolicy.PREFERRED,
        description=(
            "Default for `SchedulingTarget.agent_selection_policy` "
            "when the request does not override it."
        ),
    )


class SessionStoredOptions(_OptionsBaseModel):
    """Subset of ``SessionOptions`` that lands in ``SessionRow.options``
    JSONB.

    The fields that already have dedicated ``SessionRow`` columns
    (``priority``, ``is_preemptible``, ``cluster_mode``, ``cluster_size``,
    ``scaling_group_name``, ``designated_agent_ids``) deliberately do
    not live here — keeping them as columns preserves existing
    ``WHERE`` / ``ORDER BY`` queries and indexes without JSONB path
    operators. Everything else is stored in this blob.

    This is the ORM-facing shape plugged into ``PydanticColumn``. The
    full logical view is ``SessionOptions`` which composes this JSONB
    with the individual columns at read time.
    """

    kernel_groups: list[KernelGroup] = Field(
        default_factory=list,
        description=(
            "Frozen kernel-group layout for the session. Empty on "
            "legacy rows that predate this schema — callers fall back "
            "to the SessionRow column-level fields in that case."
        ),
    )
    handler_options: SessionHandlerOptions = Field(
        default_factory=SessionHandlerOptions,
        description="Frozen handler-keyed scheduler policy (timeout + retry).",
    )
    agent_selection_policy: AgentSelectionPolicy = Field(
        default=AgentSelectionPolicy.PREFERRED,
        description=(
            "Resolved `SchedulingTarget.agent_selection_policy`. "
            "Lives in the JSONB rather than its own column because "
            "existing queries never filter by this field."
        ),
    )


class SessionOptions(_OptionsBaseModel):
    """Resolved options for a single session (in-memory view).

    Reassembled at read time from ``SessionRow`` individual columns plus
    the ``options`` JSONB:

      | Field                                          | Location                                       |
      | ---------------------------------------------- | ---------------------------------------------- |
      | ``priority``                                   | ``SessionRow.priority`` column                 |
      | ``is_preemptible``                             | ``SessionRow.is_preemptible`` column           |
      | ``cluster_mode``                               | ``SessionRow.cluster_mode`` column             |
      | ``cluster_size``                               | ``SessionRow.cluster_size`` column             |
      | ``scheduling_target.designated_agents``        | ``SessionRow.designated_agent_ids`` column     |
      | ``scheduling_target.agent_selection_policy``   | ``SessionRow.options`` JSONB                   |
      | ``kernel_groups``                              | ``SessionRow.options`` JSONB                   |
      | ``handler_options``                            | ``SessionRow.options`` JSONB                   |

    This class is NOT persisted as a whole — use ``SessionStoredOptions``
    for the JSONB surface.
    """

    priority: int = Field(description="Scheduling priority.")
    is_preemptible: bool = Field(description="Preemption flag.")
    cluster_mode: ClusterMode = Field(description="Placement constraint.")
    cluster_size: int = Field(
        ge=1,
        description="Total number of kernels in the session.",
    )
    scheduling_target: SchedulingTarget = Field(
        description="Resolved scheduling placement constraints.",
    )
    kernel_groups: list[KernelGroup] = Field(
        description="Resolved kernel-group layout (each group frozen).",
    )
    handler_options: SessionHandlerOptions = Field(
        description="Frozen handler-keyed scheduler policy (timeout + retry).",
    )
