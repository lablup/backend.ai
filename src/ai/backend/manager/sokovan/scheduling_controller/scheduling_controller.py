"""Scheduling controller for managing session lifecycle and scheduling operations."""

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.contexts.user import current_user
from ai.backend.common.defs import RESERVED_VFOLDER_PATTERNS, RESERVED_VFOLDERS
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.session.broadcast import SchedulingBroadcastEvent
from ai.backend.common.events.types import AbstractBroadcastEvent
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.identifier.architecture import ArchName
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.plugin.hook import ALL_COMPLETED, PASSED, HookPluginContext
from ai.backend.common.types import ResourceSlot, ResourceSlotEntry, SessionId, SlotName
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.session.compute_schedule import (
    ComputeScheduleKernelResult,
    ComputeScheduleResult,
    UnschedulableReasonHint,
)
from ai.backend.manager.data.session.draft import (
    SessionResourceSpecDraft,
    SessionScopeDraft,
    SessionSpecDraft,
)
from ai.backend.manager.data.session.spec import (
    SessionResourceSpec,
    SessionScope,
    SessionSpec,
)
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.errors.common import InternalServerError, RejectedByHook
from ai.backend.manager.errors.image import ImageNotFound
from ai.backend.manager.metrics.scheduler import (
    SchedulerOperationMetricObserver,
    SchedulerPhaseMetricObserver,
)
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.repositories.scheduler import SchedulerRepository
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.exceptions import (
    BatchAgentSelectionFailedError,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
    AgentSelectionCriteria,
    AgentSelector,
    PlacementPlan,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.tracker import (
    build_agent_trackers,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.types import (
    ResourceRequirements,
)
from ai.backend.manager.sokovan.scheduler.types import ScheduleType
from ai.backend.manager.sokovan.scheduling_controller.types import SessionValidationSpec
from ai.backend.manager.views.sokovan.scheduling import ComputeScheduleData
from ai.backend.manager.views.sokovan.session import MarkTerminatingResult
from ai.backend.manager.views.sokovan.session_creation import SessionSpecContext
from ai.backend.manager.views.sokovan.workload import (
    ResourceRequest,
)

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
    SessionSpecPreparer,
)
from .validators import (
    ContainerLimitRule,
    DotfileVFolderConflictRule,
    ImageSlotTypeRule,
    InferenceModelFolderRule,
    MountNameValidationRule,
    PendingSessionCountLimitRule,
    RequestedSlotTypeRule,
    RequiredResourceSlotRule,
    ResourceLimitRule,
    ServicePortRule,
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
        # ``SessionSpec`` + ``SessionSpecContext``.
        self._spec_validator = SessionSpecValidator([
            PendingSessionCountLimitRule(),
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
        access_key = draft.resource_spec.identity.access_key
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
        ``draft.resource_spec.internal_data_extras``.

        Flow:

        1. Shared context assembly (DB fetch + vfolder-mount resolution).
        2. Preparer chain → finalized ``SessionSpec``.
        3. ``PRE_ENQUEUE_SESSION`` hook — rejected calls raise.
        4. Validator chain — spec + context.
        5. ``SchedulerRepository.enqueue_session_from_spec`` — writer tx.
        6. Broadcast PENDING, request scheduling, ``POST_ENQUEUE_SESSION``.
        """
        rg_id = draft.scope.resource_group_id

        await self._verify_resource_group_accessible(draft)

        context = await self._build_session_spec_context(draft)
        spec = await self._finalize_session_spec(draft, context)

        await self._dispatch_pre_enqueue_hook(spec)

        with self._metric_observer.measure_phase("scheduling_controller", rg_id, "spec_validation"):
            self._spec_validator.validate(spec, context)

        with self._metric_observer.measure_phase("scheduling_controller", rg_id, "enqueue"):
            session_id = await self._repository.enqueue_session_from_spec(spec)

        await self._notify_session_enqueued(spec, session_id)
        return session_id

    async def _build_session_spec_context(self, draft: SessionSpecDraft) -> SessionSpecContext:
        """Fetch the complete shared context of one enqueue request.

        The repository assembles everything (DB reads plus the
        storage-manager vfolder-mount resolution), so the context only
        ever exists in a complete state.
        """
        rg_id = draft.scope.resource_group_id
        with self._metric_observer.measure_phase("scheduling_controller", rg_id, "spec_context"):
            return await self._repository.fetch_session_spec_context(draft, resolve_mounts=True)

    async def _finalize_session_spec(
        self, draft: SessionSpecDraft, context: SessionSpecContext
    ) -> SessionSpec:
        """Run the preparer chain and promote the draft into a ``SessionSpec``."""
        rg_id = draft.scope.resource_group_id
        with self._metric_observer.measure_phase(
            "scheduling_controller", rg_id, "spec_preparation"
        ):
            resource_spec = await self._spec_preparer.prepare(draft.resource_spec, context)
            scope = SessionScope.model_validate(draft.scope.model_dump(exclude_none=True))
            return SessionSpec(resource_spec=resource_spec, scope=scope)

    async def _dispatch_pre_enqueue_hook(self, spec: SessionSpec) -> None:
        """Run the ``PRE_ENQUEUE_SESSION`` hook gate; a rejection raises."""
        hook_result = await self._hook_plugin_ctx.dispatch(
            "PRE_ENQUEUE_SESSION",
            (
                spec.resource_spec.identity.session_id,
                spec.resource_spec.identity.session_name,
                spec.resource_spec.identity.access_key,
            ),
            return_when=ALL_COMPLETED,
        )
        if hook_result.status != PASSED:
            raise RejectedByHook.from_hook_result(hook_result)

    async def _notify_session_enqueued(self, spec: SessionSpec, session_id: SessionId) -> None:
        """Post-enqueue side effects: broadcast, scheduling request, POST hook."""
        log.info(
            "Session {} ({}) enqueued successfully via draft path",
            spec.resource_spec.identity.session_name,
            session_id,
        )

        await self._event_producer.broadcast_events_batch([
            SchedulingBroadcastEvent(
                session_id=session_id,
                creation_id=spec.resource_spec.identity.creation_id,
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
            (
                session_id,
                spec.resource_spec.identity.session_name,
                spec.resource_spec.identity.access_key,
            ),
        )

    @staticmethod
    def _build_requirement_items(
        spec: SessionResourceSpec,
        context: SessionSpecContext,
    ) -> list[ResourceRequirements]:
        """Parse the prepared spec into per-item placement requirements,
        order-aligned with ``spec.kernel_specs``.

        The fitting check only reasons about resource amounts, so no
        kernel-shaped values are materialized.

        Raises:
            ImageNotFound: If a kernel group references an unknown image.
        """
        items: list[ResourceRequirements] = []
        for kernel_spec in spec.kernel_specs:
            resource_input = kernel_spec.execution_spec.resource_input
            image_info = (
                context.global_info.image_infos.get(resource_input.image_id)
                if resource_input.image_id is not None
                else None
            )
            if image_info is None:
                raise ImageNotFound(f"Image '{resource_input.image_id}' not found")
            items.append(
                ResourceRequirements(
                    requested_slots=ResourceRequest(
                        slots={
                            SlotName(k): v
                            for k, v in ResourceSlotEntry.inputs_to_resource_slot(
                                resource_input.resources
                            ).items()
                        }
                    ),
                    required_architecture=ArchName(image_info.architecture),
                    container_count=1,
                )
            )
        return items

    async def _compute_schedule(
        self,
        spec: SessionResourceSpec,
        resource_group_id: ResourceGroupID,
        data: ComputeScheduleData,
    ) -> ComputeScheduleResult:
        items = self._build_requirement_items(spec, data.spec_context)
        failure_hints: dict[int, UnschedulableReasonHint] = {}

        if items:
            plan = PlacementPlan.from_items(items, spec.options.cluster_mode)
            scheduling_target = spec.options.scheduling_target
            criteria = AgentSelectionCriteria(
                session_id=SessionId(UUID(str(spec.identity.session_id))),
                resource_group_id=resource_group_id,
                requirements=plan.requirements(),
                agent_selection_policy=scheduling_target.agent_selection_policy,
                designated_agent_ids=list(scheduling_target.designated_agents) or None,
            )
            # Trackers are throwaway here: the fitting check only needs the
            # immutable observations, never the committed batch state. The
            # same builder as the real scheduling pass is used; only the
            # retry-failure hints are absent.
            trackers = build_agent_trackers(data.resources)
            # A resource group with no candidate agents (NoAgentsInResourceGroupError)
            # is likewise a whole-request error, so it propagates too.
            try:
                await self._agent_selector.select_agents_for_batch_requirements(
                    trackers, criteria, data.limit
                )
            except BatchAgentSelectionFailedError as e:
                for err in e.errors:
                    hint = err.build_remediation_hint()
                    reason = UnschedulableReasonHint(
                        required_reduction=(
                            tuple(
                                ResourceSlotEntry(
                                    resource_type=str(k),
                                    quantity=format(v, "f"),
                                )
                                for k, v in hint.required_reduction.items()
                            )
                            if hint.required_reduction is not None
                            else None
                        ),
                    )
                    for index in plan.groups[err.requirement_index].indices:
                        failure_hints[index] = reason

        kernel_result = [
            ComputeScheduleKernelResult(
                requested_slots=tuple(kernel_spec.execution_spec.resource_input.resources),
                requested_architecture=item.required_architecture,
                success=index not in failure_hints,
                reason_hint=failure_hints.get(index),
            )
            for index, (item, kernel_spec) in enumerate(zip(items, spec.kernel_specs, strict=True))
        ]
        return ComputeScheduleResult(kernel_results=kernel_result)

    async def compute_schedule(
        self,
        resource_group_id: ResourceGroupID,
        draft: SessionResourceSpecDraft,
    ) -> ComputeScheduleResult:
        """Compute whether each kernel of a would-be session fits the target
        resource group's nodes, without provisioning.

        Reuses the enqueue prep chain (vfolder resolution skipped), then drives
        the real agent selector against a live snapshot of the group's agents.
        Results correspond positionally to ``draft.resource_spec.options.kernel_groups``.
        """
        # SessionScopeDraft is used only to fetch dotfile data and container user info.
        # Node fitting does not depend on vfolder mounts, so the storage-RPC
        # resolution is skipped and the per-role mount map stays empty.
        # An unknown resource group (ScalingGroupNotFound) is a request error,
        # not a per-kernel fitting outcome, so let it propagate to the caller.
        fetched = await self._repository.fetch_compute_schedule_data(
            SessionSpecDraft(scope=SessionScopeDraft(), resource_spec=draft),
            resource_group_id,
        )
        resource_spec = await self._spec_preparer.prepare(draft, fetched.spec_context)
        return await self._compute_schedule(resource_spec, resource_group_id, fetched)

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
        message: str = "mark_terminating success",
    ) -> MarkTerminatingResult:
        """
        Mark multiple sessions and their kernels for termination by updating their status to TERMINATING.

        When forced=True, sessions skip TERMINATING and go directly to TERMINATED so the manager
        immediately considers the session done and frees resources.

        Args:
            session_ids: List of session IDs to terminate
            reason: Reason for termination
            forced: If True, skip TERMINATING and set directly to TERMINATED
            message: Optional scheduling-history message for a TERMINATING transition

        Returns:
            MarkTerminatingResult with categorized session statuses
        """
        result = await self._repository.mark_sessions_terminating(
            session_ids,
            reason,
            forced=forced,
            message=message,
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
