"""GraphQL types for session options.

Mirrors the shared :mod:`ai.backend.common.dto.manager.v2.session_options`
DTOs so both input (Replace mutations) and output (ResourceGroup /
Session nodes) surfaces can travel through GraphQL with
Strawberry-compatible types.

Type names are prefixed with ``DefaultSession`` where they describe the
resource-group default layer and ``Session*`` for the per-session
stored view — so the deployment-side analogues
(``DeploymentHandlerOptions*``, ...) can keep their existing names
without conflict.
"""

from __future__ import annotations

from datetime import datetime

from ai.backend.common.dto.manager.v2.session_options import (
    AgentSelectionPolicyEnum,
    DefaultSessionOptionsInfo,
    DefaultSessionOptionsInput,
    FailurePolicyEnum,
    HandlerOptionsEntryInfo,
    HandlerOptionsEntryInput,
    HandlerOptionsInfo,
    HandlerOptionsInput,
    KernelExecutionSpecInfo,
    KernelExecutionSpecInput,
    KernelGroupInfo,
    KernelGroupInput,
    ResourceOptsInfo,
    ResourceOptsInput,
    SessionHandlerOptionsInfo,
    SessionHandlerOptionsInput,
)
from ai.backend.common.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.common_types import (
    BinarySizeInputGQL,
    ResourceSlotEntryGQL,
    ResourceSlotEntryInputGQL,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_enum,
    gql_pydantic_input,
    gql_pydantic_type,
)

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


FailurePolicyGQL = gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=("Policy for how a kernel group's startup failures affect the owning session."),
    ),
    FailurePolicyEnum,
    name="SessionFailurePolicy",
)


AgentSelectionPolicyGQL = gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Scheduling constraint applied to designated agents for a session.",
    ),
    AgentSelectionPolicyEnum,
    name="SessionAgentSelectionPolicy",
)


# ---------------------------------------------------------------------------
# Handler options (timeout + max_retry_count). Distinct from the
# deployment-side entry so both sides can coexist in one schema.
# ---------------------------------------------------------------------------


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Per-handler scheduler policy fields for session handler options.",
    ),
    name="DefaultSessionHandlerOptionsInput",
)
class DefaultSessionHandlerOptionsInputGQL(PydanticInputMixin[HandlerOptionsInput]):
    timeout_sec: int | None = None
    max_retry_count: int | None = None


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Per-handler scheduler policy snapshot for session handler options.",
    ),
    model=HandlerOptionsInfo,
    name="DefaultSessionHandlerOptionsInfo",
)
class DefaultSessionHandlerOptionsInfoGQL:
    timeout_sec: int | None
    max_retry_count: int | None


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="A single (handler_name, options) entry for session handler options.",
    ),
    name="DefaultSessionHandlerOptionsEntryInput",
)
class DefaultSessionHandlerOptionsEntryInputGQL(PydanticInputMixin[HandlerOptionsEntryInput]):
    handler_name: str
    timeout_sec: int | None = None
    max_retry_count: int | None = None


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="A single (handler_name, options) entry response for session handler options.",
    ),
    model=HandlerOptionsEntryInfo,
    name="DefaultSessionHandlerOptionsEntryInfo",
)
class DefaultSessionHandlerOptionsEntryInfoGQL:
    handler_name: str
    timeout_sec: int | None
    max_retry_count: int | None


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Session handler-options input (timeout + retry, handler-keyed).",
    ),
    name="DefaultSessionHandlerOptionsPolicyInput",
)
class DefaultSessionHandlerOptionsPolicyInputGQL(PydanticInputMixin[SessionHandlerOptionsInput]):
    default: DefaultSessionHandlerOptionsInputGQL | None = None
    by_handler: list[DefaultSessionHandlerOptionsEntryInputGQL] | None = None


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Session handler-options policy response.",
    ),
    model=SessionHandlerOptionsInfo,
    name="DefaultSessionHandlerOptionsPolicyInfo",
)
class DefaultSessionHandlerOptionsPolicyInfoGQL:
    default: DefaultSessionHandlerOptionsInfoGQL
    by_handler: list[DefaultSessionHandlerOptionsEntryInfoGQL]


# ---------------------------------------------------------------------------
# Resource opts (per-kernel qualitative hints — shmem, etc.)
# ---------------------------------------------------------------------------


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Qualitative resource hints for session-level defaults (shared memory, ...).",
    ),
    name="DefaultSessionResourceOptsInput",
)
class DefaultSessionResourceOptsInputGQL(PydanticInputMixin[ResourceOptsInput]):
    shmem: BinarySizeInputGQL | None = None


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Qualitative resource hints response.",
    ),
    model=ResourceOptsInfo,
    name="DefaultSessionResourceOptsInfo",
)
class DefaultSessionResourceOptsInfoGQL:
    shmem: str | None


# ---------------------------------------------------------------------------
# KernelExecutionSpec (per-kernel execution spec)
# ---------------------------------------------------------------------------


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Baseline kernel execution spec input used as the resource-group default.",
    ),
    name="DefaultSessionKernelExecutionSpecInput",
)
class DefaultSessionKernelExecutionSpecInputGQL(PydanticInputMixin[KernelExecutionSpecInput]):
    image_id: str | None = None
    resources: list[ResourceSlotEntryInputGQL] | None = None
    resource_opts: DefaultSessionResourceOptsInputGQL | None = None
    # ``environ`` and ``mounts`` are intentionally omitted from the GQL
    # surface for now. GraphQL has no native map scalar, and the
    # per-kernel mount override schema is being reworked in #33 — both
    # will get dedicated list-of-entries wrappers in a follow-up.
    # REST v2 still exposes them via the underlying Pydantic DTO.
    startup_command: str | None = None
    bootstrap_script: str | None = None
    starts_at: datetime | None = None
    batch_timeout_sec: int | None = None


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Baseline kernel execution spec response.",
    ),
    model=KernelExecutionSpecInfo,
    name="DefaultSessionKernelExecutionSpecInfo",
)
class DefaultSessionKernelExecutionSpecInfoGQL:
    image_id: str | None
    resources: list[ResourceSlotEntryGQL] | None
    resource_opts: DefaultSessionResourceOptsInfoGQL | None
    # ``environ`` / ``mounts`` are not surfaced on the GQL output
    # for the same reason they are skipped on the input side — see
    # ``DefaultSessionKernelExecutionSpecInputGQL``. REST v2 retains them.
    startup_command: str | None
    bootstrap_script: str | None
    starts_at: datetime | None
    batch_timeout_sec: int | None


# ---------------------------------------------------------------------------
# KernelGroup (role + replicas + spec). Included for completeness so the
# per-session ``SessionStoredOptionsInfo`` projection (Phase 2) can
# reuse this wrapper.
# ---------------------------------------------------------------------------


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="A role + replica bundle carrying one kernel spec.",
    ),
    name="DefaultSessionKernelGroupInput",
)
class DefaultSessionKernelGroupInputGQL(PydanticInputMixin[KernelGroupInput]):
    role: str
    replica_count: int
    execution_spec: DefaultSessionKernelExecutionSpecInputGQL | None = None
    failure_policy: FailurePolicyGQL | None = None
    depends_on_roles: list[str] | None = None


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="A role + replica bundle response.",
    ),
    model=KernelGroupInfo,
    name="DefaultSessionKernelGroupInfo",
)
class DefaultSessionKernelGroupInfoGQL:
    role: str
    replica_count: int
    execution_spec: DefaultSessionKernelExecutionSpecInfoGQL
    failure_policy: FailurePolicyGQL
    depends_on_roles: list[str]


# ---------------------------------------------------------------------------
# DefaultSessionOptions — what the resource group's
# ``default_session_options`` JSONB column stores.
# ---------------------------------------------------------------------------


@gql_pydantic_input(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Resource-group default session options input payload.",
    ),
    name="DefaultSessionOptionsInput",
)
class DefaultSessionOptionsInputGQL(PydanticInputMixin[DefaultSessionOptionsInput]):
    priority: int | None = None
    is_preemptible: bool | None = None
    # ``cluster_mode`` accepts the shared ClusterModeEnum string value so
    # the admin UI can send "single-node" / "multi-node".
    cluster_mode: str | None = None
    default_failure_policy: FailurePolicyGQL | None = None
    default_kernel_execution_spec: DefaultSessionKernelExecutionSpecInputGQL | None = None
    handler_options: DefaultSessionHandlerOptionsPolicyInputGQL | None = None
    agent_selection_policy: AgentSelectionPolicyGQL | None = None


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Resource-group default session options response.",
    ),
    model=DefaultSessionOptionsInfo,
    name="DefaultSessionOptionsInfo",
)
class DefaultSessionOptionsInfoGQL:
    priority: int
    is_preemptible: bool
    cluster_mode: str
    default_failure_policy: FailurePolicyGQL
    default_kernel_execution_spec: DefaultSessionKernelExecutionSpecInfoGQL | None
    handler_options: DefaultSessionHandlerOptionsPolicyInfoGQL
    agent_selection_policy: AgentSelectionPolicyGQL
