"""Scheduling controller for managing session lifecycle and scheduling operations."""

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID, uuid4

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.contexts.user import current_user
from ai.backend.common.defs import RESERVED_VFOLDER_PATTERNS, RESERVED_VFOLDERS
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.session.broadcast import SchedulingBroadcastEvent
from ai.backend.common.events.types import AbstractBroadcastEvent
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.plugin.hook import ALL_COMPLETED, PASSED, HookPluginContext
from ai.backend.common.types import KernelId, ResourceSlot, ResourceSlotEntry, SessionId
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.session.compute_schedule import (
    ComputeScheduleKernelResult,
    ComputeScheduleResult,
    UnschedulableReasonHint,
)
from ai.backend.manager.data.session.draft import SessionSpecDraft
from ai.backend.manager.data.session.spec import SessionSpec
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.errors.common import InternalServerError, RejectedByHook
from ai.backend.manager.metrics.scheduler import (
    SchedulerOperationMetricObserver,
    SchedulerPhaseMetricObserver,
)
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.repositories.scheduler import (
    MarkTerminatingResult,
    SchedulerRepository,
)
from ai.backend.manager.repositories.scheduler.types.session_creation import SessionSpecContextFetch
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.exceptions import (
    BatchAgentSelectionFailedError,
    NoAgentsInResourceGroupError,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
    AgentSelectionConfig,
    AgentSelectionCriteria,
    AgentSelector,
    KernelResourceSpec,
    SessionMetadata,
)
from ai.backend.manager.sokovan.scheduler.types import ScheduleType
from ai.backend.manager.sokovan.scheduling_controller.types import SessionValidationSpec

from .preparers import (
    AssignContainerUserMappingRule,
    AssignNetworkConfigRule,
    AssignUserIdentityRule,
    BuildInternalDataRule,
    ComputeKernelResourcesRule,
    ExpandKernelGroupsRule,
    InjectSessionEnvironRule,
    MergeResourceGroupDefaultsRule,
    ResolveVFolderMountsRule,
    SessionSpecPreparationContext,
    SessionSpecPreparer,
)
from .validators import (
    ConcurrentSessionLimitRule,
    ContainerLimitRule,
    DotfileVFolderConflictRule,
    ImageSlotTypeRule,
    InferenceModelFolderRule,
    MountNameValidationRule,
    RequestedSlotTypeRule,
    RequiredResourceSlotRule,
    ResourceLimitRule,
    ServicePortRule,
    SessionSpecValidationContext,
    SessionSpecValidator,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class SchedulingControllerArgs:
    """Arguments for initializing SchedulingController."""

    repository: SchedulerRepository
    config_provider: ManagerConfigProvider
    storage_manager: StorageSessionManager
    event_producer: EventProducer
    valkey_schedule: ValkeyScheduleClient
    network_plugin_ctx: NetworkPluginContext
    hook_plugin_ctx: HookPluginContext
    agent_selector: AgentSelector


@dataclass
class _Image:
    id: ImageID
    architecture: str


@dataclass
class _KernelComputeScheduleResourceSpec:
    spec: KernelResourceSpec
    image: _Image


@dataclass
class _KernelComputeScheduleData:
    """Mutable, in-progress version of a single kernel's
    :class:`ComputeScheduleKernelResult`, accumulated across
    :meth:`SchedulingController.compute_schedule` and finalized at the end.

    Held in a dict keyed by the kernel's unique cluster role (which the draft
    builder assigns in request order, so the dict preserves that order):

    - ``resolved`` becomes True once the kernel's image resolves; it stays
      False for image-unresolved kernels, which are excluded from selection.
    - ``reason_hint`` is set only for a kernel the selector could not place.
    - a kernel is schedulable iff it ``resolved`` and the selector placed it
      (``reason_hint is None``).
    """

    resource_spec: _KernelComputeScheduleResourceSpec | None

    requested_slots: tuple[ResourceSlotEntry, ...]
    reason_hint: UnschedulableReasonHint | None
    success: bool = True


class SchedulingController:
    """Controller for session lifecycle and scheduling operations management."""

    _repository: SchedulerRepository
    _config_provider: ManagerConfigProvider
    _storage_manager: StorageSessionManager
    _event_producer: EventProducer
    _valkey_schedule: ValkeyScheduleClient
    _network_plugin_ctx: NetworkPluginContext

    # Services
    _spec_preparer: SessionSpecPreparer
    _spec_validator: SessionSpecValidator
    _agent_selector: AgentSelector
    _metric_observer: SchedulerPhaseMetricObserver
    _operation_metrics: SchedulerOperationMetricObserver
    _hook_plugin_ctx: HookPluginContext

    def __init__(self, args: SchedulingControllerArgs) -> None:
        """Initialize the scheduling controller with required services."""
        self._repository = args.repository
        self._config_provider = args.config_provider
        self._storage_manager = args.storage_manager
        self._event_producer = args.event_producer
        self._valkey_schedule = args.valkey_schedule
        self._network_plugin_ctx = args.network_plugin_ctx
        self._hook_plugin_ctx = args.hook_plugin_ctx

        # Initialize metric observers (singletons)
        self._metric_observer = SchedulerPhaseMetricObserver.instance()
        self._operation_metrics = SchedulerOperationMetricObserver.instance()

        # Draft-based spec preparer chain: builds a fully-resolved
        # ``SessionSpec`` from a caller-supplied ``SessionSpecDraft``.
        # Order matters — RG defaults merge first so later rules see the
        # merged baseline; expand last on the options side so kernel
        # specs exist before per-kernel rules run.
        self._spec_preparer = SessionSpecPreparer([
            AssignUserIdentityRule(),
            MergeResourceGroupDefaultsRule(),
            ComputeKernelResourcesRule(),
            ExpandKernelGroupsRule(),
            AssignNetworkConfigRule(),
            AssignContainerUserMappingRule(),
            InjectSessionEnvironRule(),
            BuildInternalDataRule(),
            ResolveVFolderMountsRule(),
        ])

        # Draft-based spec validator chain. Runs against the finalized
        # ``SessionSpec`` + ``SessionSpecValidationContext``.
        self._spec_validator = SessionSpecValidator([
            ConcurrentSessionLimitRule(),
            ContainerLimitRule(),
            ImageSlotTypeRule(),
            RequestedSlotTypeRule(),
            RequiredResourceSlotRule(),
            ResourceLimitRule(),
            ServicePortRule(),
            MountNameValidationRule(),
            InferenceModelFolderRule(),
            DotfileVFolderConflictRule(),
        ])
        self._agent_selector = args.agent_selector

    async def _verify_resource_group_accessible(self, draft: SessionSpecDraft) -> None:
        """Reject the draft when its target resource group is outside the
        requester's single-project allowlist.

        The scope decision and rejection live in the caller; the repository only
        performs DB reads.
        """
        resource_group_id = draft.scope.resource_group_id
        if resource_group_id is None:
            return
        domain_name = str(draft.scope.domain_name) if draft.scope.domain_name else None
        project_id = draft.scope.project_id
        access_key = draft.identity.access_key
        if access_key is None or domain_name is None or project_id is None:
            raise InternalServerError(
                "Unreachable: resource_group_id supplied without identity context",
            )
        accessible_rg_ids = await self._repository.query_accessible_resource_group_ids(
            domain_name=domain_name,
            project_id=project_id,
            access_key=access_key,
        )
        if resource_group_id not in accessible_rg_ids:
            rg_label = draft.scope.resource_group_name or resource_group_id
            raise InvalidAPIParameters(f"Resource group '{rg_label}' is not accessible")

    async def enqueue_session_from_draft(
        self,
        draft: SessionSpecDraft,
    ) -> SessionId:
        """Draft-based session enqueue entry point.

        Only input is the :class:`SessionSpecDraft` — request-envelope
        extras (sudo, model-definition overlay) ride on
        ``draft.internal_data_extras``. Validation-adjacent DB reads (image
        metadata, keypair policy, resource-group network, container uid/gid,
        dotfiles, active session count) flow through
        :meth:`SchedulerRepository.fetch_session_spec_contexts`; vfolder mounts
        are resolved separately via
        :meth:`SchedulerRepository.resolve_vfolder_mounts_by_role`.

        Flow:

        1. Context fetch + vfolder-mount resolution + preparer chain →
           finalized ``SessionSpec`` + validation context.
        2. ``PRE_ENQUEUE_SESSION`` hook — rejected calls raise.
        3. Validator chain — spec + context.
        4. ``SchedulerRepository.enqueue_session_from_spec`` — writer tx.
        5. Broadcast PENDING + ask the coordinator to schedule.
        6. ``POST_ENQUEUE_SESSION`` hook notification.
        """
        rg_id = draft.scope.resource_group_id

        await self._verify_resource_group_accessible(draft)

        allowed_vfolder_types = list(
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )

        with self._metric_observer.measure_phase(
            "scheduling_controller", rg_id, "spec_fetch_contexts"
        ):
            fetched = await self._repository.fetch_session_spec_contexts(draft)

        # Vfolder mounts are resolved separately (storage-manager RPC / etcd),
        # kept out of the context fetch so resource-only callers can skip them.
        with self._metric_observer.measure_phase(
            "scheduling_controller", rg_id, "vfolder_mount_resolution"
        ):
            vfolder_mounts_by_role = await self._repository.resolve_vfolder_mounts_by_role(
                draft,
                storage_manager=self._storage_manager,
                allowed_vfolder_types=allowed_vfolder_types,
            )

        prep_ctx = SessionSpecPreparationContext(
            resource_group_defaults=fetched.resource_group_defaults,
            resource_group_network=fetched.resource_group_network,
            container_user_info=fetched.container_user_info,
            image_infos=fetched.image_infos,
            resource_group_allow_fractional=fetched.resource_group_allow_fractional,
            dotfile_data=fetched.dotfile_data,
            vfolder_mounts_by_role=vfolder_mounts_by_role,
        )
        val_ctx = SessionSpecValidationContext(
            keypair_resource_policy=fetched.keypair_resource_policy,
            image_infos=fetched.image_infos,
            known_slot_types=fetched.known_slot_types,
            slot_type_policy=fetched.slot_type_policy,
            dotfile_data=fetched.dotfile_data,
            active_session_count=fetched.active_session_count,
        )

        with self._metric_observer.measure_phase(
            "scheduling_controller", rg_id, "spec_preparation"
        ):
            spec = await self._spec_preparer.prepare(draft, prep_ctx)

        hook_result = await self._hook_plugin_ctx.dispatch(
            "PRE_ENQUEUE_SESSION",
            (
                spec.identity.session_id,
                spec.identity.session_name,
                spec.identity.access_key,
            ),
            return_when=ALL_COMPLETED,
        )
        if hook_result.status != PASSED:
            raise RejectedByHook.from_hook_result(hook_result)

        with self._metric_observer.measure_phase("scheduling_controller", rg_id, "spec_validation"):
            self._spec_validator.validate(spec, val_ctx)

        with self._metric_observer.measure_phase("scheduling_controller", rg_id, "enqueue"):
            session_id = await self._repository.enqueue_session_from_spec(spec)

        log.info(
            "Session {} ({}) enqueued successfully via draft path",
            spec.identity.session_name,
            session_id,
        )

        await self._event_producer.broadcast_events_batch([
            SchedulingBroadcastEvent(
                session_id=session_id,
                creation_id=spec.identity.creation_id,
                status_transition=str(SessionStatus.PENDING),
                reason="Session enqueued",
            )
        ])

        try:
            await self.mark_scheduling_needed([ScheduleType.SCHEDULE])
        except Exception as e:
            log.warning(
                "Failed to request scheduling for session {}: {}",
                session_id,
                e,
            )
        await self._hook_plugin_ctx.notify(
            "POST_ENQUEUE_SESSION",
            (session_id, spec.identity.session_name, spec.identity.access_key),
        )
        return session_id

    def _prepare_kernel_data(
        self, spec: SessionSpec, fetched: SessionSpecContextFetch
    ) -> dict[KernelId, _KernelComputeScheduleData]:
        prepared_data: dict[KernelId, _KernelComputeScheduleData] = {}
        for kernel_spec in spec.kernel_specs:
            kernel_id = KernelId(uuid4())
            resource_input = kernel_spec.execution_spec.resource_input
            image_info = (
                fetched.image_infos.get(resource_input.image_id)
                if resource_input.image_id is not None
                else None
            )
            if image_info is None:
                prepared_data[kernel_id] = _KernelComputeScheduleData(
                    resource_spec=None,
                    requested_slots=tuple(resource_input.resources),
                    reason_hint=UnschedulableReasonHint(image_not_found=True),
                    success=False,
                )
                continue
            prepared_data[kernel_id] = _KernelComputeScheduleData(
                resource_spec=_KernelComputeScheduleResourceSpec(
                    image=_Image(
                        id=resource_input.image_id,
                        architecture=image_info.architecture,
                    ),
                    spec=KernelResourceSpec(
                        requested_slots=ResourceSlotEntry.inputs_to_resource_slot(
                            resource_input.resources
                        ),
                        required_architecture=image_info.architecture,
                    ),
                ),
                requested_slots=tuple(resource_input.resources),
                reason_hint=None,
            )
        return prepared_data

    async def _compute_schedule(
        self,
        spec: SessionSpec,
        kernel_data: dict[KernelId, _KernelComputeScheduleData],
    ) -> ComputeScheduleResult:
        kernel_requirements: dict[UUID, KernelResourceSpec] = {
            kernel_id: data.resource_spec.spec
            for kernel_id, data in kernel_data.items()
            if data.resource_spec is not None
        }
        resource_group_reason: str | None = None

        if kernel_requirements:
            criteria = AgentSelectionCriteria(
                session_metadata=SessionMetadata(
                    session_id=SessionId(UUID(str(spec.identity.session_id))),
                    session_type=spec.classification.session_type,
                    scaling_group=str(spec.scope.resource_group_name),
                    cluster_mode=spec.options.cluster_mode,
                ),
                kernel_requirements=kernel_requirements,
            )
            # Container-limit remediation is intentionally out of scope, so the
            # per-agent container limit is not enforced for the fitting check.
            config = AgentSelectionConfig(
                max_container_count=None,
                enforce_spreading_endpoint_replica=False,
            )
            # The selector mutates the agents list on full success; feed clones so
            # the live snapshot is never altered.
            scheduling_data = await self._repository.get_scheduling_data(
                spec.scope.resource_group_id
            )
            if scheduling_data is None:
                resource_group_reason = "Resource group does not exist"
                for result in kernel_data.values():
                    result.success = False
                return ComputeScheduleResult([], resource_group_reason=resource_group_reason)
            agent_occupancy = (
                scheduling_data.snapshot_data.resource_occupancy.by_agent
                if scheduling_data.snapshot_data
                else {}
            )
            mutable_agents = [
                agent.to_agent_info(agent_occupancy) for agent in scheduling_data.agents
            ]
            try:
                await self._agent_selector.select_agents_for_batch_requirements(
                    mutable_agents, criteria, config, None
                )
            except NoAgentsInResourceGroupError:
                resource_group_reason = "No schedulable agents exist in the resource group"
                for result in kernel_data.values():
                    result.success = False
            except BatchAgentSelectionFailedError as e:
                for err in e.errors:
                    hint = err.build_remediation_hint()
                    reason = UnschedulableReasonHint(
                        required_reduction=(
                            tuple(ResourceSlotEntry.from_resource_slot(hint.required_reduction))
                            if hint.required_reduction is not None
                            else None
                        ),
                        available_archs=hint.available_archs,
                    )
                    for kernel_id in err.resource_requirement.kernel_ids:
                        failed_draft = kernel_data.get(kernel_id)
                        if failed_draft is not None:
                            failed_draft.success = False
                            failed_draft.reason_hint = reason

        kernel_result = [
            ComputeScheduleKernelResult(
                requested_slots=kernel_data.requested_slots,
                requested_architecture=kernel_data.resource_spec.image.architecture
                if kernel_data.resource_spec is not None
                else None,
                success=kernel_data.success,
                reason_hint=kernel_data.reason_hint,
            )
            for kernel_data in kernel_data.values()
        ]
        return ComputeScheduleResult(
            kernel_results=kernel_result, resource_group_reason=resource_group_reason
        )

    async def compute_schedule(
        self,
        draft: SessionSpecDraft,
    ) -> ComputeScheduleResult:
        """Compute whether each kernel of a would-be session could be placed on
        the target resource group, without provisioning or mutating any state.

        Reuses the same spec-context fetch and preparer chain as the enqueue
        path — only vfolder-mount resolution is neutralized (it needs a storage
        RPC and is irrelevant to node fitting) by feeding an empty per-role
        mount map. The finalized spec's per-kernel resource slots + architecture
        then drive the real agent selector against a live snapshot of the
        group's agents. Kernels the selector cannot place are returned with a
        remediation hint; every other kernel is schedulable.

        Results correspond positionally to ``draft.options.kernel_groups`` (each
        group is one requested kernel with a unique ``role``), so callers match
        results to their request by list index.
        """
        rg_id = draft.scope.resource_group_id
        if rg_id is None:
            raise InvalidAPIParameters("resource_group_id is required for compute-schedule")
        fetched = await self._repository.fetch_session_spec_contexts(draft)
        prep_ctx = SessionSpecPreparationContext(
            resource_group_defaults=fetched.resource_group_defaults,
            resource_group_network=fetched.resource_group_network,
            container_user_info=fetched.container_user_info,
            image_infos=fetched.image_infos,
            resource_group_allow_fractional=fetched.resource_group_allow_fractional,
            dotfile_data=fetched.dotfile_data,
            # Node fitting does not depend on vfolder mounts; skip the
            # storage-RPC resolution by leaving the per-role mount map empty.
            vfolder_mounts_by_role={},
        )
        spec = await self._spec_preparer.prepare(draft, prep_ctx)
        compute_schedule_kernel_data = self._prepare_kernel_data(spec, fetched)
        return await self._compute_schedule(spec, compute_schedule_kernel_data)

    async def mark_scheduling_needed(self, schedule_types: Sequence[ScheduleType]) -> None:
        """
        Request scheduling operations for the next cycle.

        This is the public interface for requesting scheduling operations.
        The actual scheduling will be handled internally by the coordinator.

        Args:
            schedule_types: Types of scheduling to request
        """
        if not schedule_types:
            return
        await self._valkey_schedule.mark_schedules_needed_batch([st.value for st in schedule_types])
        log.debug(
            "Requested scheduling for type(s): {}",
            ", ".join(st.value for st in schedule_types),
        )

    async def mark_sessions_for_termination(
        self,
        session_ids: list[SessionId],
        reason: str = "USER_REQUESTED",
        *,
        forced: bool = False,
    ) -> MarkTerminatingResult:
        """
        Mark multiple sessions and their kernels for termination by updating their status to TERMINATING.

        When forced=True, sessions skip TERMINATING and go directly to TERMINATED so the manager
        immediately considers the session done and frees resources.

        Args:
            session_ids: List of session IDs to terminate
            reason: Reason for termination
            forced: If True, skip TERMINATING and set directly to TERMINATED

        Returns:
            MarkTerminatingResult with categorized session statuses
        """
        result = await self._repository.mark_sessions_terminating(
            session_ids, reason, forced=forced
        )

        if result.has_processed():
            log.info(
                "Marked {} sessions for termination"
                " (cancelled: {}, terminating: {}, force_terminated: {})",
                result.processed_count(),
                len(result.cancelled_sessions),
                len(result.terminating_sessions),
                len(result.force_terminated_sessions),
            )

            # Broadcast status events for cancelled, terminating, and force-terminated sessions
            broadcast_events: list[AbstractBroadcastEvent] = [
                SchedulingBroadcastEvent(
                    session_id=session_id,
                    creation_id="",
                    status_transition=str(SessionStatus.CANCELLED),
                    reason=reason,
                )
                for session_id in result.cancelled_sessions
            ]
            broadcast_events.extend([
                SchedulingBroadcastEvent(
                    session_id=session_id,
                    creation_id="",
                    status_transition=str(SessionStatus.TERMINATING),
                    reason=reason,
                )
                for session_id in result.terminating_sessions
            ])
            broadcast_events.extend([
                SchedulingBroadcastEvent(
                    session_id=session_id,
                    creation_id="",
                    status_transition=str(SessionStatus.TERMINATED),
                    reason=reason,
                )
                for session_id in result.force_terminated_sessions
            ])
            if broadcast_events:
                await self._event_producer.broadcast_events_batch(broadcast_events)
            # Record metric for termination attempts
            self._operation_metrics.observe_success(
                operation="mark_sessions_terminating",
                count=result.processed_count(),
            )
            # Request termination scheduling for the next cycle
            schedule_types = [ScheduleType.TERMINATE]

            # For force-terminated sessions, store session IDs in Valkey for container cleanup
            if result.force_terminated_sessions:
                await self._valkey_schedule.add_force_terminated_sessions(
                    result.force_terminated_sessions
                )
                schedule_types.append(ScheduleType.CLEANUP_FORCE_TERMINATED)

            await self.mark_scheduling_needed(schedule_types)

        return result

    async def validate_session_spec(self, spec: SessionValidationSpec) -> None:
        # TODO: Refactor to use ValidationRule
        alias_destinations = [
            entry.mount_destination
            for entry in spec.mount_entries
            if entry.mount_destination is not None
        ]
        if len(alias_destinations) != len(set(alias_destinations)):
            raise InvalidAPIParameters("Duplicate alias folder name exists.")
        original_refs = {str(entry.vfolder_id) for entry in spec.mount_entries}
        for alias_name in alias_destinations:
            if alias_name.startswith("/home/work/"):
                alias_name = alias_name.replace("/home/work/", "")
            if alias_name == "":
                raise InvalidAPIParameters("Alias name cannot be empty.")
            if not _verify_vfolder_name(alias_name):
                raise InvalidAPIParameters(str(alias_name) + " is reserved for internal path.")
            if alias_name in original_refs:
                raise InvalidAPIParameters(
                    "Alias name cannot be set to an existing folder name: " + str(alias_name)
                )
        # Validate resource slots
        available_resource_slots = (
            await self._config_provider.legacy_etcd_config_loader.get_resource_slots()
        )
        try:
            ResourceSlot.from_user_input(
                spec.resource_spec.resource_slots, available_resource_slots
            )
        except ValueError as e:
            raise InvalidAPIParameters(f"Invalid resource allocation: {e}") from e
        # Validate Image
        user = current_user()
        if user is None:
            raise InvalidAPIParameters("User context is required for image validation.")
        await self._repository.check_available_image(spec.image_id, user.domain_name, user.user_id)


def _verify_vfolder_name(folder: str) -> bool:
    if folder in RESERVED_VFOLDERS:
        return False
    for pattern in RESERVED_VFOLDER_PATTERNS:
        if pattern.match(folder):
            return False
    return True
