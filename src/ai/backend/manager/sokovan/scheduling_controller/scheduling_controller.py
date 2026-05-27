"""Scheduling controller for managing session lifecycle and scheduling operations."""

import logging
from collections.abc import Sequence
from dataclasses import dataclass

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.contexts.user import current_user
from ai.backend.common.defs import RESERVED_VFOLDER_PATTERNS, RESERVED_VFOLDERS
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.session.broadcast import SchedulingBroadcastEvent
from ai.backend.common.events.types import AbstractBroadcastEvent
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.plugin.hook import ALL_COMPLETED, PASSED, HookPluginContext
from ai.backend.common.types import ResourceSlot, SessionId
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.session.draft import SessionSpecDraft
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.errors.common import RejectedByHook
from ai.backend.manager.metrics.scheduler import (
    SchedulerOperationMetricObserver,
    SchedulerPhaseMetricObserver,
)
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.repositories.scheduler import (
    MarkTerminatingResult,
    SchedulerRepository,
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

    async def enqueue_session_from_draft(
        self,
        draft: SessionSpecDraft,
    ) -> SessionId:
        """Draft-based session enqueue entry point.

        Only input is the :class:`SessionSpecDraft` — request-envelope
        extras (sudo, model-definition overlay) ride on
        ``draft.internal_data_extras``. Every validation-adjacent DB read
        (image metadata, keypair policy, resource-group network,
        container uid/gid, resolved vfolder mounts, dotfiles, active
        session count) flows through
        :meth:`SchedulerRepository.fetch_session_spec_contexts`.

        Flow:

        1. Batch fetch — resolve prep / validation context bundles.
        2. Preparer chain — draft → finalized ``SessionSpec``.
        3. ``PRE_ENQUEUE_SESSION`` hook — rejected calls raise.
        4. Validator chain — spec + context.
        5. ``SchedulerRepository.enqueue_session_from_spec`` — writer tx.
        6. Broadcast PENDING + ask the coordinator to schedule.
        7. ``POST_ENQUEUE_SESSION`` hook notification.
        """
        rg_name = str(draft.scope.resource_group_name) if draft.scope.resource_group_name else ""

        allowed_vfolder_types = list(
            await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
        )

        with self._metric_observer.measure_phase(
            "scheduling_controller", rg_name, "spec_fetch_contexts"
        ):
            fetched = await self._repository.fetch_session_spec_contexts(
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
            vfolder_mounts_by_role=fetched.vfolder_mounts_by_role,
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
            "scheduling_controller", rg_name, "spec_preparation"
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

        with self._metric_observer.measure_phase(
            "scheduling_controller", rg_name, "spec_validation"
        ):
            self._spec_validator.validate(spec, val_ctx)

        with self._metric_observer.measure_phase("scheduling_controller", rg_name, "enqueue"):
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
