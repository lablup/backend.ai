"""Route executor for handling route lifecycle operations."""

import logging
from collections.abc import Sequence
from uuid import UUID

from ai.backend.common.clients.http_client.client_pool import ClientPool
from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.types import SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.repositories.deployment.types import RouteData
from ai.backend.manager.repositories.scheduler.types.session_creation import SessionCreationSpec
from ai.backend.manager.sokovan.deployment.route.types import (
    RouteExecutionError,
    RouteExecutionResult,
)
from ai.backend.manager.sokovan.scheduling_controller.scheduling_controller import (
    SchedulingController,
)

log = BraceStyleAdapter(logging.getLogger(__name__))


class RouteExecutor:
    """Executor for route lifecycle operations."""

    def __init__(
        self,
        deployment_repo: DeploymentRepository,
        scheduling_controller: SchedulingController,
        config_provider: ManagerConfigProvider,
        client_pool: ClientPool,
        valkey_schedule: ValkeyScheduleClient,
    ):
        self._deployment_repo = deployment_repo
        self._scheduling_controller = scheduling_controller
        self._config_provider = config_provider
        self._client_pool = client_pool
        self._valkey_schedule = valkey_schedule

    async def provision_routes(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """Provision routes by creating sessions.

        Args:
            routes: Routes to provision

        Returns:
            Result containing successful and failed routes
        """
        route_session_ids: dict[UUID, SessionId] = {}
        successes: list[RouteData] = []
        errors: list[RouteExecutionError] = []
        endpoint_ids = {route.endpoint_id for route in routes}
        deployments = await self._deployment_repo.get_endpoints_by_ids(endpoint_ids)
        deployment_map = {dep.id: dep for dep in deployments}

        for route in routes:
            if route.session_id is not None:
                log.debug("Route {} already has a session, skipping", route.route_id)
                successes.append(route)
                continue
            try:
                deployment = deployment_map.get(route.endpoint_id)
                if deployment is None:
                    raise ValueError(f"Deployment not found for endpoint {route.endpoint_id}")

                # Fetch deployment context with all necessary data
                deployment_context = await self._deployment_repo.fetch_deployment_context(
                    deployment
                )

                # Create session with full context
                session_id = await self._scheduling_controller.enqueue_session(
                    SessionCreationSpec.from_deployment_info(
                        deployment_info=deployment,
                        context=deployment_context,
                        route_id=route.route_id,
                    )
                )
                route_session_ids[route.route_id] = session_id
                successes.append(route)
            except Exception as e:
                log.exception("Failed to provision route {}: {}", route.route_id, e)
                errors.append(
                    RouteExecutionError(
                        route_info=route,
                        reason="Failed to provision",
                        error_detail=str(e),
                    )
                )
        if route_session_ids:
            await self._deployment_repo.update_route_sessions(route_session_ids)
        return RouteExecutionResult(
            successes=successes,
            errors=errors,
        )

    async def terminate_routes(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """Terminate routes by destroying sessions.

        Args:
            routes: Routes to terminate

        Returns:
            Result containing successful and failed routes
        """
        target_session_ids: list[SessionId] = []
        for route in routes:
            if not route.session_id:
                log.debug("Route {} has no session, skipping termination", route.route_id)
                continue
            target_session_ids.append(route.session_id)
        await self._scheduling_controller.mark_sessions_for_termination(target_session_ids)
        await self._deployment_repo.delete_routes_by_route_ids({route.route_id for route in routes})
        return RouteExecutionResult(
            successes=list(routes),
            errors=[],
        )

    async def check_running_routes(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """Check health status of running routes.

        Args:
            routes: Routes to check (should be HEALTHY or UNHEALTHY status)

        Returns:
            Result containing routes with updated health status
        """
        successes: list[RouteData] = []
        errors: list[RouteExecutionError] = []
        route_ids = {route.route_id for route in routes}
        session_statuses = await self._deployment_repo.fetch_session_statuses_by_route_ids(
            route_ids
        )
        for route in routes:
            session_status = session_statuses.get(route.route_id)
            if session_status is None:
                log.debug("No session found for route {}, marking as error", route.route_id)
                errors.append(
                    RouteExecutionError(
                        route_info=route,
                        reason="No associated session found",
                        error_detail="Session not found",
                    )
                )
                continue

            if session_status.is_terminal():
                errors.append(
                    RouteExecutionError(
                        route_info=route,
                        reason="Session is in terminal state",
                        error_detail=f"Session status: {session_status.value}",
                    )
                )
                continue
            successes.append(route)
        return RouteExecutionResult(
            successes=successes,
            errors=errors,
        )

    async def check_route_health(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """
        Check health status of routes using Redis health data.

        Args:
            routes: Routes to check health for

        Returns:
            Result containing healthy and unhealthy routes
        """
        successes: list[RouteData] = []
        errors: list[RouteExecutionError] = []

        # Get health status for all routes from Redis
        route_ids = [str(route.route_id) for route in routes]
        health_statuses = await self._valkey_schedule.check_route_health_status(route_ids)

        for route in routes:
            route_id_str = str(route.route_id)
            health_status = health_statuses.get(route_id_str, None)
            if not health_status:
                # No health data - Redis TTL expired, mark as unhealthy
                errors.append(
                    RouteExecutionError(
                        route_info=route,
                        reason="No health data available",
                        error_detail="Health check data expired or not found",
                    )
                )
                continue
            if health_status.is_alive():
                successes.append(route)
            else:
                # One or both checks failed
                failure_reasons = []
                if not health_status.readiness:
                    failure_reasons.append("readiness check failed")
                if not health_status.liveness:
                    failure_reasons.append("liveness check failed")
                errors.append(
                    RouteExecutionError(
                        route_info=route,
                        reason="Health check failed",
                        error_detail=", ".join(failure_reasons),
                    )
                )

        return RouteExecutionResult(
            successes=successes,
            errors=errors,
        )
