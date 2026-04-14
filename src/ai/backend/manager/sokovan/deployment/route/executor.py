"""Route executor for handling route lifecycle operations."""

import logging
from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from ai.backend.common.clients.http_client.client_pool import ClientPool
from ai.backend.common.clients.valkey_client.valkey_schedule import (
    RouteHealthRecord,
    ValkeyScheduleClient,
)
from ai.backend.common.exception import BackendAIError
from ai.backend.common.service_discovery import ServiceDiscovery
from ai.backend.common.service_discovery.service_discovery import ModelServiceMetadata
from ai.backend.common.types import SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.deployment.types import DeploymentInfo, RouteHealthStatus
from ai.backend.manager.errors.deployment import (
    EndpointNotFound,
    RouteSessionNotFound,
    RouteSessionTerminated,
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

        # Phase 3: Populate replica connection info for routes missing it
        routes_missing_replica = [r for r in successes if not r.replica_host]
        if routes_missing_replica:
            with RouteRecorderContext.shared_phase("populate_replica_info"):
                with RouteRecorderContext.shared_step("fetch_kernel_connection_info"):
                    await self._populate_replica_info(routes_missing_replica)

        # Phase 4: Ensure RouteHealthRecords exist in Valkey for routes with replica info
        routes_with_replica = [r for r in successes if r.replica_host and r.replica_port]
        if routes_with_replica:
            await self._ensure_health_records(routes_with_replica)

        return RouteExecutionResult(
            successes=successes,
            errors=errors,
        )

    async def _populate_replica_info(self, routes: Sequence[RouteData]) -> None:
        """Fetch kernel host/port, store on route, and initialize RouteHealthRecords in Valkey."""
        session_ids = [r.session_id for r in routes if r.session_id]
        if not session_ids:
            return

        kernel_info = await self._deployment_repo.fetch_kernel_connection_info(session_ids)
        updates: dict[UUID, tuple[str, int]] = {}
        populated_routes: list[RouteData] = []
        for route in routes:
            if route.session_id and route.session_id in kernel_info:
                info = kernel_info[route.session_id]
                if info[0] and info[1]:
                    updates[route.route_id] = info
                    populated_routes.append(route)

        if updates:
            await self._deployment_repo.update_route_replica_info(updates)

        if populated_routes:
            await self._initialize_health_records(populated_routes, updates)

    async def _ensure_health_records(self, routes: Sequence[RouteData]) -> None:
        """Ensure RouteHealthRecords exist in Valkey for routes that already have replica info.

        Routes may already have replica_host/port in DB (set by a previous cycle or legacy code)
        but lack a RouteHealthRecord in Valkey. This method checks and initializes missing records.
        """
        route_id_strs = [str(r.route_id) for r in routes]
        existing = await self._valkey_schedule.get_route_health_records_batch(route_id_strs)
        missing = [r for r in routes if existing.get(str(r.route_id)) is None]
        if not missing:
            return
        log.warning(
            "RouteHealthRecord missing in Valkey for {} routes, re-initializing: {}",
            len(missing),
            [str(r.route_id)[:8] for r in missing],
        )
        replica_info = {
            r.route_id: (r.replica_host, r.replica_port)
            for r in missing
            if r.replica_host and r.replica_port
        }
        await self._initialize_health_records(missing, replica_info)

    async def _initialize_health_records(
        self,
        routes: Sequence[RouteData],
        replica_info: Mapping[UUID, tuple[str, int]],
    ) -> None:
        """Create RouteHealthRecords in Valkey for routes that just got replica info."""
        revision_ids = {r.revision_id for r in routes}
        health_configs = await self._deployment_repo.fetch_health_check_configs_by_revision_ids(
            revision_ids
        )
        redis_time = await self._valkey_schedule.get_redis_time()

        # Read existing running_at values that were set when routes transitioned to RUNNING
        # These may be in partial hashes (only running_at field), so read raw field directly
        running_at_map = await self._valkey_schedule.get_route_running_at_batch([
            str(r.route_id) for r in routes
        ])

        records: list[RouteHealthRecord] = []
        for route in routes:
            host, port = replica_info[route.route_id]
            health_config = health_configs.get(route.revision_id)

            health_path = health_config.path if health_config else "/"
            initial_delay = health_config.initial_delay if health_config else 60.0
            created_at = int(route.created_at.timestamp())

            # Use running_at from Valkey (set at RUNNING transition), fallback to redis_time
            route_id_str = str(route.route_id)
            running_at = running_at_map.get(route_id_str) or redis_time
            initial_delay_until = running_at + int(initial_delay)

            records.append(
                RouteHealthRecord(
                    route_id=route_id_str,
                    created_at=created_at,
                    initial_delay_until=initial_delay_until,
                    health_path=health_path,
                    inference_port=port,
                    replica_host=host,
                    running_at=running_at,
                )
            )

        if records:
            await self._valkey_schedule.initialize_route_health_records_batch(records)
            log.debug("Initialized {} RouteHealthRecords in Valkey", len(records))

    async def check_route_health(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """
        Check health status of routes using RouteHealthRecord from Valkey.

        Reads RouteHealthRecord and classifies based on computed healthy/stale:
        - HEALTHY: record.healthy is True
        - UNHEALTHY: record.healthy is False and not stale
        - DEGRADED: record is stale or missing

        The handler only reads and syncs to DB — all health check logic
        is in the RouteHealthObserver.

        Args:
            routes: Routes to check health for

        Returns:
            Result with successes (healthy), errors (unhealthy), stale (degraded)
        """
        # Phase 1: Load RouteHealthRecords
        with RouteRecorderContext.shared_phase("load_health_status"):
            with RouteRecorderContext.shared_step("query_health_check_results"):
                route_ids = [str(route.route_id) for route in routes]
                records = await self._valkey_schedule.get_route_health_records_batch(route_ids)
                current_time = await self._valkey_schedule.get_redis_time()

        successes: list[RouteData] = []
        errors: list[RouteExecutionError] = []
        stale: list[RouteData] = []

        # Phase 2: Classify health state (per-route)
        for route in routes:
            route_id_str = str(route.route_id)
            record = records.get(route_id_str)

            if record is None:
                # No RouteHealthRecord — not yet initialized
                stale.append(route)
                continue

            if record.last_check == 0:
                # Never checked yet — keep as NOT_CHECKED (stale)
                stale.append(route)
                continue

            if record.is_stale(current_time):
                stale.append(route)
                continue

            if record.healthy:
                successes.append(route)
            else:
                errors.append(
                    RouteExecutionError(
                        route_info=route,
                        reason="Route health check failed",
                        error_detail="RouteHealthRecord reports unhealthy",
                        error_code=None,
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
        endpoint_cleanup_config: dict[UUID, set[RouteHealthStatus]] = {}
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

    def _check_route_cleanup_eligibility(
        self,
        route: RouteData,
        endpoint_cleanup_config: Mapping[UUID, set[RouteHealthStatus]],
    ) -> bool:
        """Check if route should be cleaned up based on cleanup config."""
        pool = RouteRecorderContext.current_pool()
        recorder = pool.recorder(route.route_id)

        with recorder.phase("identify_cleanup_target"):
            with recorder.step("check_cleanup_eligibility"):
                cleanup_targets = endpoint_cleanup_config.get(route.endpoint_id, set())
                return route.health_status in cleanup_targets
