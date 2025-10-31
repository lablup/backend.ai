"""Scheduling controller for managing session lifecycle and scheduling operations."""

import logging
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
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    AllowedScalingGroup,
    SessionCreationSpec,
)
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.sokovan.scheduling_controller.types import SessionValidationSpec

from .calculators.resource_calculator import ResourceCalculator
from .preparers import (
    ClusterConfigurationRule,
    InternalDataRule,
    MountPreparationRule,
    SessionPreparer,
)
from .resolvers.scaling_group_resolver import ScalingGroupResolver
from .validators import (
    ClusterValidationRule,
    ContainerLimitRule,
    MountNameValidationRule,
    ScalingGroupAccessRule,
    ServicePortRule,
    SessionTypeRule,
    SessionValidator,
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
    _scaling_group_resolver: ScalingGroupResolver
    _validator: SessionValidator
    _preparer: SessionPreparer
    _resource_calculator: ResourceCalculator
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

        # Initialize services
        self._scaling_group_resolver = ScalingGroupResolver()

        # Initialize validator with rules
        validator_rules = [
            ContainerLimitRule(),
            ScalingGroupAccessRule(),
            SessionTypeRule(),
            ServicePortRule(),
            ClusterValidationRule(),
            MountNameValidationRule(),
        ]
        self._validator = SessionValidator(validator_rules)

        # Initialize preparer with rules
        preparer_rules = [
            ClusterConfigurationRule(),
            MountPreparationRule(),
            InternalDataRule(),
        ]
        self._preparer = SessionPreparer(preparer_rules)

        # Initialize resource calculator (still needed for resource calculations)
        self._resource_calculator = ResourceCalculator(args.config_provider)

    async def _resolve_scaling_group(
        self,
        session_spec: SessionCreationSpec,
    ) -> AllowedScalingGroup:
        """
        Resolve the scaling group for the session.

        If scaling group is specified in spec, use it.
        Otherwise, fetch allowed groups and auto-select.

        Args:
            session_spec: Session creation specification

        Returns:
            str: The resolved scaling group name
        """
        # Fetch allowed groups to determine the scaling group
        allowed_groups = await self._repository.query_allowed_scaling_groups(
            session_spec.user_scope.domain_name,
            str(session_spec.user_scope.group_id),
            session_spec.access_key,
        )
        if session_spec.scaling_group:
            for sg in allowed_groups:
                if sg.name == session_spec.scaling_group:
                    return sg
            raise InvalidAPIParameters(
                f"Scaling group '{session_spec.scaling_group}' is not accessible"
            )

        # Resolve the scaling group
        return self._scaling_group_resolver.resolve(
            session_spec,
            allowed_groups,
        )

    async def enqueue_session(
        self,
        session_spec: SessionCreationSpec,
    ) -> SessionId:
        """
        Enqueue a new session for scheduling.

        Steps:
        1. Resolve scaling group
        2. Fetch all required data from repository
        3. Validate the specification
        4. Calculate resources and prepare session data
        5. Enqueue in repository

        Args:
            session_spec: Session creation specification

        Returns:
            SessionId: The ID of the created session
        """
        # Phase 1: Resolve scaling group
        with self._metric_observer.measure_phase(
            "scheduling_controller", "", "resolve_scaling_group"
        ):
            validated_scaling_group = await self._resolve_scaling_group(session_spec)

        # Phase 2: Fetch all required data
        with self._metric_observer.measure_phase(
            "scheduling_controller", validated_scaling_group.name, "fetch_data"
        ):
            allowed_vfolder_types = list(
                await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
            )
            creation_context = await self._repository.fetch_session_creation_data(
                session_spec,
                validated_scaling_group.name,
                self._storage_manager,
                allowed_vfolder_types,
            )

        # Phase 3: Validate
        with self._metric_observer.measure_phase(
            "scheduling_controller", validated_scaling_group.name, "validation"
        ):
            self._validator.validate(
                session_spec,
                creation_context,
            )

        # Phase 4: Calculate resources and prepare session data
        with self._metric_observer.measure_phase(
            "scheduling_controller", validated_scaling_group.name, "preparation"
        ):
            # Pre-calculate resources
            calculated_resources = await self._resource_calculator.calculate(
                validated_scaling_group,
                session_spec,
                creation_context,
            )

            # Prepare session data with calculated resources
            session_data = await self._preparer.prepare(
                session_spec,
                validated_scaling_group,
                creation_context,
                calculated_resources,
            )

        hook_result = await self._hook_plugin_ctx.dispatch(
            "PRE_ENQUEUE_SESSION",
            (session_data.id, session_data.name, session_data.access_key),
            return_when=ALL_COMPLETED,
        )
        if hook_result.status != PASSED:
            raise RejectedByHook.from_hook_result(hook_result)

        # Phase 5: Enqueue in repository
        with self._metric_observer.measure_phase(
            "scheduling_controller", validated_scaling_group.name, "enqueue"
        ):
            session_id = await self._repository.enqueue_session(session_data)

        log.info(
            "Session {} ({}) enqueued successfully",
            session_data.name,
            session_id,
        )
        try:
            await self.mark_scheduling_needed(ScheduleType.SCHEDULE)
        except Exception as e:
            log.warning(
                "Failed to request scheduling for session {}: {}",
                session_id,
                e,
            )
        await self._hook_plugin_ctx.notify(
            "POST_ENQUEUE_SESSION",
            (session_id, session_data.name, session_data.access_key),
        )
        return session_id

    async def mark_scheduling_needed(self, schedule_type: ScheduleType) -> None:
        """
        Request a scheduling operation for the next cycle.

        This is the public interface for requesting scheduling operations.
        The actual scheduling will be handled internally by the coordinator.

        Args:
            schedule_type: Type of scheduling to request
        """
        await self._valkey_schedule.mark_schedule_needed(schedule_type.value)
        log.debug("Requested scheduling for type: {}", schedule_type.value)

    async def mark_sessions_for_termination(
        self,
        session_ids: list[SessionId],
        reason: str = "USER_REQUESTED",
    ) -> MarkTerminatingResult:
        """
        Mark multiple sessions and their kernels for termination by updating their status to TERMINATING.

        This method handles the lifecycle management of sessions by marking them
        for termination, which will be processed by the scheduler's terminate_sessions method.
        It also automatically requests TERMINATE scheduling if sessions were processed.

        Args:
            session_ids: List of session IDs to terminate
            reason: Reason for termination

        Returns:
            MarkTerminatingResult with categorized session statuses
        """
        result = await self._repository.mark_sessions_terminating(session_ids, reason)

        if result.has_processed():
            log.info(
                "Marked {} sessions for termination (cancelled: {}, terminating: {})",
                result.processed_count(),
                len(result.cancelled_sessions),
                len(result.terminating_sessions),
            )

            cancelled_events: list[AbstractBroadcastEvent] = [
                SchedulingBroadcastEvent(
                    session_id=session_id,
                    creation_id="",
                    status_transition=str(SessionStatus.CANCELLED),
                    reason=reason,
                )
                for session_id in result.cancelled_sessions
            ]
            if cancelled_events:
                await self._event_producer.broadcast_events_batch(cancelled_events)
            # Record metric for termination attempts
            self._operation_metrics.observe_success(
                operation="mark_sessions_terminating",
                count=result.processed_count(),
            )
            # Request termination scheduling for the next cycle
            await self.mark_scheduling_needed(ScheduleType.TERMINATE)

        return result

    async def validate_session_spec(self, spec: SessionValidationSpec) -> None:
        # TODO: Refactor to use ValidationRule
        alias_folders = spec.mount_spec.mount_map.values()
        if len(alias_folders) != len(set(alias_folders)):
            raise InvalidAPIParameters("Duplicate alias folder name exists.")
        original_folders = spec.mount_spec.mount_map.keys()
        alias_name: str
        for alias_name in alias_folders:
            if alias_name.startswith("/home/work/"):
                alias_name = alias_name.replace("/home/work/", "")
            if alias_name == "":
                raise InvalidAPIParameters("Alias name cannot be empty.")
            if not _verify_vfolder_name(alias_name):
                raise InvalidAPIParameters(str(alias_name) + " is reserved for internal path.")
            if alias_name in original_folders:
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
            raise InvalidAPIParameters(f"Invalid resource allocation: {e}")
        # Validate Image
        user = current_user()
        if user is None:
            raise InvalidAPIParameters("User context is required for image validation.")
        await self._repository.check_available_image(
            spec.image_identifier, user.domain_name, user.user_id
        )


def _verify_vfolder_name(folder: str) -> bool:
    if folder in RESERVED_VFOLDERS:
        return False
    for pattern in RESERVED_VFOLDER_PATTERNS:
        if pattern.match(folder):
            return False
    return True
