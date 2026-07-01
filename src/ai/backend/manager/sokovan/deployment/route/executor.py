"""Route executor for handling route lifecycle operations."""

import logging
from collections.abc import Mapping, Sequence
from typing import cast
from uuid import UUID

from ai.backend.common.clients.http_client.client_pool import ClientPool
from ai.backend.common.clients.valkey_client.valkey_schedule import (
    ReplicaProbeTarget,
    ValkeyScheduleClient,
)
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.request import (
    BulkRegisterRoutesRequest,
    BulkUnregisterRoutesRequest,
    BulkUpdateRoutesRequest,
)
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.types import (
    RegisterRoutesItem,
    RouteEntry,
    UnregisterRoutesItem,
    UpdateRoutesItem,
)
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.exception import BackendAIError
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.replica import ReplicaID
from ai.backend.common.service_discovery import ServiceDiscovery
from ai.backend.common.service_discovery.service_discovery import ModelServiceMetadata
from ai.backend.common.types import SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.appproxy.client import AppProxyClientPool
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    RouteHealthStatus,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.errors.deployment import (
    EndpointNotFound,
    RouteSessionNotFound,
    RouteSessionTerminated,
)
from ai.backend.manager.models.routing.conditions import RouteConditions
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.repositories.deployment.types import (
    RouteData,
    RouteSessionInfo,
    RouteSessionKernelInfo,
)
from ai.backend.manager.sokovan.deployment.deployment_draft_builder import (
    DeploymentSessionDraftBuilder,
)
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
        event_producer: EventProducer,
        appproxy_client_pool: AppProxyClientPool,
    ) -> None:
        self._deployment_repo = deployment_repo
        self._scheduling_controller = scheduling_controller
        self._config_provider = config_provider
        self._client_pool = client_pool
        self._valkey_schedule = valkey_schedule
        self._service_discovery = service_discovery
        self._event_producer = event_producer
        self._appproxy_client_pool = appproxy_client_pool

    async def provision_routes(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """Provision routes by creating sessions.

        Args:
            routes: Routes to provision

        Returns:
            Result containing successful and failed routes
        """
        # Phase 1: Load configuration
        with RouteRecorderContext.shared_phase("load_configuration"):
            with RouteRecorderContext.shared_step("load_deployment_config"):
                deployment_ids = {route.deployment_id for route in routes}
                deployments = await self._deployment_repo.get_deployments_by_ids(deployment_ids)
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

    async def drain_routes(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """Drain traffic for TERMINATING+DRAINING routes via AppProxy unregister.

        The synchronous unregister runs before any kernel teardown so no
        fresh request lands on a kernel that is about to die. Unregister
        failures are logged but do not hold the route in DRAINING — the
        AppProxy client's own retry policy already attempted, and the
        long-cycle ``AppProxySyncRouteHandler`` keeps state convergent
        for any leftover drift, so all routes advance to COOLING_DOWN.

        Args:
            routes: Routes in the DRAINING stage

        Returns:
            Result with every route as success (→ COOLING_DOWN)
        """
        if not routes:
            return RouteExecutionResult(successes=[], errors=[])

        with RouteRecorderContext.shared_phase("drain_appproxy_routes"):
            try:
                unregister_result = await self.unregister_routes_now(routes)
            except Exception:
                log.exception(
                    "Synchronous AppProxy unregister failed for {} draining routes",
                    len(routes),
                )
            else:
                if unregister_result.errors:
                    log.warning(
                        "AppProxy unregister: {} succeeded, {} failed (proceeding to cooling down)",
                        len(unregister_result.successes),
                        len(unregister_result.errors),
                    )
                    for error in unregister_result.errors:
                        log.warning(
                            "Failed to unregister route {} from AppProxy: {}",
                            error.route_info.route_id,
                            error.reason,
                        )
                else:
                    log.debug(
                        "Unregistered {} routes from AppProxy",
                        len(unregister_result.successes),
                    )

        return RouteExecutionResult(
            successes=list(routes),
            errors=[],
        )

    async def terminate_routes(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """Destroy sessions of COOLING_DOWN routes whose grace period elapsed.

        Traffic was already removed in the DRAINING stage; this stage only
        waits out each route's ``termination_grace_period`` (counted from
        the DRAINING → COOLING_DOWN transition) so in-flight requests can
        finish. Routes still inside their grace period are returned as
        ``stale`` (no transition) and re-checked on the next cycle.

        Args:
            routes: Routes in the COOLING_DOWN stage

        Returns:
            Result with terminated routes as successes and grace-waiting
            routes as stale
        """
        if not routes:
            return RouteExecutionResult(successes=[], errors=[])

        # Partition by termination grace (no phase - cannot fail)
        now = await self._deployment_repo.get_db_now()
        ready_routes: list[RouteData] = []
        waiting_routes: list[RouteData] = []
        for route in routes:
            if route.is_termination_grace_elapsed(now):
                ready_routes.append(route)
            else:
                waiting_routes.append(route)

        # Collect session IDs from grace-elapsed routes (no phase - cannot fail)
        target_session_ids: list[SessionId] = []
        for route in ready_routes:
            if not route.session_id:
                log.debug("Route {} has no session, skipping termination", route.route_id)
                continue
            target_session_ids.append(route.session_id)

        # Terminate sessions whose grace period elapsed
        with RouteRecorderContext.shared_phase("terminate_sessions"):
            with RouteRecorderContext.shared_step("mark_sessions_terminating"):
                await self._scheduling_controller.mark_sessions_for_termination(
                    target_session_ids, reason="ROUTE_TERMINATION"
                )

        return RouteExecutionResult(
            successes=ready_routes,
            errors=[],
            stale=waiting_routes,
        )

    async def check_starting_routes(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """Check if STARTING routes have their sessions ready.

        Queries session status and kernel connection info for routes whose sessions
        are being provisioned. Transitions routes to:
        - success (replica info ready): session is RUNNING with an inference port
        - error (session terminated): session reached a terminal status
        - skip (still starting): session is not yet RUNNING

        Args:
            routes: Routes in STARTING state to check

        Returns:
            Result containing routes that are ready (success) or failed (error)
        """
        if not routes:
            return RouteExecutionResult(successes=[], errors=[])

        route_ids = {route.route_id for route in routes}
        session_infos: dict[ReplicaID, RouteSessionInfo | None] = dict(
            await self._deployment_repo.fetch_route_session_kernel_infos(route_ids)
        )

        successes: list[RouteData] = []
        errors: list[RouteExecutionError] = []
        updates: dict[ReplicaID, RouteSessionKernelInfo] = {}

        for route in routes:
            replica_id = route.route_id
            info = session_infos.get(replica_id)

            if info is None:
                errors.append(
                    RouteExecutionError(
                        route_info=route,
                        reason="Session not found",
                        error_detail="Route has no session linked",
                        error_code=None,
                    )
                )
                continue

            if info.status.is_terminal():
                errors.append(
                    RouteExecutionError(
                        route_info=route,
                        reason="Session terminated",
                        error_detail=f"Session reached terminal status: {info.status}",
                        error_code=None,
                    )
                )
                continue

            if info.kernel is not None:
                updates[replica_id] = info.kernel
                successes.append(route)
            elif info.status == SessionStatus.RUNNING:
                errors.append(
                    RouteExecutionError(
                        route_info=route,
                        reason="Session running but no inference port available",
                        error_detail=f"Session status: {info.status}, kernel has no inference port",
                        error_code=None,
                    )
                )
            # else: session not yet RUNNING → skip (stay in STARTING)

        if updates:
            await self._deployment_repo.update_route_replica_info(updates)
            await self._register_route_probe_targets(successes, updates)

        return RouteExecutionResult(
            successes=successes,
            errors=errors,
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

    @staticmethod
    def _build_probe_target(route: RouteData) -> ReplicaProbeTarget | None:
        """Build a ReplicaProbeTarget from a route, or None if any required field is absent."""
        health_check = route.enabled_health_check
        if health_check is None or route.replica_host is None or route.replica_port is None:
            return None
        return ReplicaProbeTarget(
            replica_id=route.route_id,
            health_path=health_check.path,
            inference_port=route.replica_port,
            replica_host=route.replica_host,
        )

    async def _register_route_probe_targets(
        self,
        routes: Sequence[RouteData],
        replica_info: Mapping[ReplicaID, RouteSessionKernelInfo],
    ) -> None:
        """Register ReplicaProbeTargets in Valkey for routes that just got replica info."""
        targets: list[ReplicaProbeTarget] = [
            ReplicaProbeTarget(
                replica_id=route.route_id,
                health_path=health_check.path,
                inference_port=replica_info[route.route_id].replica_port,
                replica_host=replica_info[route.route_id].replica_host,
            )
            for route in routes
            if (health_check := route.enabled_health_check) is not None
        ]

        if targets:
            await self._valkey_schedule.register_route_probe_targets_batch(targets)
            log.debug("Registered {} ReplicaProbeTargets in Valkey", len(targets))

    async def sync_route_probe_targets(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """Sync ReplicaProbeTargets to Valkey for routes with known replica info.

        Handles two cases:
        - Valkey data lost (restart, eviction) → re-registers probe targets
        - TTL refresh for long-running routes

        Routes without health_check/replica_host/replica_port are skipped silently.
        """
        targets = [t for route in routes if (t := self._build_probe_target(route)) is not None]

        if targets:
            with RouteRecorderContext.shared_phase(
                "register_probe_targets",
                entity_ids={t.replica_id for t in targets},
            ):
                with RouteRecorderContext.shared_step("write_probe_targets"):
                    await self._valkey_schedule.register_route_probe_targets_batch(targets)
            log.debug("Synced {} ReplicaProbeTargets to Valkey", len(targets))

        return RouteExecutionResult(successes=[], errors=[])

    async def check_warming_up_health(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """Check health of PROVISIONING+WARMING_UP routes for initial activation.

        - success: health probe passed, or no health check configured → RUNNING+ACTIVE
        - failure: last_transition_at + initial_delay exceeded without a passing probe → TERMINATING
        - (no transition): still within initial_delay, or last_transition_at unknown → stay WARMING_UP
        """
        statuses = await self._valkey_schedule.get_route_health_statuses_batch([
            route.route_id for route in routes
        ])
        now = await self._deployment_repo.get_db_now()

        successes: list[RouteData] = []
        errors: list[RouteExecutionError] = []

        for route in routes:
            health_check = route.enabled_health_check
            if health_check is None:
                successes.append(route)
                continue

            status = statuses.get(route.route_id)
            if status is not None and status.healthy:
                successes.append(route)
                continue

            if route.last_transition_at is None:
                continue

            elapsed = (now - route.last_transition_at).total_seconds()
            if elapsed > health_check.initial_delay:
                errors.append(
                    RouteExecutionError(
                        route_info=route,
                        reason="Route warming-up timed out waiting for healthy probe",
                        error_detail=(
                            f"Elapsed {elapsed:.0f}s exceeds "
                            f"initial_delay {health_check.initial_delay}s"
                        ),
                    )
                )

        return RouteExecutionResult(successes=successes, errors=errors)

    async def check_route_health(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """
        Check health status of RUNNING routes and push newly-healthy ones to AppProxy.

        Routes with no active health check (absent or disabled) are skipped —
        their health is left unmanaged. For the rest, reads RouteHealthStatus
        from Valkey and classifies:
        - HEALTHY:   latest probe passed, or it failed but consecutive_failures
                     has not yet reached ``max_retries`` (still within retry budget)
        - UNHEALTHY: consecutive_failures reached ``max_retries``
        - DEGRADED:  status absent (key missing or TTL expired — no recent check)

        Routes whose pre-execute health_status was not HEALTHY but whose
        probe just passed are pushed to AppProxy synchronously so traffic
        can flow without waiting for the long-cycle fallback.

        Args:
            routes: Routes to check health for

        Returns:
            Result with successes (healthy), errors (unhealthy), stale (degraded)
        """
        # Phase 1: Load RouteHealthStatuses
        with RouteRecorderContext.shared_phase("load_health_status"):
            with RouteRecorderContext.shared_step("query_health_check_results"):
                statuses = await self._valkey_schedule.get_route_health_statuses_batch([
                    route.route_id for route in routes
                ])

        successes: list[RouteData] = []
        errors: list[RouteExecutionError] = []
        stale: list[RouteData] = []

        # Phase 2: Classify health state (per-route)
        for route in routes:
            health_check = route.enabled_health_check
            if health_check is None:
                # No active health check (absent or disabled) → leave health
                # unmanaged; do not transition this route.
                continue

            status = statuses.get(route.route_id)

            if status is None:
                # Key absent or TTL expired → DEGRADED
                stale.append(route)
                continue

            if status.healthy:
                successes.append(route)
            elif not health_check.is_retry_exhausted(status.consecutive_failures):
                # Probe failing but still within the retry budget → keep HEALTHY.
                successes.append(route)
            else:
                errors.append(
                    RouteExecutionError(
                        route_info=route,
                        reason="Route health check failed",
                        error_detail=(
                            f"RouteHealthStatus reports unhealthy after "
                            f"{status.consecutive_failures} consecutive failures"
                        ),
                        error_code=None,
                    )
                )

        # Phase 3: Push newly-healthy routes to AppProxy.
        # ``successes`` carries the pre-execute RouteData snapshot; routes
        # whose pre-state was not yet HEALTHY are first-time transitions.
        # Failures here are swallowed so the health-check tick never
        # raises out — the long-cycle fallback converges state.
        newly_healthy = [
            route for route in successes if route.health_status != RouteHealthStatus.HEALTHY
        ]
        if newly_healthy:
            with RouteRecorderContext.shared_phase("register_newly_healthy_routes"):
                try:
                    register_result = await self.register_routes_now(newly_healthy)
                except Exception:
                    log.exception(
                        "Synchronous AppProxy register failed for {} newly-healthy routes",
                        len(newly_healthy),
                    )
                else:
                    if register_result.errors:
                        log.warning(
                            "AppProxy register: {} succeeded, {} failed "
                            "(will be retried by long cycle)",
                            len(register_result.successes),
                            len(register_result.errors),
                        )
                        for error in register_result.errors:
                            log.warning(
                                "Failed to register route {} with AppProxy: {}",
                                error.route_info.route_id,
                                error.reason,
                            )
                    else:
                        log.debug(
                            "Registered {} newly-healthy routes with AppProxy",
                            len(register_result.successes),
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
                    "endpoint_id": str(data.deployment_id),
                    "deployment_id": str(data.deployment_id),
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

    async def sync_appproxy(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """Push the current ACTIVE routing tables for affected endpoints to AppProxy.

        Sync mirrors AppProxy to the manager's routing intent (traffic
        ACTIVE), not to live health. Evicting an UNHEALTHY backend from
        the pool is AppProxy's own health-check responsibility; on the
        manager side a confirmed-unhealthy route is removed via the
        route-eviction → terminate → unregister path per the scaling
        group's ``cleanup_target_statuses`` policy. Filtering by HEALTHY
        here would double-manage that and drop health-check-disabled
        (NOT_CHECKED) routes that should keep serving.

        Steps:
        1. Group the input routes by endpoint (the AppProxy contract is
           endpoint-scoped: one ``circuit.route_info`` per deployment).
        2. Resolve each endpoint's proxy target (wsproxy_addr / token)
           via the deployment repository in two batched calls.
        3. Re-read the authoritative RUNNING + ACTIVE route set per
           endpoint with a caller-composed ``BatchQuerier`` so the same
           plumbing works for sync, debug, and reporting paths.
        4. Group endpoints by proxy target and issue one
           ``bulk_update_routes`` HTTP call per target instead of one
           event per endpoint, which previously meant one DB connection
           per endpoint on the AppProxy side.
        5. Map per-entry response status back to the lifecycle handler's
           per-route success / error result so failed pushes are picked
           up by the next short cycle.
        """
        if not routes:
            return RouteExecutionResult(successes=[], errors=[])

        routes_by_endpoint: dict[DeploymentID, list[RouteData]] = {}
        for route in routes:
            routes_by_endpoint.setdefault(route.deployment_id, []).append(route)
        endpoint_ids = list(routes_by_endpoint.keys())

        successes: list[RouteData] = []
        errors: list[RouteExecutionError] = []

        deployments = await self._deployment_repo.get_deployments_by_ids(set(endpoint_ids))
        deployment_by_id = {dep.id: dep for dep in deployments}
        scaling_groups = {dep.metadata.resource_group for dep in deployments}
        proxy_targets = await self._deployment_repo.fetch_scaling_group_proxy_targets(
            scaling_groups
        )

        # Caller composes the filter so the conditions stay explicit at
        # the call site instead of hiding behind a flag-laden helper.
        route_querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[
                RouteConditions.by_endpoint_ids(endpoint_ids),
                RouteConditions.by_lifecycle_statuses([RouteStatus.RUNNING]),
                RouteConditions.by_traffic_status_equals(RouteTrafficStatus.ACTIVE),
            ],
        )
        connection_infos = await self._deployment_repo.fetch_route_connection_infos(
            route_querier=route_querier,
        )

        items_by_target: dict[tuple[str, str], list[UpdateRoutesItem]] = {}
        for endpoint_id in endpoint_ids:
            deployment = deployment_by_id.get(endpoint_id)
            if deployment is None:
                for route in routes_by_endpoint[endpoint_id]:
                    errors.append(
                        RouteExecutionError(
                            route_info=route,
                            reason="Deployment row not found for AppProxy sync",
                            error_detail=f"deployment {endpoint_id} disappeared between fetch and sync",
                            error_code=None,
                        )
                    )
                continue
            target = proxy_targets.get(deployment.metadata.resource_group)
            if target is None:
                for route in routes_by_endpoint[endpoint_id]:
                    errors.append(
                        RouteExecutionError(
                            route_info=route,
                            reason="No proxy target configured for scaling group",
                            error_detail=f"scaling group {deployment.metadata.resource_group}",
                            error_code=None,
                        )
                    )
                continue
            entries = connection_infos.get(endpoint_id, [])
            items_by_target.setdefault((target.addr, target.api_token), []).append(
                UpdateRoutesItem(
                    deployment_id=endpoint_id,
                    routes=[
                        RouteEntry(
                            session_id=entry.session_id,
                            route_id=entry.route_id,
                            kernel_host=entry.kernel_host,
                            kernel_port=entry.kernel_port,
                        )
                        for entry in entries
                    ],
                )
            )

        for (addr, token), items in items_by_target.items():
            client = self._appproxy_client_pool.load_client(addr, token)
            try:
                response = await client.bulk_update_routes(BulkUpdateRoutesRequest(endpoints=items))
            except Exception as exc:
                log.exception("AppProxy bulk routes-sync request failed for target {}", addr)
                error_code = _extract_error_code(exc)
                for item in items:
                    ep_id = DeploymentID(item.deployment_id)
                    for route in routes_by_endpoint.get(ep_id, []):
                        errors.append(
                            RouteExecutionError(
                                route_info=route,
                                reason="AppProxy bulk routes-sync request failed",
                                error_detail=str(exc),
                                error_code=error_code,
                            )
                        )
                continue

            for resp_item in response.endpoints:
                ep_id = DeploymentID(resp_item.deployment_id)
                ep_routes = routes_by_endpoint.get(ep_id, [])
                if resp_item.success:
                    successes.extend(ep_routes)
                else:
                    for route in ep_routes:
                        errors.append(
                            RouteExecutionError(
                                route_info=route,
                                reason="AppProxy bulk routes-sync entry failed",
                                error_detail=resp_item.error or "unknown",
                                error_code=None,
                            )
                        )

        return RouteExecutionResult(successes=successes, errors=errors)

    async def register_routes_now(
        self,
        routes: Sequence[RouteData],
    ) -> RouteExecutionResult:
        """Push the given routes to AppProxy as a delta-register payload.

        Synchronous counterpart to :meth:`sync_appproxy` for the
        push-side hot path (e.g. first-time HEALTHY transition):

        1. Group routes by endpoint and resolve each endpoint's proxy
           target via the deployment repository.
        2. Build a ``RegisterRoutesItem`` per endpoint using the
           replica host / port already attached to each ``RouteData``,
           skipping routes that have no replica info populated.
        3. Group endpoints by proxy target and issue one
           ``bulk_register_routes`` HTTP call per target.
        4. Map per-entry response status back to the executor's
           per-route success / error result so the caller can log
           failures (the long-cycle ``sync_appproxy`` will eventually
           converge).
        """
        if not routes:
            return RouteExecutionResult(successes=[], errors=[])

        routes_by_endpoint: dict[DeploymentID, list[RouteData]] = {}
        for route in routes:
            routes_by_endpoint.setdefault(route.deployment_id, []).append(route)
        endpoint_ids = list(routes_by_endpoint.keys())

        successes: list[RouteData] = []
        errors: list[RouteExecutionError] = []

        deployments = await self._deployment_repo.get_deployments_by_ids(set(endpoint_ids))
        deployment_by_id = {dep.id: dep for dep in deployments}
        scaling_groups = {dep.metadata.resource_group for dep in deployments}
        proxy_targets = await self._deployment_repo.fetch_scaling_group_proxy_targets(
            scaling_groups
        )

        # Routes that actually make it onto the wire per endpoint;
        # routes already added to ``errors`` (no replica info, missing
        # deployment, no proxy target) are excluded so the response
        # mapping does not accidentally double-count them as
        # successes.
        in_flight_by_endpoint: dict[DeploymentID, list[RouteData]] = {}
        items_by_target: dict[tuple[str, str], list[RegisterRoutesItem]] = {}
        for endpoint_id in endpoint_ids:
            deployment = deployment_by_id.get(endpoint_id)
            if deployment is None:
                for route in routes_by_endpoint[endpoint_id]:
                    errors.append(
                        RouteExecutionError(
                            route_info=route,
                            reason="Deployment row not found for AppProxy register",
                            error_detail=f"deployment {endpoint_id} disappeared between fetch and register",
                            error_code=None,
                        )
                    )
                continue
            target = proxy_targets.get(deployment.metadata.resource_group)
            if target is None:
                for route in routes_by_endpoint[endpoint_id]:
                    errors.append(
                        RouteExecutionError(
                            route_info=route,
                            reason="No proxy target configured for scaling group",
                            error_detail=f"scaling group {deployment.metadata.resource_group}",
                            error_code=None,
                        )
                    )
                continue

            entries: list[RouteEntry] = []
            in_flight_routes: list[RouteData] = []
            for route in routes_by_endpoint[endpoint_id]:
                if route.session_id is None or not route.replica_host or not route.replica_port:
                    errors.append(
                        RouteExecutionError(
                            route_info=route,
                            reason="Route has no replica connection info to register",
                            error_detail=(
                                f"session_id={route.session_id} replica_host={route.replica_host} "
                                f"replica_port={route.replica_port}"
                            ),
                            error_code=None,
                        )
                    )
                    continue
                entries.append(
                    RouteEntry(
                        session_id=route.session_id,
                        route_id=route.route_id,
                        kernel_host=route.replica_host,
                        kernel_port=route.replica_port,
                    )
                )
                in_flight_routes.append(route)
            if not entries:
                continue
            in_flight_by_endpoint[endpoint_id] = in_flight_routes
            items_by_target.setdefault((target.addr, target.api_token), []).append(
                RegisterRoutesItem(
                    deployment_id=endpoint_id,
                    routes=entries,
                )
            )

        for (addr, token), items in items_by_target.items():
            client = self._appproxy_client_pool.load_client(addr, token)
            try:
                response = await client.bulk_register_routes(
                    BulkRegisterRoutesRequest(endpoints=items)
                )
            except Exception as exc:
                log.exception("AppProxy bulk routes-register request failed for target {}", addr)
                error_code = _extract_error_code(exc)
                for item in items:
                    ep_id = DeploymentID(item.deployment_id)
                    for route in in_flight_by_endpoint.get(ep_id, []):
                        errors.append(
                            RouteExecutionError(
                                route_info=route,
                                reason="AppProxy bulk routes-register request failed",
                                error_detail=str(exc),
                                error_code=error_code,
                            )
                        )
                continue

            for resp_item in response.endpoints:
                ep_id = DeploymentID(resp_item.deployment_id)
                ep_routes = in_flight_by_endpoint.get(ep_id, [])
                if resp_item.success:
                    successes.extend(ep_routes)
                else:
                    for route in ep_routes:
                        errors.append(
                            RouteExecutionError(
                                route_info=route,
                                reason="AppProxy bulk routes-register entry failed",
                                error_detail=resp_item.error or "unknown",
                                error_code=None,
                            )
                        )

        return RouteExecutionResult(successes=successes, errors=errors)

    async def unregister_routes_now(
        self,
        routes: Sequence[RouteData],
    ) -> RouteExecutionResult:
        """Drop the given routes from AppProxy with a delta-unregister payload.

        Synchronous counterpart for the drain hot path:

        1. Group routes by endpoint and resolve each endpoint's proxy
           target via the deployment repository.
        2. Build an ``UnregisterRoutesItem`` per endpoint with just the
           ``route_id`` set.
        3. Group endpoints by proxy target and issue one
           ``bulk_unregister_routes`` HTTP call per target.
        4. Map per-entry response status back to the per-route
           success / error result so the caller can sequence
           termination after the unregister has succeeded.
        """
        if not routes:
            return RouteExecutionResult(successes=[], errors=[])

        routes_by_endpoint: dict[DeploymentID, list[RouteData]] = {}
        for route in routes:
            routes_by_endpoint.setdefault(route.deployment_id, []).append(route)
        endpoint_ids = list(routes_by_endpoint.keys())

        successes: list[RouteData] = []
        errors: list[RouteExecutionError] = []

        deployments = await self._deployment_repo.get_deployments_by_ids(set(endpoint_ids))
        deployment_by_id = {dep.id: dep for dep in deployments}
        scaling_groups = {dep.metadata.resource_group for dep in deployments}
        proxy_targets = await self._deployment_repo.fetch_scaling_group_proxy_targets(
            scaling_groups
        )

        items_by_target: dict[tuple[str, str], list[UnregisterRoutesItem]] = {}
        for endpoint_id in endpoint_ids:
            deployment = deployment_by_id.get(endpoint_id)
            if deployment is None:
                for route in routes_by_endpoint[endpoint_id]:
                    errors.append(
                        RouteExecutionError(
                            route_info=route,
                            reason="Deployment row not found for AppProxy unregister",
                            error_detail=f"deployment {endpoint_id} disappeared between fetch and unregister",
                            error_code=None,
                        )
                    )
                continue
            target = proxy_targets.get(deployment.metadata.resource_group)
            if target is None:
                for route in routes_by_endpoint[endpoint_id]:
                    errors.append(
                        RouteExecutionError(
                            route_info=route,
                            reason="No proxy target configured for scaling group",
                            error_detail=f"scaling group {deployment.metadata.resource_group}",
                            error_code=None,
                        )
                    )
                continue

            route_ids = cast(
                list[UUID], [route.route_id for route in routes_by_endpoint[endpoint_id]]
            )
            items_by_target.setdefault((target.addr, target.api_token), []).append(
                UnregisterRoutesItem(
                    deployment_id=endpoint_id,
                    route_ids=route_ids,
                )
            )

        for (addr, token), items in items_by_target.items():
            client = self._appproxy_client_pool.load_client(addr, token)
            try:
                response = await client.bulk_unregister_routes(
                    BulkUnregisterRoutesRequest(endpoints=items)
                )
            except Exception as exc:
                log.exception("AppProxy bulk routes-unregister request failed for target {}", addr)
                error_code = _extract_error_code(exc)
                for item in items:
                    ep_id = DeploymentID(item.deployment_id)
                    for route in routes_by_endpoint.get(ep_id, []):
                        errors.append(
                            RouteExecutionError(
                                route_info=route,
                                reason="AppProxy bulk routes-unregister request failed",
                                error_detail=str(exc),
                                error_code=error_code,
                            )
                        )
                continue

            for resp_item in response.endpoints:
                ep_id = DeploymentID(resp_item.deployment_id)
                ep_routes = routes_by_endpoint.get(ep_id, [])
                if resp_item.success:
                    successes.extend(ep_routes)
                else:
                    for route in ep_routes:
                        errors.append(
                            RouteExecutionError(
                                route_info=route,
                                reason="AppProxy bulk routes-unregister entry failed",
                                error_detail=resp_item.error or "unknown",
                                error_code=None,
                            )
                        )

        return RouteExecutionResult(successes=successes, errors=errors)

    async def cleanup_routes_by_config(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """
        Filter routes that should be terminated.

        A route is flagged when at least one of the following holds:

        - **Orphan revision**: ``route.revision_id`` matches neither the
          endpoint's ``current_revision_id`` nor its ``deploying_revision_id``.
          Catches leftovers from a preempted rollout.
        - **Health policy**: ``route.health_status`` is listed in the
          scaling group's ``cleanup_target_statuses`` (default: UNHEALTHY).

        Args:
            routes: Routes to check for cleanup eligibility

        Returns:
            Result with routes that should be terminated (successes)
        """
        if not routes:
            return RouteExecutionResult(successes=[], errors=[])

        # Phase 1: Load cleanup configuration
        with RouteRecorderContext.shared_phase("load_cleanup_config"):
            with RouteRecorderContext.shared_step("load_deployment_info"):
                deployment_ids = {route.deployment_id for route in routes}
                deployments = await self._deployment_repo.get_deployments_by_ids(deployment_ids)

            with RouteRecorderContext.shared_step("load_cleanup_policy"):
                scaling_group_names = list({
                    deployment.metadata.resource_group for deployment in deployments
                })
                cleanup_configs = await self._deployment_repo.get_scaling_group_cleanup_configs(
                    scaling_group_names
                )

        # Create mapping of deployment_id -> cleanup config (no phase - transformation only)
        deployment_cleanup_config: dict[DeploymentID, set[RouteHealthStatus]] = {}
        deployment_valid_revisions: dict[DeploymentID, set[DeploymentRevisionID]] = {}
        for deployment in deployments:
            config = cleanup_configs.get(deployment.metadata.resource_group, None)
            if config:
                deployment_cleanup_config[deployment.id] = set(config.cleanup_target_statuses)
            else:
                deployment_cleanup_config[deployment.id] = set()
            valid_revisions: set[DeploymentRevisionID] = set()
            if deployment.current_revision is not None:
                valid_revisions.add(deployment.current_revision.id)
            if deployment.deploying_revision is not None:
                valid_revisions.add(deployment.deploying_revision.id)
            deployment_valid_revisions[deployment.id] = valid_revisions

        successes: list[RouteData] = []

        # Phase 2: Identify cleanup targets (per-route)
        for route in routes:
            should_cleanup = self._check_route_cleanup_eligibility(
                route, deployment_cleanup_config, deployment_valid_revisions
            )
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
        deployment_map: Mapping[DeploymentID, DeploymentInfo],
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
                deployment = deployment_map.get(route.deployment_id)
                if deployment is None:
                    raise EndpointNotFound(
                        f"Deployment not found for deployment {route.deployment_id}"
                    )

                deployment_context = await self._deployment_repo.fetch_deployment_context(
                    deployment,
                    revision_id=route.revision_id,
                )
                target_revision = await self._deployment_repo.get_revision(route.revision_id)

                draft = DeploymentSessionDraftBuilder.build(
                    deployment_info=deployment,
                    context=deployment_context,
                    route_id=route.route_id,
                    target_revision=target_revision,
                )
                return await self._scheduling_controller.enqueue_session_from_draft(draft)

    def _verify_route_session_status(
        self,
        route: RouteData,
        session_statuses: Mapping[ReplicaID, SessionStatus | None],
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
        deployment_cleanup_config: Mapping[DeploymentID, set[RouteHealthStatus]],
        deployment_valid_revisions: Mapping[DeploymentID, set[DeploymentRevisionID]],
    ) -> bool:
        """Return True if the route should be evicted.

        Checked reasons (OR-combined):

        1. Orphan revision: ``route.revision_id`` is not the endpoint's
           current or deploying revision. The check is skipped when the
           endpoint has no revisions known yet (transient bootstrap state)
           to avoid wiping freshly-created routes.
        2. Scaling-group health policy: ``route.health_status`` is in
           ``cleanup_target_statuses`` for the route's scaling group.
        """
        pool = RouteRecorderContext.current_pool()
        recorder = pool.recorder(route.route_id)

        with recorder.phase("identify_cleanup_target"):
            with recorder.step("check_orphan_revision"):
                valid_revisions = deployment_valid_revisions.get(route.deployment_id, set())
                if valid_revisions and route.revision_id not in valid_revisions:
                    return True

            with recorder.step("check_cleanup_eligibility"):
                cleanup_targets = deployment_cleanup_config.get(route.deployment_id, set())
                return route.health_status in cleanup_targets
