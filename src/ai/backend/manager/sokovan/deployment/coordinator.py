"""
Deployment coordinator for managing deployment lifecycle.
"""

import logging
from collections.abc import Mapping
from contextlib import AsyncExitStack
from dataclasses import dataclass
from typing import Optional

from ai.backend.common.clients.http_client.client_pool import ClientPool
from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.schedule.anycast import (
    DoDeploymentLifecycleEvent,
    DoDeploymentLifecycleIfNeededEvent,
)
from ai.backend.common.leader.tasks.event_task import EventTaskSpec
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.sokovan.deployment.route.route_controller import RouteController
from ai.backend.manager.sokovan.scheduling_controller.scheduling_controller import (
    SchedulingController,
)
from ai.backend.manager.types import DistributedLockFactory

from .deployment_controller import DeploymentController
from .executor import DeploymentExecutor
from .handlers import (
    CheckPendingDeploymentHandler,
    CheckReplicaDeploymentHandler,
    DeploymentHandler,
    DestroyingDeploymentHandler,
    ReconcileDeploymentHandler,
    ScalingDeploymentHandler,
)
from .types import DeploymentLifecycleType

log = BraceStyleAdapter(logging.getLogger(__name__))


@dataclass
class DeploymentTaskSpec:
    """Specification for a deployment lifecycle periodic task."""

    lifecycle_type: DeploymentLifecycleType
    short_interval: Optional[float] = None  # None means no short-cycle task
    long_interval: float = 60.0
    initial_delay: float = 30.0

    def create_if_needed_event(self) -> DoDeploymentLifecycleIfNeededEvent:
        """Create event for checking if processing is needed."""
        return DoDeploymentLifecycleIfNeededEvent(self.lifecycle_type.value)

    def create_process_event(self) -> DoDeploymentLifecycleEvent:
        """Create event for forced processing."""
        return DoDeploymentLifecycleEvent(self.lifecycle_type.value)

    @property
    def short_task_name(self) -> str:
        """Name for the short-cycle task."""
        return f"deployment_process_if_needed_{self.lifecycle_type.value}"

    @property
    def long_task_name(self) -> str:
        """Name for the long-cycle task."""
        return f"deployment_process_{self.lifecycle_type.value}"


class DeploymentCoordinator:
    """Coordinates deployment-related operations."""

    _valkey_schedule: ValkeyScheduleClient
    _deployment_controller: DeploymentController
    _deployment_repository: DeploymentRepository
    _deployment_handlers: Mapping[DeploymentLifecycleType, DeploymentHandler]
    _lock_factory: DistributedLockFactory
    _config_provider: ManagerConfigProvider
    _event_producer: EventProducer

    def __init__(
        self,
        valkey_schedule: ValkeyScheduleClient,
        deployment_controller: DeploymentController,
        deployment_repository: DeploymentRepository,
        event_producer: EventProducer,
        lock_factory: DistributedLockFactory,
        config_provider: ManagerConfigProvider,
        scheduling_controller: SchedulingController,
        client_pool: ClientPool,
        valkey_stat: ValkeyStatClient,
        route_controller: RouteController,
    ) -> None:
        """Initialize the deployment coordinator."""
        self._valkey_schedule = valkey_schedule
        self._deployment_controller = deployment_controller
        self._deployment_repository = deployment_repository
        self._event_producer = event_producer
        self._lock_factory = lock_factory
        self._config_provider = config_provider
        self._route_controller = route_controller

        # Create deployment executor
        executor = DeploymentExecutor(
            deployment_repo=self._deployment_repository,
            scheduling_controller=scheduling_controller,
            config_provider=self._config_provider,
            client_pool=client_pool,
            valkey_stat=valkey_stat,
        )
        self._deployment_handlers = self._init_handlers(executor)

    def _init_handlers(
        self, executor: DeploymentExecutor
    ) -> Mapping[DeploymentLifecycleType, DeploymentHandler]:
        """Initialize and return the mapping of deployment lifecycle types to their handlers."""
        return {
            DeploymentLifecycleType.CHECK_PENDING: CheckPendingDeploymentHandler(
                deployment_executor=executor,
                deployment_controller=self._deployment_controller,
            ),
            DeploymentLifecycleType.CHECK_REPLICA: CheckReplicaDeploymentHandler(
                deployment_executor=executor,
                deployment_controller=self._deployment_controller,
            ),
            DeploymentLifecycleType.SCALING: ScalingDeploymentHandler(
                deployment_executor=executor,
                deployment_controller=self._deployment_controller,
                route_controller=self._route_controller,
            ),
            DeploymentLifecycleType.RECONCILE: ReconcileDeploymentHandler(
                deployment_executor=executor,
                deployment_controller=self._deployment_controller,
            ),
            DeploymentLifecycleType.DESTROYING: DestroyingDeploymentHandler(
                deployment_executor=executor,
                deployment_controller=self._deployment_controller,
                route_controller=self._route_controller,
            ),
        }

    async def process_deployment_lifecycle(
        self,
        lifecycle_type: DeploymentLifecycleType,
    ) -> None:
        handler = self._deployment_handlers.get(lifecycle_type)
        if not handler:
            log.warning("No handler for deployment lifecycle type: {}", lifecycle_type.value)
            return
        async with AsyncExitStack() as stack:
            if handler.lock_id is not None:
                lock_lifetime = self._config_provider.config.manager.session_schedule_lock_lifetime
                await stack.enter_async_context(self._lock_factory(handler.lock_id, lock_lifetime))
            deployments = await self._deployment_repository.get_endpoints_by_statuses(
                handler.target_statuses()
            )
            if not deployments:
                log.trace("No deployments to process for handler: {}", handler.name())
                return
            log.info("handler: {} - processing {} deployments", handler.name(), len(deployments))
            result = await handler.execute(deployments)
            next_status = handler.next_status()
            if next_status is not None:
                await self._deployment_repository.update_endpoint_lifecycle_bulk(
                    [d.id for d in result.successes],
                    handler.target_statuses(),
                    next_status,
                )
            failure_status = handler.failure_status()
            if failure_status is not None:
                await self._deployment_repository.update_endpoint_lifecycle_bulk(
                    [e.deployment_info.id for e in result.errors],
                    handler.target_statuses(),
                    failure_status,
                )
            try:
                await handler.post_process(result)
            except Exception as e:
                log.error("Error during post-processing: {}", e)

    async def process_if_needed(self, lifecycle_type: DeploymentLifecycleType) -> None:
        """
        Process deployment lifecycle operation if needed (based on internal state).

        Args:
            lifecycle_type: Type of deployment lifecycle operation

        Returns:
            True if operation was performed, False otherwise
        """
        # Check internal state (uses Redis marks)
        if not await self._valkey_schedule.load_and_delete_deployment_mark(lifecycle_type.value):
            return
        await self.process_deployment_lifecycle(lifecycle_type)

    @staticmethod
    def _create_task_specs() -> list[DeploymentTaskSpec]:
        """Create task specifications for all deployment lifecycle types."""
        return [
            # Check pending deployments frequently with both short and long cycles
            DeploymentTaskSpec(
                DeploymentLifecycleType.CHECK_PENDING,
                short_interval=2.0,
                long_interval=30.0,
                initial_delay=10.0,
            ),
            # Check replicas moderately with both short and long cycles
            DeploymentTaskSpec(
                DeploymentLifecycleType.CHECK_REPLICA,
                short_interval=5.0,
                long_interval=30.0,
                initial_delay=10.0,
            ),
            # Scaling operations with both short and long cycles
            DeploymentTaskSpec(
                DeploymentLifecycleType.SCALING,
                short_interval=5.0,
                long_interval=30.0,
                initial_delay=10.0,
            ),
            DeploymentTaskSpec(
                DeploymentLifecycleType.RECONCILE,
                short_interval=None,
                long_interval=30.0,
                initial_delay=10.0,
            ),
            # Check destroying deployments - only long cycle
            DeploymentTaskSpec(
                DeploymentLifecycleType.DESTROYING,
                short_interval=5.0,
                long_interval=60.0,
                initial_delay=25.0,
            ),
        ]

    def create_task_specs(self) -> list[EventTaskSpec]:
        """Create task specifications for deployment lifecycle events."""
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
