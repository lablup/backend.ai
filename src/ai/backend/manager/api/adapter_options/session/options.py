"""Shared conversion helpers between the session-options DTO surface
and the data-layer session options domain objects.

Used by every adapter that reads or writes session options — the
per-resource-group default path (this file's primary use case) and any
future per-session surfaces that expose the resolved
:class:`SessionOptions`.

The DTO side is intentionally Optional-heavy (so partial replace
payloads remain expressible); the data side is fully resolved. The
``from_input`` helpers therefore perform two kinds of work:

1. Type shaping — list-of-entries → dict, DTO enum → domain enum,
   ``BinarySizeInput.expr`` → ``BinarySize``, etc.
2. Validation — duplicate / unknown ``by_handler`` keys, required
   ``KernelExecutionSpec`` fields that cannot be deferred to runtime
   defaults.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from ai.backend.common.dto.manager.v2.common import (
    ResourceSlotEntryInfo,
    ResourceSlotEntryInput,
)
from ai.backend.common.dto.manager.v2.session.request import MountItemInput
from ai.backend.common.dto.manager.v2.session.types import ClusterModeEnum
from ai.backend.common.dto.manager.v2.session_options import (
    AgentSelectionPolicyEnum,
    DefaultSessionOptionsInfo,
    DefaultSessionOptionsInput,
    FailurePolicyEnum,
    HandlerOptionsEntryInfo,
    HandlerOptionsInfo,
    KernelExecutionSpecInfo,
    KernelExecutionSpecInput,
    ResourceOptsInfo,
    ResourceOptsInput,
    SessionHandlerOptionsInfo,
    SessionHandlerOptionsInput,
)
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.common.types import (
    BinarySize,
    ClusterMode,
    MountInfoEntry,
    MountPermission,
    ResourceSlot,
    ResourceSlotEntry,
)
from ai.backend.manager.data.session.options import (
    AgentSelectionPolicy,
    DefaultSessionOptions,
    FailurePolicy,
    HandlerOptions,
    KernelExecutionSpec,
    ResourceOpts,
    SessionHandlerOptions,
)

__all__ = (
    "default_session_options_from_input",
    "default_session_options_to_info",
)


# ---------------------------------------------------------------------------
# Enum mapping (DTO enum <-> data enum). Values are identical strings so the
# mapping is purely type discipline.
# ---------------------------------------------------------------------------


def _failure_policy_from_input(value: FailurePolicyEnum) -> FailurePolicy:
    return FailurePolicy(value.value)


def _failure_policy_to_info(value: FailurePolicy) -> FailurePolicyEnum:
    return FailurePolicyEnum(value.value)


def _agent_selection_policy_from_input(value: AgentSelectionPolicyEnum) -> AgentSelectionPolicy:
    return AgentSelectionPolicy(value.value)


def _agent_selection_policy_to_info(value: AgentSelectionPolicy) -> AgentSelectionPolicyEnum:
    return AgentSelectionPolicyEnum(value.value)


def _cluster_mode_from_input(value: ClusterModeEnum) -> ClusterMode:
    return ClusterMode(value.value)


def _cluster_mode_to_info(value: ClusterMode) -> ClusterModeEnum:
    return ClusterModeEnum(value.value)


# ---------------------------------------------------------------------------
# Handler options (timeout + max_retry_count)
# ---------------------------------------------------------------------------


def _handler_options_from_input(
    options: SessionHandlerOptionsInput,
    valid_handler_names: frozenset[str],
) -> SessionHandlerOptions:
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
    return SessionHandlerOptions(
        default=HandlerOptions(
            timeout=options.default.timeout_sec,
            max_retry_count=options.default.max_retry_count,
        ),
        by_handler=by_handler,
    )


def _handler_options_to_info(options: SessionHandlerOptions) -> SessionHandlerOptionsInfo:
    entries = [
        HandlerOptionsEntryInfo(
            handler_name=name,
            timeout_sec=opts.timeout,
            max_retry_count=opts.max_retry_count,
        )
        for name, opts in options.by_handler.items()
    ]
    # Keep the output order deterministic so clients see a stable view.
    entries.sort(key=lambda e: e.handler_name)
    return SessionHandlerOptionsInfo(
        default=HandlerOptionsInfo(
            timeout_sec=options.default.timeout,
            max_retry_count=options.default.max_retry_count,
        ),
        by_handler=entries,
    )


# ---------------------------------------------------------------------------
# KernelExecutionSpec (ResourceSlot, Mounts, ResourceOpts)
# ---------------------------------------------------------------------------


def _resource_slot_from_entries(entries: Sequence[ResourceSlotEntryInput]) -> ResourceSlot:
    return ResourceSlot({e.resource_type: Decimal(e.quantity) for e in entries})


def _resource_slot_to_entries(slot: ResourceSlot) -> list[ResourceSlotEntryInfo]:
    entries = [
        ResourceSlotEntryInfo(resource_type=rtype, quantity=Decimal(quantity))
        for rtype, quantity in slot.items()
    ]
    entries.sort(key=lambda e: e.resource_type)
    return entries


def _resource_entry_list_from_input(
    entries: Sequence[ResourceSlotEntryInput],
) -> list[ResourceSlotEntry]:
    """Project DTO resource-slot input entries into the data-layer
    :class:`ResourceSlotEntry` list used by ``KernelExecutionSpec``.
    """
    return [ResourceSlotEntry(resource_type=e.resource_type, quantity=e.quantity) for e in entries]


def _resource_opts_from_input(value: ResourceOptsInput | None) -> ResourceOpts:
    if value is None or value.shmem is None:
        return ResourceOpts()
    return ResourceOpts(shmem=BinarySize.finite_from_str(value.shmem.expr))


def _resource_opts_to_info(value: ResourceOpts) -> ResourceOptsInfo:
    return ResourceOptsInfo(shmem=str(value.shmem) if value.shmem is not None else None)


def _mount_items_to_entries(items: Sequence[MountItemInput]) -> list[MountInfoEntry]:
    result: list[MountInfoEntry] = []
    for item in items:
        perm: MountPermission | None = None
        if item.permission is not None:
            perm = MountPermission(item.permission)
        result.append(
            MountInfoEntry(
                vfolder_id=VFolderUUID(item.vfolder_id),
                mount_destination=item.mount_path,
                mount_perm=perm or MountPermission.READ_WRITE,
                subpath=item.subpath,
            )
        )
    return result


def _kernel_execution_spec_from_input(
    input: KernelExecutionSpecInput,
) -> KernelExecutionSpec:
    """Project :class:`KernelExecutionSpecInput` into the fully-resolved
    :class:`KernelExecutionSpec`.

    Raises :class:`InvalidAPIParameters` when required fields
    (``image_id``, ``resources``) are not present in the input payload.
    The resource-group default lookup happens in the caller
    (``default_session_options_from_input``) — this function does not
    consult outside sources.
    """
    if input.image_id is None:
        raise InvalidAPIParameters("default_kernel_execution_spec.image_id is required when set")
    if input.resources is None:
        raise InvalidAPIParameters("default_kernel_execution_spec.resources is required when set")
    return KernelExecutionSpec(
        image_id=ImageID(input.image_id),
        resources=_resource_entry_list_from_input(input.resources),
        resource_opts=_resource_opts_from_input(input.resource_opts),
        environ=dict(input.environ or {}),
        mounts=_mount_items_to_entries(input.mounts or ()),
        startup_command=input.startup_command,
        bootstrap_script=input.bootstrap_script,
        starts_at=input.starts_at,
        batch_timeout_sec=input.batch_timeout_sec,
    )


def _kernel_execution_spec_to_info(
    spec: KernelExecutionSpec,
) -> KernelExecutionSpecInfo:
    return KernelExecutionSpecInfo(
        image_id=spec.image_id,
        resources=[
            ResourceSlotEntryInfo(
                resource_type=entry.resource_type,
                quantity=Decimal(entry.quantity),
            )
            for entry in spec.resources
        ],
        resource_opts=_resource_opts_to_info(spec.resource_opts),
        environ=dict(spec.environ),
        startup_command=spec.startup_command,
        bootstrap_script=spec.bootstrap_script,
        starts_at=spec.starts_at,
        batch_timeout_sec=spec.batch_timeout_sec,
    )


# ---------------------------------------------------------------------------
# Public: DefaultSessionOptions converters
# ---------------------------------------------------------------------------


def default_session_options_from_input(
    options: DefaultSessionOptionsInput,
    *,
    valid_handler_names: frozenset[str],
) -> DefaultSessionOptions:
    """Validate and project an admin-replace payload into the domain
    :class:`DefaultSessionOptions`.

    ``valid_handler_names`` is the runtime set of handler ``name()``
    results registered on the session scheduler coordinator; any
    ``handler_options.by_handler`` key outside this set is rejected as
    :class:`InvalidAPIParameters`.

    Every field on the input is optional — missing fields fall back to
    the Python ``DefaultSessionOptions`` field defaults. The admin
    surface therefore accepts partial payloads (e.g. only
    ``handler_options``) while still yielding a complete stored object.
    """
    baseline = DefaultSessionOptions()
    resolved_kernel_execution_spec: KernelExecutionSpec | None
    if options.default_kernel_execution_spec is not None:
        resolved_kernel_execution_spec = _kernel_execution_spec_from_input(
            options.default_kernel_execution_spec
        )
    else:
        resolved_kernel_execution_spec = baseline.default_kernel_execution_spec

    resolved_handler_options: SessionHandlerOptions
    if options.handler_options is not None:
        resolved_handler_options = _handler_options_from_input(
            options.handler_options, valid_handler_names
        )
    else:
        resolved_handler_options = baseline.handler_options

    return DefaultSessionOptions(
        priority=options.priority if options.priority is not None else baseline.priority,
        is_preemptible=(
            options.is_preemptible
            if options.is_preemptible is not None
            else baseline.is_preemptible
        ),
        cluster_mode=(
            _cluster_mode_from_input(options.cluster_mode)
            if options.cluster_mode is not None
            else baseline.cluster_mode
        ),
        default_failure_policy=(
            _failure_policy_from_input(options.default_failure_policy)
            if options.default_failure_policy is not None
            else baseline.default_failure_policy
        ),
        default_kernel_execution_spec=resolved_kernel_execution_spec,
        handler_options=resolved_handler_options,
        agent_selection_policy=(
            _agent_selection_policy_from_input(options.agent_selection_policy)
            if options.agent_selection_policy is not None
            else baseline.agent_selection_policy
        ),
    )


def default_session_options_to_info(options: DefaultSessionOptions) -> DefaultSessionOptionsInfo:
    """Project the domain model to the admin-visible response DTO."""
    return DefaultSessionOptionsInfo(
        priority=options.priority,
        is_preemptible=options.is_preemptible,
        cluster_mode=_cluster_mode_to_info(options.cluster_mode),
        default_failure_policy=_failure_policy_to_info(options.default_failure_policy),
        default_kernel_execution_spec=(
            _kernel_execution_spec_to_info(options.default_kernel_execution_spec)
            if options.default_kernel_execution_spec is not None
            else None
        ),
        handler_options=_handler_options_to_info(options.handler_options),
        agent_selection_policy=_agent_selection_policy_to_info(options.agent_selection_policy),
    )
