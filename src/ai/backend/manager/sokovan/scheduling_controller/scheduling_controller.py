"""Scheduling controller for managing session lifecycle and scheduling operations."""

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai.backend.manager.repositories.deployment.repository import DeploymentRepository

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import SessionId
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.deployment.creator import DeploymentCreator
from ai.backend.manager.metrics.scheduler import SchedulerPhaseMetricObserver
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.repositories.scheduler import (
    MarkTerminatingResult,
    SchedulerRepository,
)
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    SessionCreationSpec,
)
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.sokovan.deployment.validators import (
    DeploymentValidator,
    ModelVFolderValidationRule,
)

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
    SessionValidator,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class SchedulingControllerArgs:
    """Arguments for initializing SchedulingController."""

    repository: SchedulerRepository
    deployment_repository: "DeploymentRepository"
    config_provider: ManagerConfigProvider
    storage_manager: StorageSessionManager
    event_producer: EventProducer
    valkey_schedule: ValkeyScheduleClient
    network_plugin_ctx: NetworkPluginContext


class SchedulingController:
    """Controller for session lifecycle and scheduling operations management."""

    _repository: SchedulerRepository
    _deployment_repository: "DeploymentRepository"
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
    _deployment_validator: DeploymentValidator

    def __init__(self, args: SchedulingControllerArgs) -> None:
        """Initialize the scheduling controller with required services."""
        self._repository = args.repository
        self._deployment_repository = args.deployment_repository
        self._config_provider = args.config_provider
        self._storage_manager = args.storage_manager
        self._event_producer = args.event_producer
        self._valkey_schedule = args.valkey_schedule
        self._network_plugin_ctx = args.network_plugin_ctx

        # Initialize metric observer (singleton)
        self._metric_observer = SchedulerPhaseMetricObserver.instance()

        # Initialize services
        self._scaling_group_resolver = ScalingGroupResolver()

        # Initialize validator with rules
        validator_rules = [
            ContainerLimitRule(),
            ScalingGroupAccessRule(),
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

        # Initialize deployment validator with rules
        deployment_validator_rules = [
            ModelVFolderValidationRule(),
        ]
        self._deployment_validator = DeploymentValidator(deployment_validator_rules)

    async def _resolve_scaling_group(
        self,
        session_spec: SessionCreationSpec,
    ) -> str:
        """
        Resolve the scaling group for the session.

        If scaling group is specified in spec, use it.
        Otherwise, fetch allowed groups and auto-select.

        Args:
            session_spec: Session creation specification

        Returns:
            str: The resolved scaling group name
        """
        if session_spec.scaling_group:
            return session_spec.scaling_group

        # Fetch allowed groups to determine the scaling group
        allowed_groups = await self._repository.query_allowed_scaling_groups(
            session_spec.user_scope.domain_name,
            str(session_spec.user_scope.group_id),
            session_spec.access_key,
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
            "scheduling_controller", validated_scaling_group, "fetch_data"
        ):
            allowed_vfolder_types = list(
                await self._config_provider.legacy_etcd_config_loader.get_vfolder_types()
            )

            creation_context = await self._repository.fetch_session_creation_data(
                session_spec,
                validated_scaling_group,
                self._storage_manager,
                allowed_vfolder_types,
            )

        # Phase 3: Validate
        with self._metric_observer.measure_phase(
            "scheduling_controller", validated_scaling_group, "validation"
        ):
            self._validator.validate(
                session_spec,
                creation_context,
            )

        # Phase 4: Calculate resources and prepare session data
        with self._metric_observer.measure_phase(
            "scheduling_controller", validated_scaling_group, "preparation"
        ):
            # Pre-calculate resources
            calculated_resources = await self._resource_calculator.calculate(
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

        # Phase 5: Enqueue in repository
        with self._metric_observer.measure_phase(
            "scheduling_controller", validated_scaling_group, "enqueue"
        ):
            session_id = await self._repository.enqueue_session(session_data)

        log.info(
            "Session {} ({}) enqueued successfully",
            session_data.name,
            session_id,
        )
        try:
            await self.request_scheduling(ScheduleType.SCHEDULE)
        except Exception as e:
            log.warning(
                "Failed to request scheduling for session {}: {}",
                session_id,
                e,
            )
        return session_id

    async def request_scheduling(self, schedule_type: ScheduleType) -> None:
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
            # Request termination scheduling for the next cycle
            await self.request_scheduling(ScheduleType.TERMINATE)

        return result

    async def dry_run_deployment(
        self,
        deployment_spec: DeploymentCreator,
    ) -> None:
        """
        Perform a dry-run validation of a deployment without actually creating it.

        This method validates all aspects of a deployment:
        1. Fetches deployment preparation data (vfolder info, group validation, endpoint name check)
        2. Reads service definition from model vfolder if available
        3. Validates the deployment specification

        Args:
            deployment_spec: Deployment creation specification

        Raises:
            ModelVFolderNotFound: If model vfolder doesn't exist
            InvalidVFolderOwnership: If vfolder has project ownership
            GroupNotFound: If group doesn't exist
            DuplicateEndpointName: If endpoint name already exists
        """
        # Fetch deployment preparation data (will raise exceptions if validation fails)
        prep_data = await self._deployment_repository.fetch_deployment_preparation_data(
            vfolder_id=deployment_spec.model_id,
            domain_name=deployment_spec.domain,
            group_name=deployment_spec.project,
            endpoint_name=deployment_spec.name,
        )

        # Fetch service definition from storage if available
        service_definition = await self._deployment_repository.fetch_service_definition(
            deployment_spec.model_id
        )

        # Run validation rules
        await self._deployment_validator.validate(
            deployment_spec,
            prep_data,
            service_definition,
        )
