"""Route executor for handling route lifecycle operations."""

import logging
from collections.abc import Mapping, Sequence
from typing import Any, Optional
from uuid import UUID

from ai.backend.common.clients.http_client.client_pool import ClientPool
from ai.backend.common.clients.valkey_client.valkey_schedule import (
    HealthCheckStatus,
    ValkeyScheduleClient,
)
from ai.backend.common.service_discovery import ServiceDiscovery
from ai.backend.common.service_discovery.service_discovery import ModelServiceMetadata
from ai.backend.common.types import SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.deployment.types import DeploymentInfo, RouteStatus
from ai.backend.manager.errors.deployment import (
    EndpointNotFound,
    RouteSessionNotFound,
    RouteSessionTerminated,
    RouteUnhealthy,
)
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.repositories.deployment.types import RouteData
from ai.backend.manager.repositories.scheduler.types.session_creation import SessionCreationSpec
from ai.backend.manager.sokovan.deployment.route.recorder.context import RouteRecorderContext
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
        service_discovery: ServiceDiscovery,
    ) -> None:
        self._deployment_repo = deployment_repo
        self._scheduling_controller = scheduling_controller
        self._config_provider = config_provider
        self._client_pool = client_pool
        self._valkey_schedule = valkey_schedule
        self._service_discovery = service_discovery

    async def provision_routes(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """Provision routes by creating sessions.

        Args:
            routes: Routes to provision

        Returns:
            Result containing successful and failed routes
        """
        # Phase 1: Load configuration
        with RouteRecorderContext.shared_phase("load_configuration"):
            with RouteRecorderContext.shared_step("load_endpoint_config"):
                endpoint_ids = {route.endpoint_id for route in routes}
                deployments = await self._deployment_repo.get_endpoints_by_ids(endpoint_ids)
                deployment_map = {dep.id: dep for dep in deployments}

        route_session_ids: dict[UUID, SessionId] = {}
        successes: list[RouteData] = []
        errors: list[RouteExecutionError] = []

        # Phase 2: Create sessions (per-route)
        for route in routes:
            try:
                session_id = await self._provision_route(route, deployment_map)
                if session_id is not None:
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

        # Phase 3: Link sessions to routes (only for successful routes)
        if route_session_ids:
            with RouteRecorderContext.shared_phase(
                "link_session_mapping", entity_ids=set(route_session_ids.keys())
            ):
                with RouteRecorderContext.shared_step("link_sessions_to_routes"):
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
        # Collect session IDs from routes (no phase - cannot fail)
        target_session_ids: list[SessionId] = []
        for route in routes:
            if not route.session_id:
                log.debug("Route {} has no session, skipping termination", route.route_id)
                continue
            target_session_ids.append(route.session_id)

        # Phase 1: Terminate sessions
        with RouteRecorderContext.shared_phase("terminate_sessions"):
            with RouteRecorderContext.shared_step("mark_sessions_terminating"):
                await self._scheduling_controller.mark_sessions_for_termination(
                    target_session_ids, reason="ROUTE_TERMINATION"
                )

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
        # Phase 1: Load status
        with RouteRecorderContext.shared_phase("load_status"):
            with RouteRecorderContext.shared_step("load_session_status"):
                route_ids = {route.route_id for route in routes}
                session_statuses = await self._deployment_repo.fetch_session_statuses_by_route_ids(
                    route_ids
                )

        successes: list[RouteData] = []
        errors: list[RouteExecutionError] = []

        # Phase 2: Verify status (per-route)
        for route in routes:
            try:
                self._verify_route_session_status(route, session_statuses)
                successes.append(route)
            except (RouteSessionNotFound, RouteSessionTerminated) as e:
                log.debug("Route {} session status check failed: {}", route.route_id, e)
                errors.append(
                    RouteExecutionError(
                        route_info=route,
                        reason=e.error_title,
                        error_detail=str(e),
                    )
                )

        return RouteExecutionResult(
            successes=successes,
            errors=errors,
        )

    async def check_route_health(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """
        Check health status of routes using Redis health data.

        Classifies routes into three states:
        - HEALTHY: readiness check passes and data is fresh (successes)
        - UNHEALTHY: readiness check fails (errors)
        - DEGRADED: health data is stale or missing (stale)

        Args:
            routes: Routes to check health for

        Returns:
            Result containing:
            - successes: healthy routes
            - errors: unhealthy routes
            - stale: degraded routes
        """
        # Phase 1: Load health status
        with RouteRecorderContext.shared_phase("load_health_status"):
            with RouteRecorderContext.shared_step("query_health_check_results"):
                # Get health status for all routes from Redis
                route_ids = [str(route.route_id) for route in routes]
                health_statuses = await self._valkey_schedule.check_route_health_status(route_ids)

        successes: list[RouteData] = []
        errors: list[RouteExecutionError] = []
        stale: list[RouteData] = []

        # Phase 2: Classify health state (per-route)
        for route in routes:
            try:
                is_healthy = self._classify_route_health(route, health_statuses)
                if is_healthy:
                    successes.append(route)
                else:
                    stale.append(route)
            except RouteUnhealthy as e:
                errors.append(
                    RouteExecutionError(
                        route_info=route,
                        reason=e.error_title,
                        error_detail=str(e),
                    )
                )

        return RouteExecutionResult(
            successes=successes,
            errors=errors,
            stale=stale,
        )

    async def sync_service_discovery(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """
        Sync healthy routes to service discovery backend for Prometheus scraping.

        For each route, extracts kernel host and port information and registers
        with service discovery so Prometheus can discover and scrape metrics endpoints.

        Args:
            routes: Healthy routes to sync

        Returns:
            Empty result (no status changes)
        """
        # Filter routes that have sessions (no phase - cannot fail)
        route_ids_with_session = {
            route.route_id for route in routes if route.session_id is not None
        }

        if not route_ids_with_session:
            log.debug("No routes with sessions to sync")
            return RouteExecutionResult(successes=[], errors=[])

        # Phase 1: Load service metadata
        with RouteRecorderContext.shared_phase("load_metadata"):
            with RouteRecorderContext.shared_step("load_service_metadata"):
                # Fetch service discovery information through repository
                route_discovery_data = (
                    await self._deployment_repo.fetch_route_service_discovery_info(
                        route_ids_with_session
                    )
                )

        # Construct ModelServiceMetadata for each route (no phase - transformation only)
        metadata_list: list[ModelServiceMetadata] = []
        for data in route_discovery_data:
            metadata = ModelServiceMetadata(
                route_id=data.route_id,
                model_service_name=data.endpoint_name,
                host=data.kernel_host,
                port=data.kernel_port,
                metrics_path="/metrics",
                labels={
                    "runtime_variant": data.runtime_variant,
                    "endpoint_id": str(data.endpoint_id),
                },
            )
            metadata_list.append(metadata)

        # Phase 2: Register for monitoring (only for routes with valid metadata)
        if metadata_list:
            with RouteRecorderContext.shared_phase(
                "register_monitoring", entity_ids={m.route_id for m in metadata_list}
            ):
                with RouteRecorderContext.shared_step("register_for_monitoring"):
                    await self._service_discovery.sync_model_service_routes(metadata_list)
            log.debug("Synced {} routes to service discovery", len(metadata_list))
        else:
            log.debug("No valid routes to sync to service discovery")

        return RouteExecutionResult(successes=[], errors=[])

    async def cleanup_routes_by_config(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """
        Filter routes for cleanup based on scaling group configuration.

        Checks if each route's status (unhealthy/degraded) is in the scaling group's
        cleanup_target_statuses. Routes that should be cleaned up are returned as successes,
        others are filtered out.

        Args:
            routes: Routes to check for cleanup eligibility

        Returns:
            Result with routes that should be terminated (successes)
        """
        if not routes:
            return RouteExecutionResult(successes=[], errors=[])

        # Phase 1: Load cleanup configuration
        with RouteRecorderContext.shared_phase("load_cleanup_config"):
            with RouteRecorderContext.shared_step("load_endpoint_info"):
                endpoint_ids = {route.endpoint_id for route in routes}
                endpoints = await self._deployment_repo.get_endpoints_by_ids(endpoint_ids)

            with RouteRecorderContext.shared_step("load_cleanup_policy"):
                scaling_group_names = list({
                    endpoint.metadata.resource_group for endpoint in endpoints
                })
                cleanup_configs = await self._deployment_repo.get_scaling_group_cleanup_configs(
                    scaling_group_names
                )

        # Create mapping of endpoint_id -> cleanup config (no phase - transformation only)
        endpoint_cleanup_config: dict[UUID, set[RouteStatus]] = {}
        for endpoint in endpoints:
            config = cleanup_configs.get(endpoint.metadata.resource_group, None)
            if config:
                endpoint_cleanup_config[endpoint.id] = set(config.cleanup_target_statuses)
            else:
                endpoint_cleanup_config[endpoint.id] = set()

        successes: list[RouteData] = []

        # Phase 2: Identify cleanup targets (per-route)
        for route in routes:
            should_cleanup = self._check_route_cleanup_eligibility(route, endpoint_cleanup_config)
            if should_cleanup:
                successes.append(route)
                log.info(
                    "Route {} marked for cleanup (status: {})",
                    route.route_id,
                    route.status.value,
                )
            else:
                log.trace(
                    "Route {} kept (status {} not in cleanup targets)",
                    route.route_id,
                    route.status.value,
                )

        return RouteExecutionResult(
            successes=successes,
        )

    # Private helper methods

    async def _provision_route(
        self,
        route: RouteData,
        deployment_map: Mapping[UUID, DeploymentInfo],
    ) -> Optional[SessionId]:
        """Provision a single route by creating a session.

        Returns:
            SessionId: newly created session ID
            None: route already has a session (skipped)
        """
        pool = RouteRecorderContext.current_pool()
        recorder = pool.recorder(route.route_id)

        with recorder.phase("create_session"):
            if route.session_id is not None:
                with recorder.step("skip_existing_session"):
                    log.debug("Route {} already has a session, skipping", route.route_id)
                return None

            with recorder.step("enqueue_session"):
                deployment = deployment_map.get(route.endpoint_id)
                if deployment is None:
                    raise EndpointNotFound(f"Deployment not found for endpoint {route.endpoint_id}")

                # Fetch deployment context with all necessary data
                deployment_context = await self._deployment_repo.fetch_deployment_context(
                    deployment
                )

                # Create session with full context
                return await self._scheduling_controller.enqueue_session(
                    SessionCreationSpec.from_deployment_info(
                        deployment_info=deployment,
                        context=deployment_context,
                        route_id=route.route_id,
                    )
                )

    def _verify_route_session_status(
        self,
        route: RouteData,
        session_statuses: Mapping[UUID, Any],
    ) -> None:
        """Verify that route's session is in a valid state."""
        pool = RouteRecorderContext.current_pool()
        recorder = pool.recorder(route.route_id)

        with recorder.phase("verify_session"):
            with recorder.step("check_session_exists"):
                session_status = session_statuses.get(route.route_id)
                if session_status is None:
                    raise RouteSessionNotFound("No session associated with route")

            with recorder.step("check_session_active"):
                if session_status.is_terminal():
                    raise RouteSessionTerminated(session_status.value)

    def _classify_route_health(
        self,
        route: RouteData,
        health_statuses: Mapping[str, Any],
    ) -> bool:
        """Classify route health status. Returns True for healthy, False for stale, raises for unhealthy."""
        pool = RouteRecorderContext.current_pool()
        recorder = pool.recorder(route.route_id)

        with recorder.phase("classify_health"):
            with recorder.step("determine_health_state"):
                route_id_str = str(route.route_id)
                health_status = health_statuses.get(route_id_str, None)

                if not health_status:
                    # No health data - Redis TTL expired, mark as stale
                    return False

                status = health_status.get_status()
                match status:
                    case HealthCheckStatus.HEALTHY:
                        return True
                    case HealthCheckStatus.STALE:
                        return False
                    case HealthCheckStatus.UNHEALTHY:
                        raise RouteUnhealthy("Route health check failed")

        return False  # Default to stale for unexpected cases

    def _check_route_cleanup_eligibility(
        self,
        route: RouteData,
        endpoint_cleanup_config: Mapping[UUID, set[RouteStatus]],
    ) -> bool:
        """Check if route should be cleaned up based on cleanup config."""
        pool = RouteRecorderContext.current_pool()
        recorder = pool.recorder(route.route_id)

        with recorder.phase("identify_cleanup_target"):
            with recorder.step("check_cleanup_eligibility"):
                cleanup_targets = endpoint_cleanup_config.get(route.endpoint_id, set())
                return route.status in cleanup_targets
