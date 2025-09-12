"""Route coordinator for managing route lifecycle."""

import logging
from collections.abc import Mapping
from contextlib import AsyncExitStack
from dataclasses import dataclass
from typing import Optional

from ai.backend.common.clients.http_client.client_pool import ClientPool
from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.schedule.anycast import (
    DoRouteLifecycleEvent,
    DoRouteLifecycleIfNeededEvent,
)
from ai.backend.common.leader.tasks import EventTaskSpec
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.sokovan.deployment.route.executor import RouteExecutor
from ai.backend.manager.sokovan.deployment.route.handlers import (
    HealthCheckRouteHandler,
    ProvisioningRouteHandler,
    RouteHandler,
    TerminatingRouteHandler,
)
from ai.backend.manager.sokovan.deployment.route.handlers.running import RunningRouteHandler
from ai.backend.manager.sokovan.deployment.route.types import RouteLifecycleType
from ai.backend.manager.sokovan.scheduling_controller.scheduling_controller import (
    SchedulingController,
)
from ai.backend.manager.types import DistributedLockFactory

log = BraceStyleAdapter(logging.getLogger(__name__))


@dataclass
class RouteTaskSpec:
    """Specification for a route lifecycle periodic task."""

    lifecycle_type: RouteLifecycleType
    short_interval: Optional[float] = None  # None means no short-cycle task
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
        )
        self._route_handlers = self._init_handlers(executor)

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
            RouteLifecycleType.TERMINATING: TerminatingRouteHandler(
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
        handler = self._route_handlers.get(lifecycle_type)
        if not handler:
            log.warning("No handler for route lifecycle type: {}", lifecycle_type.value)
            return

        async with AsyncExitStack() as stack:
            if handler.lock_id is not None:
                lock_lifetime = self._config_provider.config.manager.session_schedule_lock_lifetime
                await stack.enter_async_context(self._lock_factory(handler.lock_id, lock_lifetime))

            # Get routes by target statuses
            routes = await self._deployment_repository.get_routes_by_statuses(
                handler.target_statuses()
            )
            if not routes:
                log.trace("No routes to process for handler: {}", handler.name())
                return

            log.trace("handler: {}, routes: {}", handler.name(), routes)
            result = await handler.execute(routes)

            # Update route statuses for successful operations
            next_status = handler.next_status()
            if next_status is not None:
                await self._deployment_repository.update_route_status_bulk(
                    set([r.route_id for r in result.successes]),
                    handler.target_statuses(),
                    next_status,
                )

            # Update route statuses for failed operations
            failure_status = handler.failure_status()
            if failure_status is not None:
                await self._deployment_repository.update_route_status_bulk(
                    set([e.route_info.route_id for e in result.errors]),
                    handler.target_statuses(),
                    failure_status,
                )

            try:
                await handler.post_process(result)
            except Exception as e:
                log.error("Error during post-processing: {}", e)

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
            # Terminate routes - only long cycle
            RouteTaskSpec(
                RouteLifecycleType.TERMINATING,
                short_interval=None,  # No short-cycle for cleanup
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
