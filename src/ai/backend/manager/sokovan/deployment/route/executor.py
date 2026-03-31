"""Route executor for handling route lifecycle operations."""

import asyncio
import logging
import time
from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

import aiohttp

from ai.backend.common.clients.http_client.client_pool import ClientKey, ClientPool
from ai.backend.common.clients.valkey_client.valkey_schedule import (
    HealthStatus,
    ValkeyScheduleClient,
)
from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.exception import BackendAIError
from ai.backend.common.service_discovery import ServiceDiscovery
from ai.backend.common.service_discovery.service_discovery import ModelServiceMetadata
from ai.backend.common.types import (
    MODEL_SERVICE_RUNTIME_PROFILES,
    SessionId,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.deployment.types import DeploymentInfo, RouteStatus
from ai.backend.manager.errors.deployment import (
    EndpointNotFound,
    RouteSessionNotFound,
    RouteSessionTerminated,
)
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.repositories.deployment.types import (
    RouteData,
    RouteServiceDiscoveryInfo,
)
from ai.backend.manager.repositories.scheduler.types.session_creation import SessionCreationSpec
from ai.backend.manager.sokovan.deployment.route.recorder.context import RouteRecorderContext
from ai.backend.manager.sokovan.deployment.route.types import (
    RouteExecutionError,
    RouteExecutionResult,
)
from ai.backend.manager.sokovan.scheduling_controller.scheduling_controller import (
    SchedulingController,
)

HEALTH_CHECK_SEMAPHORE_SIZE = 100
HEALTH_CHECK_CONNECT_TIMEOUT = 5.0

log = BraceStyleAdapter(logging.getLogger(__name__))


def _extract_error_code(exception: BaseException) -> str | None:
    """Extract error code from exception if available.

    Args:
        exception: The exception to extract error code from.

    Returns:
        Error code string if exception is BackendAIError, None otherwise.
    """
    if isinstance(exception, BackendAIError):
        return str(exception.error_code())
    return None


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
                log.warning("Failed to provision route {}: {}", route.route_id, e)
                errors.append(
                    RouteExecutionError(
                        route_info=route,
                        reason="Failed to provision",
                        error_detail=str(e),
                        error_code=_extract_error_code(e),
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
                        error_code=_extract_error_code(e),
                    )
                )

        return RouteExecutionResult(
            successes=successes,
            errors=errors,
        )

    async def check_route_health(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """
        Perform direct HTTP readiness checks on route endpoints.

        Classifies routes into three states:
        - HEALTHY: readiness check passes (successes)
        - UNHEALTHY: consecutive failures exceed max_retries (errors)
        - DEGRADED: check skipped, within initial_delay, or failures within threshold (stale)

        Args:
            routes: Routes to check health for

        Returns:
            Result containing successes, errors, and stale routes
        """
        # Phase 1: Load configuration and current state
        with RouteRecorderContext.shared_phase("load_health_config"):
            with RouteRecorderContext.shared_step("load_endpoint_config"):
                endpoint_ids = {route.endpoint_id for route in routes}
                deployments = await self._deployment_repo.get_endpoints_by_ids(endpoint_ids)
                deployment_map = {dep.id: dep for dep in deployments}

            with RouteRecorderContext.shared_step("load_service_discovery_info"):
                route_ids_set = {route.route_id for route in routes}
                discovery_infos = await self._deployment_repo.fetch_route_service_discovery_info(
                    route_ids_set
                )
                discovery_map: dict[UUID, RouteServiceDiscoveryInfo] = {
                    info.route_id: info for info in discovery_infos
                }

            with RouteRecorderContext.shared_step("load_current_health_status"):
                route_id_strs = [str(route.route_id) for route in routes]
                health_statuses = await self._valkey_schedule.check_route_health_status(
                    route_id_strs
                )

        # Phase 2: Perform HTTP health checks
        semaphore = asyncio.Semaphore(HEALTH_CHECK_SEMAPHORE_SIZE)
        now = time.time()
        check_results: dict[UUID, bool | None] = {}  # True=pass, False=fail, None=skip

        async def _check_one(route: RouteData) -> None:
            async with semaphore:
                result = await self._check_single_route_health(
                    route,
                    deployment_map,
                    discovery_map,
                    health_statuses,
                    now,
                )
                check_results[route.route_id] = result

        with RouteRecorderContext.shared_phase("perform_health_checks"):
            with RouteRecorderContext.shared_step("http_health_checks"):
                lock_lifetime = self._config_provider.config.manager.session_schedule_lock_lifetime
                cycle_timeout = lock_lifetime * 0.8
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*[_check_one(route) for route in routes]),
                        timeout=cycle_timeout,
                    )
                except TimeoutError:
                    log.warning(
                        "Health check cycle timed out after {:.1f}s, {}/{} routes checked",
                        cycle_timeout,
                        len(check_results),
                        len(routes),
                    )

        # Phase 3: Apply results to Redis and classify
        with RouteRecorderContext.shared_phase("apply_results"):
            with RouteRecorderContext.shared_step("update_redis_and_classify"):
                passed_ids = [str(rid) for rid, result in check_results.items() if result is True]
                failed_ids = [str(rid) for rid, result in check_results.items() if result is False]

                failure_counts = await self._valkey_schedule.apply_readiness_check_results(
                    successes=passed_ids,
                    failures=failed_ids,
                )

        # Phase 4: Build execution result
        successes: list[RouteData] = []
        errors: list[RouteExecutionError] = []
        stale: list[RouteData] = []

        for route in routes:
            result = check_results.get(route.route_id)
            if result is True:
                successes.append(route)
            elif result is False:
                route_id_str = str(route.route_id)
                new_failures = failure_counts.get(route_id_str, 0)
                config = self._resolve_health_check_config(
                    deployment_map.get(route.endpoint_id),
                    route,
                )
                max_retries = config.max_retries if config else 10
                if new_failures > max_retries:
                    errors.append(
                        RouteExecutionError(
                            route_info=route,
                            reason="Readiness check failed",
                            error_detail=(f"Consecutive failures: {new_failures} > {max_retries}"),
                            error_code=None,
                        )
                    )
                else:
                    stale.append(route)
            else:
                # None = skipped (initial_delay, interval, no config, no discovery)
                stale.append(route)

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
                    "session_owner": str(data.session_owner),
                    "project": str(data.project),
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
    ) -> SessionId | None:
        """Provision a single route by creating a session.

        Returns:
            SessionId: newly created session ID
            None: route already has a session, skipped
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

                deployment_context = await self._deployment_repo.fetch_deployment_context(
                    deployment,
                    revision_id=route.revision_id,
                )
                target_revision = deployment.resolve_revision_spec(route.revision_id)

                # Create session with full context
                return await self._scheduling_controller.enqueue_session(
                    SessionCreationSpec.from_deployment_info(
                        deployment_info=deployment,
                        context=deployment_context,
                        route_id=route.route_id,
                        target_revision=target_revision,
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

    async def _check_single_route_health(
        self,
        route: RouteData,
        deployment_map: Mapping[UUID, DeploymentInfo],
        discovery_map: Mapping[UUID, RouteServiceDiscoveryInfo],
        health_statuses: Mapping[str, HealthStatus | None],
        now: float,
    ) -> bool | None:
        """Check health of a single route. Returns True=pass, False=fail, None=skip."""
        deployment = deployment_map.get(route.endpoint_id)
        config = self._resolve_health_check_config(deployment, route)
        if config is None:
            return None

        discovery = discovery_map.get(route.route_id)
        if discovery is None:
            return None

        route_age = now - route.created_at.timestamp()
        if route_age < config.initial_delay:
            return None

        route_id_str = str(route.route_id)
        health_status = health_statuses.get(route_id_str)
        if health_status and health_status.last_readiness is not None:
            elapsed = now - health_status.last_readiness
            if elapsed < config.interval:
                return None

        return await self._perform_http_health_check(
            discovery.kernel_host,
            discovery.kernel_port,
            config,
        )

    def _resolve_health_check_config(
        self,
        deployment: DeploymentInfo | None,
        route: RouteData,
    ) -> ModelHealthCheck | None:
        """Extract health check config from deployment's current revision."""
        if deployment is None:
            return None

        revision_id = route.revision_id or deployment.current_revision_id
        if revision_id is None:
            return None

        try:
            revision = deployment.resolve_revision_spec(revision_id)
        except Exception:
            return None

        if revision.model_definition is not None:
            config = revision.model_definition.health_check_config()
            if config is not None:
                return config

        runtime_variant = revision.execution.runtime_variant
        profile = MODEL_SERVICE_RUNTIME_PROFILES.get(runtime_variant)
        if profile and profile.health_check_endpoint:
            return ModelHealthCheck(path=profile.health_check_endpoint)

        return None

    async def _perform_http_health_check(
        self,
        kernel_host: str,
        kernel_port: int,
        config: ModelHealthCheck,
    ) -> bool:
        """Perform a single HTTP health check request."""
        endpoint = f"http://{kernel_host}:{kernel_port}"
        path = config.path if config.path.startswith("/") else f"/{config.path}"
        timeout = aiohttp.ClientTimeout(
            total=config.max_wait_time,
            connect=HEALTH_CHECK_CONNECT_TIMEOUT,
        )
        try:
            session = self._client_pool.load_client_session(
                ClientKey(endpoint=endpoint, domain="health-check")
            )
            async with session.get(path, timeout=timeout) as response:
                return response.status == config.expected_status_code
        except TimeoutError:
            return False
        except aiohttp.ClientError:
            return False
        except Exception:
            log.warning(
                "Unexpected error during health check for {}:{}",
                kernel_host,
                kernel_port,
                exc_info=True,
            )
            return False

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
