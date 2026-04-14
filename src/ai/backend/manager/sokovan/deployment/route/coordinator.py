"""Route coordinator for managing route lifecycle."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from contextlib import AsyncExitStack
from dataclasses import dataclass
from uuid import UUID

from ai.backend.common.clients.http_client.client_pool import ClientPool
from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.schedule.anycast import (
    DoRouteLifecycleEvent,
    DoRouteLifecycleIfNeededEvent,
)
from ai.backend.common.leader.tasks import EventTaskSpec
from ai.backend.common.service_discovery import ServiceDiscovery
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.deployment.types import RouteHealthStatus, RouteStatus
from ai.backend.manager.data.session.types import SchedulingResult
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.routing.conditions import RouteConditions
from ai.backend.manager.repositories.base.creator import BulkCreator
from ai.backend.manager.repositories.base.updater import BatchUpdater
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.repositories.deployment.creators import RouteBatchUpdaterSpec
from ai.backend.manager.repositories.scheduling_history.creators import RouteHistoryCreatorSpec
from ai.backend.manager.sokovan.deployment.route.executor import RouteExecutor
from ai.backend.manager.sokovan.deployment.route.handlers import (
    HealthCheckRouteHandler,
    ProvisioningRouteHandler,
    RouteEvictionHandler,
    RouteHandler,
    ServiceDiscoverySyncHandler,
    TerminatingRouteHandler,
)
from ai.backend.manager.sokovan.deployment.route.handlers.observer import (
    RouteHealthObserver,
    RouteObserver,
)
from ai.backend.manager.sokovan.deployment.route.handlers.running import RunningRouteHandler
from ai.backend.manager.sokovan.deployment.route.recorder import RouteRecorderContext
from ai.backend.manager.sokovan.deployment.route.types import (
    RouteExecutionResult,
    RouteLifecycleType,
)
from ai.backend.manager.sokovan.recorder.types import ExecutionRecord
from ai.backend.manager.sokovan.recorder.utils import extract_sub_steps_for_entity
from ai.backend.manager.sokovan.scheduling_controller.scheduling_controller import (
    SchedulingController,
)
from ai.backend.manager.types import DistributedLockFactory

log = BraceStyleAdapter(logging.getLogger(__name__))


@dataclass
class RouteTaskSpec:
    """Specification for a route lifecycle periodic task."""

    lifecycle_type: RouteLifecycleType
    short_interval: float | None = None  # None means no short-cycle task
    long_interval: float = 60.0
    initial_delay: float = 30.0

    def create_if_needed_event(self) -> DoRouteLifecycleIfNeededEvent:
        """Create event for checking if processing is needed."""
        return DoRouteLifecycleIfNeededEvent(self.lifecycle_type.value)

    def create_process_event(self) -> DoRouteLifecycleEvent:
        """Create event for forced processing."""
        return DoRouteLifecycleEvent(self.lifecycle_type.value)

    @property
    def short_task_name(self) -> str:
        """Name for the short-cycle task."""
        return f"route_process_if_needed_{self.lifecycle_type.value}"

    @property
    def long_task_name(self) -> str:
        """Name for the long-cycle task."""
        return f"route_process_{self.lifecycle_type.value}"


class RouteCoordinator:
    """Coordinates route-related operations."""

    _valkey_schedule: ValkeyScheduleClient
    _deployment_repository: DeploymentRepository
    _route_handlers: Mapping[RouteLifecycleType, RouteHandler]
    _lock_factory: DistributedLockFactory
    _config_provider: ManagerConfigProvider
    _event_producer: EventProducer

    def __init__(
        self,
        valkey_schedule: ValkeyScheduleClient,
        deployment_repository: DeploymentRepository,
        event_producer: EventProducer,
        lock_factory: DistributedLockFactory,
        config_provider: ManagerConfigProvider,
        scheduling_controller: SchedulingController,
        client_pool: ClientPool,
        service_discovery: ServiceDiscovery,
    ) -> None:
        """Initialize the route coordinator."""
        self._valkey_schedule = valkey_schedule
        self._deployment_repository = deployment_repository
        self._event_producer = event_producer
        self._lock_factory = lock_factory
        self._config_provider = config_provider

        # Create route executor
        executor = RouteExecutor(
            deployment_repo=self._deployment_repository,
            scheduling_controller=scheduling_controller,
            config_provider=self._config_provider,
            client_pool=client_pool,
            valkey_schedule=self._valkey_schedule,
            service_discovery=service_discovery,
        )
        self._route_handlers = self._init_handlers(executor)
        self._route_observers = self._init_observers()

    def _init_observers(self) -> Mapping[RouteLifecycleType, RouteObserver]:
        """Initialize route observers (no state transitions)."""
        return {
            RouteLifecycleType.OBSERVE_HEALTH: RouteHealthObserver(
                deployment_repository=self._deployment_repository,
                valkey_schedule=self._valkey_schedule,
            ),
        }

    def _init_handlers(self, executor: RouteExecutor) -> Mapping[RouteLifecycleType, RouteHandler]:
        """Initialize and return the mapping of route lifecycle types to their handlers."""
        return {
            RouteLifecycleType.PROVISIONING: ProvisioningRouteHandler(
                route_executor=executor,
                event_producer=self._event_producer,
            ),
            RouteLifecycleType.RUNNING: RunningRouteHandler(
                route_executor=executor,
                event_producer=self._event_producer,
            ),
            RouteLifecycleType.HEALTH_CHECK: HealthCheckRouteHandler(
                route_executor=executor,
                event_producer=self._event_producer,
            ),
            RouteLifecycleType.ROUTE_EVICTION: RouteEvictionHandler(
                route_executor=executor,
                event_producer=self._event_producer,
            ),
            RouteLifecycleType.TERMINATING: TerminatingRouteHandler(
                route_executor=executor,
                event_producer=self._event_producer,
            ),
            RouteLifecycleType.SERVICE_DISCOVERY_SYNC: ServiceDiscoverySyncHandler(
                route_executor=executor,
                event_producer=self._event_producer,
            ),
        }

    async def process_route_lifecycle(
        self,
        lifecycle_type: RouteLifecycleType,
    ) -> None:
        """Process route lifecycle operation.

        Args:
            lifecycle_type: Type of route lifecycle operation to process
        """
        # Check for observer first (no state transitions)
        observer = self._route_observers.get(lifecycle_type)
        if observer:
            await self._process_observer(observer)
            return

        handler = self._route_handlers.get(lifecycle_type)
        if not handler:
            log.warning("No handler for route lifecycle type: {}", lifecycle_type.value)
            return

        async with AsyncExitStack() as stack:
            if handler.lock_id is not None:
                lock_lifetime = self._config_provider.config.manager.session_schedule_lock_lifetime
                await stack.enter_async_context(self._lock_factory(handler.lock_id, lock_lifetime))

            # Get routes by target lifecycle + health statuses
            target = handler.target_statuses()
            routes = await self._deployment_repository.get_routes_by_statuses(
                target.lifecycle,
                target.health,
            )
            if not routes:
                log.trace("No routes to process for handler: {}", handler.name())
                return

            log.trace("handler: {}, routes: {}", handler.name(), routes)

            # Execute handler with recorder context
            route_ids = [r.route_id for r in routes]
            with RouteRecorderContext.scope(lifecycle_type.value, entity_ids=route_ids) as pool:
                result = await handler.execute(routes)
                all_records = pool.build_all_records()

                # Handle status transitions with history recording
                await self._handle_status_transitions(handler, result, all_records)

            try:
                await handler.post_process(result)
            except Exception as e:
                log.error("Error during post-processing: {}", e)

    async def _process_observer(self, observer: RouteObserver) -> None:
        """Process a route observer (no state transitions).

        Observers collect data (e.g., health check results) without
        changing route status in DB.
        """
        try:
            routes = await self._deployment_repository.get_routes_by_statuses(
                [RouteStatus.RUNNING],
                list(RouteHealthStatus),
            )
            if not routes:
                return

            result = await observer.observe(routes)
            log.debug(
                "Observer {}: observed {} routes",
                observer.name(),
                result.observed_count,
            )
        except Exception:
            log.exception("Error in route observer {}", observer.name())

    async def _handle_status_transitions(
        self,
        handler: RouteHandler,
        result: RouteExecutionResult,
        records: Mapping[UUID, ExecutionRecord],
    ) -> None:
        """Handle status transitions with history recording.

        All transitions (success, failure, and stale) are processed in a single
        transaction to ensure atomicity.

        Args:
            handler: The route handler that was executed
            result: The result of the handler execution
            records: Execution records from the recorder context
        """
        handler_name = handler.name()
        handler_category = handler.category()
        transitions = handler.status_transitions()
        target = handler.target_statuses()
        from_status = target.lifecycle[0] if target.lifecycle else None

        # Collect all batch updaters and history specs
        batch_updaters: list[BatchUpdater[RoutingRow]] = []
        all_history_specs: list[RouteHistoryCreatorSpec] = []

        # Handle success transitions
        if transitions.success is not None and result.successes:
            route_ids = [r.route_id for r in result.successes]
            to_status = transitions.success.status or from_status
            success_history_specs = [
                RouteHistoryCreatorSpec(
                    route_id=r.route_id,
                    deployment_id=r.endpoint_id,
                    category=handler_category,
                    phase=handler_name,
                    result=SchedulingResult.SUCCESS,
                    message=f"{handler_name} completed successfully",
                    from_status=from_status,
                    to_status=to_status,
                    to_health_status=transitions.success.health_status,
                    sub_steps=extract_sub_steps_for_entity(r.route_id, records),
                )
                for r in result.successes
            ]
            updater_spec = RouteBatchUpdaterSpec(
                status=transitions.success.status,
                health_status=transitions.success.health_status,
            )
            batch_updaters.append(
                BatchUpdater(
                    spec=updater_spec,
                    conditions=[
                        RouteConditions.by_ids(route_ids),
                        RouteConditions.by_lifecycle_statuses(target.lifecycle),
                    ],
                )
            )
            all_history_specs.extend(success_history_specs)

        # Handle failure transitions
        if transitions.failure is not None and result.errors:
            route_ids = [e.route_info.route_id for e in result.errors]
            to_status = transitions.failure.status or from_status
            failure_history_specs = [
                RouteHistoryCreatorSpec(
                    route_id=e.route_info.route_id,
                    deployment_id=e.route_info.endpoint_id,
                    category=handler_category,
                    phase=handler_name,
                    result=SchedulingResult.FAILURE,
                    message=e.reason,
                    from_status=from_status,
                    to_status=to_status,
                    to_health_status=transitions.failure.health_status,
                    error_code=e.error_code,
                    sub_steps=extract_sub_steps_for_entity(e.route_info.route_id, records),
                )
                for e in result.errors
            ]
            batch_updaters.append(
                BatchUpdater(
                    spec=RouteBatchUpdaterSpec(
                        status=transitions.failure.status,
                        health_status=transitions.failure.health_status,
                    ),
                    conditions=[
                        RouteConditions.by_ids(route_ids),
                        RouteConditions.by_lifecycle_statuses(target.lifecycle),
                    ],
                )
            )
            all_history_specs.extend(failure_history_specs)

        # Handle stale transitions
        if transitions.stale is not None and result.stale:
            route_ids = [r.route_id for r in result.stale]
            to_status = transitions.stale.status or from_status
            stale_history_specs = [
                RouteHistoryCreatorSpec(
                    route_id=r.route_id,
                    deployment_id=r.endpoint_id,
                    category=handler_category,
                    phase=handler_name,
                    result=SchedulingResult.SUCCESS,
                    message=f"{handler_name} marked route as stale",
                    from_status=from_status,
                    to_status=to_status,
                    to_health_status=transitions.stale.health_status,
                    sub_steps=extract_sub_steps_for_entity(r.route_id, records),
                )
                for r in result.stale
            ]
            batch_updaters.append(
                BatchUpdater(
                    spec=RouteBatchUpdaterSpec(
                        status=transitions.stale.status,
                        health_status=transitions.stale.health_status,
                    ),
                    conditions=[
                        RouteConditions.by_ids(route_ids),
                        RouteConditions.by_lifecycle_statuses(target.lifecycle),
                    ],
                )
            )
            all_history_specs.extend(stale_history_specs)

        # Execute all updates in a single transaction
        if batch_updaters:
            await self._deployment_repository.update_route_status_bulk_with_history(
                batch_updaters, BulkCreator(specs=all_history_specs)
            )

    async def process_if_needed(self, lifecycle_type: RouteLifecycleType) -> None:
        """
        Process route lifecycle operation if needed (based on internal state).

        Args:
            lifecycle_type: Type of route lifecycle operation

        Returns:
            True if operation was performed, False otherwise
        """
        # Check internal state (uses Redis marks)
        if not await self._valkey_schedule.load_and_delete_route_mark(lifecycle_type.value):
            return
        await self.process_route_lifecycle(lifecycle_type)

    @staticmethod
    def _create_task_specs() -> list[RouteTaskSpec]:
        """Create task specifications for all route lifecycle types."""
        return [
            # Provision routes frequently with both short and long cycles
            RouteTaskSpec(
                RouteLifecycleType.PROVISIONING,
                short_interval=5.0,
                long_interval=60.0,
                initial_delay=10.0,
            ),
            # Check running routes frequently with both short and long cycles
            RouteTaskSpec(
                RouteLifecycleType.RUNNING,
                short_interval=10.0,
                long_interval=60.0,
                initial_delay=10.0,
            ),
            # Health check routes - frequent checking
            RouteTaskSpec(
                RouteLifecycleType.HEALTH_CHECK,
                short_interval=5.0,
                long_interval=60.0,
                initial_delay=20.0,
            ),
            # Evict unhealthy routes based on scaling group config - moderate frequency
            RouteTaskSpec(
                RouteLifecycleType.ROUTE_EVICTION,
                short_interval=None,  # No short-cycle for eviction
                long_interval=60.0,  # Every 1 minute
                initial_delay=30.0,
            ),
            # Terminate routes - only long cycle
            RouteTaskSpec(
                RouteLifecycleType.TERMINATING,
                short_interval=None,  # No short-cycle for cleanup
                long_interval=30.0,
                initial_delay=15.0,
            ),
            # Service discovery sync - only long cycle
            RouteTaskSpec(
                RouteLifecycleType.SERVICE_DISCOVERY_SYNC,
                short_interval=None,  # No short-cycle for sync
                long_interval=60.0,
                initial_delay=30.0,
            ),
            # Health observer - manager fallback health check for stale routes
            RouteTaskSpec(
                RouteLifecycleType.OBSERVE_HEALTH,
                short_interval=None,
                long_interval=30.0,
                initial_delay=15.0,
            ),
        ]

    def create_task_specs(self) -> list[EventTaskSpec]:
        """Create task specifications for route lifecycle events."""
        task_specs = self._create_task_specs()
        specs: list[EventTaskSpec] = []

        for spec in task_specs:
            # Create short-cycle task spec if specified
            if spec.short_interval is not None:
                short_spec = EventTaskSpec(
                    name=spec.short_task_name,
                    event_factory=spec.create_if_needed_event,
                    interval=spec.short_interval,
                    initial_delay=0.0,  # Start immediately for short tasks
                )
                specs.append(short_spec)

            # Create long-cycle task spec (always present)
            long_spec = EventTaskSpec(
                name=spec.long_task_name,
                event_factory=spec.create_process_event,
                interval=spec.long_interval,
                initial_delay=spec.initial_delay,
            )
            specs.append(long_spec)

        return specs
