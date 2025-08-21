"""Auto-scaler for deployment management with global timer integration."""

import logging
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Self, override

from ai.backend.common.distributed import GlobalTimer
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.types import AbstractAnycastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.model_serving.types import RouteStatus
from ai.backend.manager.defs import LockID

if TYPE_CHECKING:
    from ai.backend.manager.types import DistributedLockFactory

    from .deployment_controller import DeploymentController

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class DeploymentAutoScaleEvent(AbstractAnycastEvent):
    """Event for triggering deployment auto-scaling."""

    @override
    def serialize(self) -> tuple:
        return tuple()

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
        return cls()

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.MODEL_SERVING

    @classmethod
    @override
    def event_name(cls) -> str:
        return "deployment_auto_scale"

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


@dataclass
class AutoScalerConfig:
    """Configuration for auto-scaler."""

    check_interval: float = 30.0  # Check every 30 seconds
    initial_delay: float = 60.0  # Wait 1 minute before first check
    lock_timeout: float = 45.0  # Lock timeout slightly longer than interval


class DeploymentAutoScaler:
    """
    Auto-scaler for deployment management.

    This class runs on a global timer to periodically:
    - Check deployment health
    - Scale services based on metrics
    - Recover failed routes
    """

    _deployment_controller: "DeploymentController"
    _event_producer: EventProducer
    _lock_factory: "DistributedLockFactory"
    _config: AutoScalerConfig
    _timer: GlobalTimer

    def __init__(
        self,
        deployment_controller: "DeploymentController",
        event_producer: EventProducer,
        lock_factory: "DistributedLockFactory",
        config: Optional[AutoScalerConfig] = None,
    ) -> None:
        self._deployment_controller = deployment_controller
        self._event_producer = event_producer
        self._lock_factory = lock_factory
        self._config = config or AutoScalerConfig()

    async def init_timer(self) -> None:
        """Initialize the global timer for auto-scaling operations."""
        # Create timer for auto-scaling operations
        # Following the pattern from sokovan.py
        self._timer = GlobalTimer(
            self._lock_factory(
                LockID.LOCKID_DEPLOYMENT_AUTO_SCALER,  # Need to add this to LockID enum
                self._config.lock_timeout,
            ),
            self._event_producer,
            lambda: DeploymentAutoScaleEvent(),  # Create event for auto-scaling
            interval=self._config.check_interval,
            initial_delay=self._config.initial_delay,
            task_name="deployment_auto_scaler",
        )

        await self._timer.join()
        log.info(
            "Deployment auto-scaler timer initialized (interval: {}s)",
            self._config.check_interval,
        )

    async def shutdown_timer(self) -> None:
        """Shutdown the auto-scaler timer gracefully."""
        if hasattr(self, "_timer"):
            await self._timer.leave()
            log.info("Deployment auto-scaler timer stopped")

    async def run_auto_scaling_cycle(self) -> None:
        """
        Run a single auto-scaling cycle.

        This method should be called by an event handler when DeploymentAutoScaleEvent is received.
        It performs:
        1. Sync deployment states
        2. Check auto-scaling rules
        3. Scale services as needed
        4. Recover failed routes
        """
        try:
            log.debug("Starting auto-scaling cycle")

            # Sync deployment states first
            await self._deployment_controller.sync_deployments()

            # Get all active endpoints and check for failed routes
            endpoints = (
                await self._deployment_controller._deployment_repository.get_all_active_endpoints()
            )

            for endpoint in endpoints:
                try:
                    # Check if endpoint needs recovery
                    routes = await self._deployment_controller._deployment_repository.get_routes_by_endpoint(
                        endpoint.endpoint_id
                    )

                    failed_routes = [
                        route
                        for route in routes
                        if route.status in [RouteStatus.FAILED_TO_START, RouteStatus.UNHEALTHY]
                        or route.session_id is None
                    ]

                    if failed_routes and endpoint.desired_session_count > (
                        len(routes) - len(failed_routes)
                    ):
                        # Attempt to recover failed routes
                        log.info(
                            "Recovering {} failed routes for endpoint {}",
                            len(failed_routes),
                            endpoint.endpoint_id,
                        )
                        await self.recover_failed_routes(str(endpoint.endpoint_id))

                    # TODO: Check auto-scaling rules when they are implemented
                    # This would involve checking metrics and scaling based on rules

                except Exception as e:
                    log.error(
                        "Error processing endpoint {} in auto-scaling cycle: {}",
                        endpoint.endpoint_id,
                        e,
                    )

            log.debug("Auto-scaling cycle completed")

        except Exception as e:
            log.error("Error in auto-scaling cycle: {}", e, exc_info=True)

    async def check_and_scale(self, endpoint_id: str) -> None:
        """
        Check and scale a specific endpoint based on its auto-scaling rules.

        This can be called manually or by the timer cycle.

        Args:
            endpoint_id: ID of the endpoint to check
        """
        # TODO: Implement when auto-scaling rules are added
        pass

    async def recover_failed_routes(self, endpoint_id: str) -> None:
        """
        Attempt to recover failed routes for an endpoint.

        This recreates sessions for failed routes up to the desired replica count.

        Args:
            endpoint_id: ID of the endpoint to recover
        """
        try:
            endpoint_uuid = uuid.UUID(endpoint_id)

            # Get endpoint info and current routes
            endpoint_info = (
                await self._deployment_controller._deployment_repository.get_endpoint_info(
                    endpoint_uuid
                )
            )
            if not endpoint_info:
                log.warning("Endpoint {} not found during recovery", endpoint_id)
                return

            routes = (
                await self._deployment_controller._deployment_repository.get_routes_by_endpoint(
                    endpoint_uuid
                )
            )

            # Identify failed routes that need recovery
            failed_routes = [
                route
                for route in routes
                if route.status in [RouteStatus.FAILED_TO_START, RouteStatus.UNHEALTHY]
                or route.session_id is None
            ]

            if not failed_routes:
                log.debug("No failed routes to recover for endpoint {}", endpoint_id)
                return

            log.info(
                "Recovering {} failed routes for endpoint {}",
                len(failed_routes),
                endpoint_id,
            )

            # For each failed route, create a new session
            for idx, route in enumerate(failed_routes):
                try:
                    # Delete the failed route first
                    await self._deployment_controller._deployment_repository.delete_route(
                        route.route_id
                    )

                    # Create a new route
                    new_route_id = (
                        await self._deployment_controller._deployment_repository.create_route(
                            endpoint_uuid,
                            traffic_ratio=1.0 / endpoint_info.desired_session_count,
                        )
                    )

                    # Create session spec from endpoint info
                    session_spec = (
                        await self._deployment_controller._prepare_session_spec_from_endpoint(
                            endpoint_info,
                            len(routes) - len(failed_routes) + idx,  # Calculate replica index
                            endpoint_uuid,
                            new_route_id,
                        )
                    )

                    # Enqueue new session
                    session_id = (
                        await self._deployment_controller._scheduling_controller.enqueue_session(
                            session_spec
                        )
                    )

                    # Update route with new session ID
                    await self._deployment_controller._deployment_repository.update_route_session(
                        new_route_id,
                        session_id,
                    )

                    log.info(
                        "Successfully recovered route {} with new session {} for endpoint {}",
                        new_route_id,
                        session_id,
                        endpoint_id,
                    )

                except Exception as e:
                    log.error(
                        "Failed to recover route {} for endpoint {}: {}",
                        route.route_id,
                        endpoint_id,
                        e,
                    )

        except Exception as e:
            log.error(
                "Error in route recovery for endpoint {}: {}",
                endpoint_id,
                e,
                exc_info=True,
            )
