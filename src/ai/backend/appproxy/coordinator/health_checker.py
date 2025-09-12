from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Optional
from uuid import UUID

import aiohttp
import sqlalchemy as sa

from ai.backend.appproxy.common.exceptions import ObjectNotFound
from ai.backend.appproxy.common.types import AppMode, HealthCheckConfig, HealthCheckState, RouteInfo
from ai.backend.appproxy.coordinator.models.utils import (
    ExtendedAsyncSAEngine,
    execute_with_txn_retry,
)
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.model_serving.broadcast import (
    ModelServiceStatusBroadcastEvent,
)
from ai.backend.common.types import ModelServiceStatus, SessionId
from ai.backend.logging import BraceStyleAdapter

from .models import Circuit, Endpoint

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

    from .types import CircuitManager


log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class HealthCheckEngine:
    """
    Engine for performing HTTP health checks on model services
    """

    db: ExtendedAsyncSAEngine
    event_producer: EventProducer
    valkey_live: ValkeyLiveClient
    circuit_manager: "CircuitManager"
    valkey_schedule: ValkeyScheduleClient

    health_check_timer_interval: float

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        event_producer: EventProducer,
        valkey_live: ValkeyLiveClient,
        circuit_manager: "CircuitManager",
        health_check_timer_interval: float,
        valkey_schedule: ValkeyScheduleClient,
    ) -> None:
        self.db = db
        self.event_producer = event_producer
        self.valkey_live = valkey_live
        self.circuit_manager = circuit_manager
        self.health_check_timer_interval = health_check_timer_interval
        self.valkey_schedule = valkey_schedule
        self._session: Optional[aiohttp.ClientSession] = None

    async def start(self) -> None:
        """Initialize the health check engine"""
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=10,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        timeout = aiohttp.ClientTimeout(total=None, connect=5.0, sock_read=30.0)
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            skip_auto_headers={"User-Agent"},
            headers={"User-Agent": "Backend.AI-AppProxy-HealthChecker/1.0"},
        )

    async def stop(self) -> None:
        """Cleanup the health check engine"""
        if self._session:
            await self._session.close()
            self._session = None

    async def check_endpoint_health(self, endpoint: Endpoint) -> None:
        """
        Perform health check on individual containers for an endpoint via Circuit.route_info

        This method respects each endpoint's individual health check interval and only tracks
        individual route health status, not consolidated endpoint health.
        Health information is stored directly in the route_info column for each container.

        Args:
            endpoint: Endpoint model with health check configuration
        """
        if not endpoint.health_check_enabled or not endpoint.health_check_config:
            log.debug("Health check disabled for endpoint {}", endpoint.id)
            return

        config = endpoint.health_check_config

        # Validate configuration
        if not self._validate_config(config, endpoint.id):
            log.error("Invalid health check configuration for endpoint {}", endpoint.id)
            return

        # Check if enough time has elapsed since last health check based on endpoint's interval
        if not await self._should_check_endpoint_now(endpoint.id, config.interval):
            log.debug(
                "Skipping health check for endpoint {} - interval {:.1f}s not elapsed",
                endpoint.id,
                config.interval,
            )
            return

        # Get the circuit to access individual routes
        try:
            async with self.db.begin_readonly_session() as sess:
                circuit = await Circuit.find_by_endpoint(sess, endpoint.id, load_worker=True)
        except ObjectNotFound:
            log.warning("No circuit found for endpoint {}", endpoint.id)
            return
        except Exception as e:
            log.error("Failed to get circuit for endpoint {}: {}", endpoint.id, e)
            return

        # Only check health for circuits in INFERENCE mode
        if circuit.app_mode != AppMode.INFERENCE:
            log.debug(
                "Skipping health check for endpoint {} - circuit not in INFERENCE mode (current: {})",
                endpoint.id,
                circuit.app_mode,
            )
            return

        # Check health for each individual container in the circuit's route_info
        route_health_results: dict[UUID, tuple[Optional[ModelServiceStatus], float, int]] = {}
        status_changed = False
        for route in circuit.route_info:
            if not route.route_id:
                continue
            # Check individual container health via route_info
            is_healthy = await self._check_individual_container_health(route, config)

            if is_healthy:
                # Health check passed - reset consecutive failures and mark as healthy
                route_health_results[route.route_id] = (ModelServiceStatus.HEALTHY, time.time(), 0)
                log.debug(
                    "Route {} health check passed for endpoint {}", route.route_id, endpoint.id
                )
                if route.health_status != ModelServiceStatus.HEALTHY:
                    status_changed = True
            else:
                # Health check failed - increment consecutive failures
                new_consecutive_failures = route.consecutive_failures + 1
                new_status: Optional[ModelServiceStatus]

                # Only mark as UNHEALTHY if consecutive failures exceed max_retries
                if new_consecutive_failures > config.max_retries:
                    new_status = ModelServiceStatus.UNHEALTHY
                    log.warning(
                        "Route {} marked as UNHEALTHY after {} consecutive failures (max_retries: {})",
                        route.route_id,
                        new_consecutive_failures,
                        config.max_retries,
                    )
                else:
                    # Keep current status but increment failure count - don't change to UNHEALTHY yet
                    new_status = route.health_status
                    log.debug(
                        "Route {} health check failed ({}/{} failures) - keeping status as {}",
                        route.route_id,
                        new_consecutive_failures,
                        config.max_retries,
                        new_status or "Undetermined",
                    )
                if route.health_status != new_status:
                    status_changed = True
                route_health_results[route.route_id] = (
                    new_status,
                    time.time(),
                    new_consecutive_failures,
                )

                log.debug(
                    "Route {} health check failed for endpoint {} (failures: {}/{})",
                    route.route_id,
                    endpoint.id,
                    new_consecutive_failures,
                    config.max_retries,
                )

        # Update route health status in circuit
        if route_health_results:
            await self._update_route_health_in_circuit(circuit, route_health_results)
            log.debug(
                "Updated health status for {} routes in endpoint {}",
                len(route_health_results),
                endpoint.id,
            )

            # Update readiness status in Redis for manager to consume
            route_readiness: dict[str, bool] = {}
            for route_id, (status, _, _) in route_health_results.items():
                # Consider route ready if it's healthy
                route_readiness[str(route_id)] = status == ModelServiceStatus.HEALTHY

            try:
                await self.valkey_schedule.update_routes_readiness_batch(route_readiness)
                log.debug(
                    "Updated readiness status in Redis for {} routes",
                    len(route_readiness),
                )
                if status_changed:
                    await self.valkey_schedule.mark_route_needed("health_check")
            except Exception as e:
                log.error("Failed to update readiness status in Redis: {}", e)

        # Record that we performed a health check for this endpoint
        await self._record_endpoint_check_time(endpoint.id)

    async def _check_individual_container_health(
        self, route: RouteInfo, config: HealthCheckConfig
    ) -> bool:
        """
        Check health of an individual container using its route information

        Args:
            route: RouteInfo containing container connection details
            config: Health check configuration

        Returns:
            True if container is healthy, False otherwise
        """
        if not self._session:
            log.error("Health check session not initialized")
            return False

        # Construct health check URL directly to the container
        try:
            health_check_url = (
                f"http://{route.current_kernel_host}:{route.kernel_port}/{config.path.lstrip('/')}"
            )

            # Validate URL scheme
            if not health_check_url.startswith(("http://", "https://")):
                log.error(
                    "Health check only supports HTTP/HTTPS protocols, got: {} for route {}",
                    health_check_url,
                    route.route_id,
                )
                return False

        except Exception as e:
            log.error("Failed to construct health check URL for route {}: {}", route.route_id, e)
            return False

        # Perform the health check request
        try:
            timeout = aiohttp.ClientTimeout(total=config.max_wait_time)
            async with self._session.get(health_check_url, timeout=timeout) as response:
                if response.status == config.expected_status_code:
                    log.debug(
                        "Container health check passed for route {} at {} (status: {})",
                        route.route_id,
                        health_check_url,
                        response.status,
                    )
                    return True
                log.warning(
                    "Container health check failed for route {} at {} (expected: {}, got: {}, failures: {})",
                    route.route_id,
                    health_check_url,
                    config.expected_status_code,
                    response.status,
                    route.consecutive_failures + 1,
                )
                return False
        except asyncio.TimeoutError:
            log.warning(
                "Container health check timeout for route {} at {} (timeout: {}s, failures: {})",
                route.route_id,
                health_check_url,
                config.max_wait_time,
                route.consecutive_failures + 1,
            )
            return False
        except aiohttp.ClientError as e:
            log.warning(
                "Container health check connection error for route {} at {}: {} (failures: {})",
                route.route_id,
                health_check_url,
                e,
                route.consecutive_failures + 1,
            )
            return False
        except Exception as e:
            log.error(
                "Container health check unexpected error for route {} at {}: {} (failures: {})",
                route.route_id,
                health_check_url,
                e,
                route.consecutive_failures + 1,
            )
            return False

    async def _update_route_health_in_circuit(
        self,
        circuit: Circuit,
        route_health_results: dict[UUID, tuple[ModelServiceStatus | None, float, int]],
    ) -> None:
        """
        Update health status for routes in the circuit's route_info, persist to database,
        and propagate updated route information to AppProxy workers

        Args:
            circuit: Circuit containing the routes to update
            route_health_results: Dict mapping route_id to (status, last_check_time, consecutive_failures)
        """
        if not route_health_results:
            return

        try:
            # Store the original routes for comparison
            original_routes = circuit.route_info.copy()

            # Create a map of route_id -> old_health_status for transition detection
            old_health_status_map = {
                route.route_id: route.health_status for route in original_routes
            }

            async def _update(sess: SASession) -> None:
                # Re-fetch the circuit in this session to ensure we can update it
                circuit_in_session = await Circuit.get(
                    sess, circuit.id, load_worker=True, load_endpoint=True
                )

                updated_routes = 0
                health_transitions = []  # List of (session_id, old_status, new_status) tuples

                # Update health status for each route and detect transitions
                for route_id, (
                    status,
                    last_check_time,
                    consecutive_failures,
                ) in route_health_results.items():
                    # Get the old health status for this route
                    old_status = old_health_status_map.get(route_id)

                    updated = circuit_in_session.update_route_health_status(
                        route_id, status, last_check_time, consecutive_failures
                    )

                    if updated:
                        updated_routes += 1

                        # Find the corresponding route to get session_id
                        route_info = next(
                            (r for r in circuit_in_session.route_info if r.route_id == route_id),
                            None,
                        )

                        if route_info and old_status != status and status is not None:
                            # Health status transition detected
                            health_transitions.append((
                                route_info.session_id,
                                old_status,
                                status,
                            ))
                            log.info(
                                "Health status transition detected for session {} (route {}): {} -> {}",
                                route_info.session_id,
                                route_id,
                                old_status,
                                status,
                            )

                        log.debug(
                            "Updated container health status for route {} to {} in circuit {} (failures: {})",
                            route_id,
                            status,
                            circuit.id,
                            consecutive_failures,
                        )
                    else:
                        log.warning(
                            "Route {} not found in circuit {} for health status update",
                            route_id,
                            circuit.id,
                        )

                if updated_routes > 0:
                    log.debug(
                        "Persisted health status updates for {}/{} routes in circuit {}",
                        updated_routes,
                        len(route_health_results),
                        circuit.id,
                    )

                    # Publish health status transition events
                    await self.publish_health_transition_events(health_transitions)

                    # Propagate updated route information to AppProxy workers
                    await self.propagate_route_updates_to_workers(
                        circuit_in_session, original_routes
                    )
                else:
                    log.warning(
                        "No routes were updated in circuit {} - possibly stale route IDs",
                        circuit.id,
                    )

            async with self.db.connect() as db_conn:
                await execute_with_txn_retry(_update, self.db.begin_session, db_conn)
        except Exception as e:
            log.error("Failed to update route health status in circuit {}: {}", circuit.id, e)
            # Re-raise the exception to ensure health check failure is properly handled
            raise

    async def propagate_route_updates_to_workers(
        self, circuit: Circuit, old_routes: list[RouteInfo]
    ) -> None:
        """
        Propagate updated route information to AppProxy workers using RootContext.update_circuit_routes().

        This method ensures that traffic is distributed only to routes marked as healthy.
        If the endpoint is not equipped with health check, all routes are considered healthy.

        Args:
            circuit: Updated circuit with new route health information
            old_routes: Previous route information for comparison
        """
        try:
            # Get the endpoint to check if health checking is enabled
            endpoint = None
            if circuit.endpoint_id:
                try:
                    async with self.db.begin_readonly_session() as sess:
                        endpoint = await Endpoint.get(sess, circuit.endpoint_id)
                except Exception as e:
                    log.warning(
                        "Failed to get endpoint {} for circuit {}: {}",
                        circuit.endpoint_id,
                        circuit.id,
                        e,
                    )

            # Determine if health checking is enabled for this endpoint
            health_check_enabled = (
                endpoint is not None
                and endpoint.health_check_enabled
                and endpoint.health_check_config is not None
            )

            if health_check_enabled:
                # Health checking is enabled: use circuit.healthy_routes which filters by health status
                # This automatically considers routes with health_status=None or HEALTHY as healthy
                healthy_routes_count = len(circuit.healthy_routes)
                total_routes_count = len(circuit.route_info)

                log.debug(
                    "Health checking enabled for circuit {} - propagating {}/{} healthy routes to workers",
                    circuit.id,
                    healthy_routes_count,
                    total_routes_count,
                )
            else:
                # Health checking is disabled: all routes are considered healthy
                log.debug(
                    "Health checking disabled for circuit {} - propagating all {} routes to workers",
                    circuit.id,
                    len(circuit.route_info),
                )

            # Use RootContext.update_circuit_routes() to propagate route updates
            # This method automatically handles both Traefik and legacy modes
            # The circuit.healthy_routes property handles the health filtering logic
            await self.circuit_manager.update_circuit_routes(circuit, old_routes)

            log.debug(
                "Successfully propagated route updates for circuit {} to workers",
                circuit.id,
            )

        except Exception as e:
            log.error(
                "Failed to propagate route updates for circuit {} to workers: {}",
                circuit.id,
                e,
            )
            # Don't re-raise here as this is a propagation failure, not a health check failure
            # The health status updates were already persisted successfully

    async def _should_check_endpoint_now(self, endpoint_id: UUID, interval: float) -> bool:
        """
        Check if enough time has elapsed since the last health check for this endpoint

        Uses Valkey to store last check times with TTL to handle multi-process coordination

        Args:
            endpoint_id: Endpoint to check
            interval: Health check interval in seconds from endpoint configuration

        Returns:
            True if health check should be performed, False if interval hasn't elapsed
        """
        try:
            # Valkey key for storing last check time
            redis_key = f"endpoint.{endpoint_id}.last_health_check"

            # Get last check time from Valkey
            last_check_bytes = await self.valkey_live.get_live_data(redis_key)
            last_check_str = last_check_bytes.decode("utf-8") if last_check_bytes else None

            current_time = time.time()

            if last_check_str is None:
                # No previous check recorded, should check now
                log.debug("No previous health check recorded for endpoint {}", endpoint_id)
                return True

            try:
                last_check_time = float(last_check_str)
                time_since_last_check = current_time - last_check_time

                if time_since_last_check >= interval:
                    log.debug(
                        "Health check interval elapsed for endpoint {} ({:.1f}s >= {:.1f}s)",
                        endpoint_id,
                        time_since_last_check,
                        interval,
                    )
                    return True
                else:
                    log.debug(
                        "Health check interval not elapsed for endpoint {} ({:.1f}s < {:.1f}s)",
                        endpoint_id,
                        time_since_last_check,
                        interval,
                    )
                    return False

            except (ValueError, TypeError) as e:
                log.warning(
                    "Invalid last check time format for endpoint {}: {} - will check now",
                    endpoint_id,
                    e,
                )
                return True

        except Exception as e:
            log.error(
                "Failed to check last health check time for endpoint {} from Valkey: {} - will check now",
                endpoint_id,
                e,
            )
            # On Valkey errors, default to checking (fail-safe)
            return True

    async def _record_endpoint_check_time(self, endpoint_id: UUID) -> None:
        """
        Record the current time as the last health check time for this endpoint in Valkey

        Args:
            endpoint_id: Endpoint that was just checked
        """
        try:
            # Valkey key for storing last check time
            redis_key = f"endpoint.{endpoint_id}.last_health_check"
            current_time = time.time()

            # Store with TTL of 300 seconds (5 minutes) to handle cleanup
            # TTL should be longer than the longest expected health check interval
            ttl_seconds = 300

            await self.valkey_live.store_live_data(
                redis_key,
                str(current_time),
                ex=ttl_seconds,
            )

            log.debug(
                "Recorded health check time for endpoint {} in Valkey (TTL: {}s)",
                endpoint_id,
                ttl_seconds,
            )

        except Exception as e:
            log.error(
                "Failed to record health check time for endpoint {} in Valkey: {}",
                endpoint_id,
                e,
            )
            # Don't raise here as this is just tracking - health check was successful

    async def _perform_health_check_request(
        self,
        url: str,
        config: HealthCheckConfig,
        current_state: HealthCheckState,
    ) -> bool:
        """
        Perform the actual HTTP request for health checking

        Args:
            url: Full URL to check
            config: Health check configuration
            current_state: Current health check state

        Returns:
            True if healthy, False otherwise
        """
        if not self._session:
            log.error("Health check session not initialized")
            return False

        try:
            # Create timeout for this specific request
            timeout = aiohttp.ClientTimeout(total=config.max_wait_time)

            async with self._session.get(url, timeout=timeout) as response:
                # Check if status code matches expected
                if response.status == config.expected_status_code:
                    log.debug("Health check passed for {} (status: {})", url, response.status)
                    return True
                else:
                    log.warning(
                        "Health check failed for {} (expected: {}, got: {}, attempts: {})",
                        url,
                        config.expected_status_code,
                        response.status,
                        current_state.current_retry_count + 1,
                    )
                    return False

        except asyncio.TimeoutError:
            log.warning(
                "Health check timeout for {} (timeout: {}s, attempts: {})",
                url,
                config.max_wait_time,
                current_state.current_retry_count + 1,
            )
            return False
        except aiohttp.ClientError as e:
            log.warning(
                "Health check connection error for {}: {} (attempts: {})",
                url,
                e,
                current_state.current_retry_count + 1,
            )
            return False
        except Exception as e:
            log.error(
                "Health check unexpected error for {}: {} (attempts: {})",
                url,
                e,
                current_state.current_retry_count + 1,
            )
            return False

    async def check_all_routes(
        self,
    ) -> dict[UUID, tuple[ModelServiceStatus | None, float | None, int]]:
        """
        Check health of all routes across all endpoints with health checking enabled

        Returns:
            Dictionary mapping route_id to (health_status, last_check_time, consecutive_failures)
        """
        results: dict[UUID, tuple[ModelServiceStatus | None, float | None, int]] = {}

        async with self.db.begin_readonly_session() as sess:
            # Get all endpoints with health checking enabled
            endpoints = await Endpoint.list_health_check_enabled(sess)

            for endpoint in endpoints:
                if not endpoint.health_check_config:
                    continue

                # Find the circuit for this endpoint
                try:
                    circuit = await Circuit.find_by_endpoint(sess, endpoint.id)

                    # Only check health for circuits in INFERENCE mode
                    if circuit.app_mode != AppMode.INFERENCE:
                        log.debug(
                            "Skipping health check for circuit {} - not in INFERENCE mode (current: {})",
                            circuit.id,
                            circuit.app_mode,
                        )
                        continue

                    # Check health for each route in the circuit
                    for route in circuit.route_info:
                        if not route.route_id:
                            continue

                        status, check_time, failures = await self._check_route_health(
                            route, endpoint.health_check_config
                        )
                        results[route.route_id] = (status, check_time, failures)

                except Exception as e:
                    log.error("Failed to find circuit for endpoint {}: {}", endpoint.id, e)
                    continue

        return results

    async def _check_route_health(
        self, route: RouteInfo, config: HealthCheckConfig
    ) -> tuple[ModelServiceStatus | None, float | None, int]:
        """
        Perform health check on a single route

        Args:
            route: RouteInfo to check
            config: Health check configuration

        Returns:
            Tuple of (health_status, last_check_time, consecutive_failures)
        """
        if not self._session:
            log.error("Health check session not initialized")
            return ModelServiceStatus.UNHEALTHY, time.time(), route.consecutive_failures + 1

        # Construct health check URL
        try:
            health_check_url = (
                f"http://{route.current_kernel_host}:{route.kernel_port}/{config.path.lstrip('/')}"
            )

            # Validate URL scheme
            if not health_check_url.startswith(("http://", "https://")):
                log.error(
                    "Health check only supports HTTP/HTTPS protocols, got: {} for route {}",
                    health_check_url,
                    route.route_id,
                )
                return ModelServiceStatus.UNHEALTHY, time.time(), route.consecutive_failures + 1

        except Exception as e:
            log.error("Failed to construct health check URL for route {}: {}", route.route_id, e)
            return ModelServiceStatus.UNHEALTHY, time.time(), route.consecutive_failures + 1

        # Perform the health check request
        check_time = time.time()
        is_healthy = await self._perform_health_check_request_for_route(
            health_check_url, config, route
        )

        if is_healthy:
            log.debug("Route {} health check passed", route.route_id)
            return ModelServiceStatus.HEALTHY, check_time, 0  # Reset failures on success
        else:
            log.debug("Route {} health check failed", route.route_id)
            return ModelServiceStatus.UNHEALTHY, check_time, route.consecutive_failures + 1

    async def _perform_health_check_request_for_route(
        self,
        url: str,
        config: HealthCheckConfig,
        route: RouteInfo,
    ) -> bool:
        """
        Perform HTTP request for route health checking

        Args:
            url: Full URL to check
            config: Health check configuration
            route: RouteInfo being checked

        Returns:
            True if healthy, False otherwise
        """
        if not self._session:
            log.error("Health check session not initialized for route health check")
            return False

        try:
            timeout = aiohttp.ClientTimeout(total=config.max_wait_time)

            async with self._session.get(url, timeout=timeout) as response:
                if response.status == config.expected_status_code:
                    log.debug(
                        "Route {} health check passed (status: {})", route.route_id, response.status
                    )
                    return True
                else:
                    log.warning(
                        "Route {} health check failed (expected: {}, got: {}, failures: {})",
                        route.route_id,
                        config.expected_status_code,
                        response.status,
                        route.consecutive_failures + 1,
                    )
                    return False

        except asyncio.TimeoutError:
            log.warning(
                "Route {} health check timeout (timeout: {}s, failures: {})",
                route.route_id,
                config.max_wait_time,
                route.consecutive_failures + 1,
            )
            return False
        except aiohttp.ClientError as e:
            log.warning(
                "Route {} health check connection error: {} (failures: {})",
                route.route_id,
                e,
                route.consecutive_failures + 1,
            )
            return False
        except Exception as e:
            log.error(
                "Route {} health check unexpected error: {} (failures: {})",
                route.route_id,
                e,
                route.consecutive_failures + 1,
            )
            return False

    async def update_circuit_route_health(
        self, route_health_results: dict[UUID, tuple[ModelServiceStatus | None, float | None, int]]
    ) -> None:
        """
        Update route health status in circuit route_info JSON

        Args:
            route_health_results: Dict mapping route_id to (status, last_check_time, consecutive_failures)
        """
        if not route_health_results:
            return

        async with self.db.begin_session() as sess:
            # Group routes by endpoint_id
            endpoint_routes: dict[UUID, list[tuple[Circuit, UUID]]] = {}

            # Find circuits that contain these routes
            for route_id in route_health_results.keys():
                try:
                    # Find circuit containing this route
                    circuit_query = sa.select(Circuit).where(
                        Circuit.route_info.op("@>")([{"route_id": str(route_id)}])
                    )
                    circuit = await sess.scalar(circuit_query)

                    if circuit and circuit.endpoint_id:
                        if circuit.endpoint_id not in endpoint_routes:
                            endpoint_routes[circuit.endpoint_id] = []
                        endpoint_routes[circuit.endpoint_id].append((circuit, route_id))

                except Exception as e:
                    log.error("Failed to find circuit for route {}: {}", route_id, e)
                    continue

            # Update health status for each circuit
            for endpoint_id, circuit_routes in endpoint_routes.items():
                for circuit, route_id in circuit_routes:
                    if circuit is None:
                        continue

                    status, last_check_time, consecutive_failures = route_health_results[route_id]

                    # Update the route in circuit's route_info
                    updated = circuit.update_route_health_status(
                        route_id, status, last_check_time, consecutive_failures
                    )

                    if updated:
                        # Mark circuit as modified for database update
                        sess.add(circuit)
                        log.debug(
                            "Updated route {} health status to {} in circuit {}",
                            route_id,
                            status,
                            circuit.id,
                        )

            await sess.commit()

    async def check_all_endpoints(self) -> None:
        """
        Check health of all endpoints with health checking enabled, using safe concurrency control

        This method only performs individual route health checks, not endpoint-level aggregation.
        Health information is stored directly in each route's route_info column.
        """
        async with self.db.begin_readonly_session() as sess:
            endpoints = await Endpoint.list_health_check_enabled(sess)

        if not endpoints:
            log.debug("No endpoints with health checking enabled")
            return

        log.info("Starting health check cycle for {} endpoints", len(endpoints))

        # Calculate safe execution parameters
        timer_interval = self.health_check_timer_interval
        target_duration = timer_interval * 0.75  # 75% of timer interval for safety
        max_endpoint_time = 15.0  # Conservative estimate based on max_wait_time

        # Calculate safe concurrency limit to ensure completion within time limit
        min_concurrency = max(1, int(len(endpoints) * max_endpoint_time / target_duration))
        safe_concurrency = min(50, max(min_concurrency, 10))  # Between 10-50

        log.debug(
            "Health check timing: {} endpoints, {:.1f}s target duration, {} concurrent limit",
            len(endpoints),
            target_duration,
            safe_concurrency,
        )

        # Apply concurrency control with timeout protection
        try:
            await asyncio.wait_for(
                self._check_with_concurrency_limit(list(endpoints), safe_concurrency),
                timeout=target_duration,
            )
        except asyncio.TimeoutError:
            log.error(
                "Health check cycle exceeded {:.1f}s timeout",
                target_duration,
            )

    async def _check_with_concurrency_limit(
        self, endpoints: list["Endpoint"], concurrency_limit: int
    ) -> None:
        """
        Perform health checks with semaphore-based concurrency limiting

        Args:
            endpoints: List of endpoints to check
            concurrency_limit: Maximum number of concurrent health checks
        """
        semaphore = asyncio.Semaphore(concurrency_limit)

        async def _check_with_semaphore(endpoint: "Endpoint") -> tuple[UUID, bool]:
            """Wrapper to apply semaphore limiting to individual health checks"""
            async with semaphore:
                try:
                    await self.check_endpoint_health(endpoint)
                    return endpoint.id, True
                except Exception as e:
                    log.error("Health check failed for endpoint {}: {}", endpoint.id, e)
                    return endpoint.id, False

        # Create tasks with semaphore limiting
        tasks = [
            asyncio.create_task(_check_with_semaphore(endpoint), name=f"health-check-{endpoint.id}")
            for endpoint in endpoints
        ]

        # Wait for all checks to complete and collect metrics
        successful_checks = 0
        failed_checks = 0
        start_time = time.time()

        # Gather all results
        completed_results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in completed_results:
            if isinstance(result, (Exception, BaseException)):
                log.error("Unexpected error in health check task: {}", result)
                failed_checks += 1
            else:
                endpoint_id, success = result
                if success:
                    successful_checks += 1
                else:
                    failed_checks += 1

        # Log health check cycle summary
        cycle_duration = time.time() - start_time
        log.info(
            "Health check cycle completed in {:.2f}s: {} successful, {} failed (concurrency: {})",
            cycle_duration,
            successful_checks,
            failed_checks,
            concurrency_limit,
        )

    def _validate_config(self, config: HealthCheckConfig, endpoint_id: UUID) -> bool:
        """
        Validate health check configuration

        Args:
            config: Health check configuration to validate
            endpoint_id: Endpoint ID for logging

        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Validate path
            if not config.path:
                log.error("Health check path is empty for endpoint {}", endpoint_id)
                return False

            if not config.path.startswith("/"):
                log.error("Health check path must start with '/' for endpoint {}", endpoint_id)
                return False

            # Validate intervals and timeouts
            if config.interval <= 0:
                log.error("Health check interval must be positive for endpoint {}", endpoint_id)
                return False

            if config.max_wait_time <= 0:
                log.error("Health check timeout must be positive for endpoint {}", endpoint_id)
                return False

            if config.max_retries < 1:
                log.error(
                    "Health check max_retries must be at least 1 for endpoint {}", endpoint_id
                )
                return False

            # Validate status code range
            if not (100 <= config.expected_status_code <= 599):
                log.error(
                    "Health check expected_status_code must be between 100-599 for endpoint {}",
                    endpoint_id,
                )
                return False

            # Validate reasonable timeout vs interval
            if config.max_wait_time >= config.interval:
                log.warning(
                    "Health check timeout ({:.1f}s) is >= interval ({:.1f}s) for endpoint {}",
                    config.max_wait_time,
                    config.interval,
                    endpoint_id,
                )

            return True

        except Exception as e:
            log.error("Error validating health check config for endpoint {}: {}", endpoint_id, e)
            return False

    async def publish_health_transition_events(
        self, health_transitions: list[tuple[UUID, ModelServiceStatus | None, ModelServiceStatus]]
    ) -> None:
        """
        Publish ModelServiceStatusAnycastEvent and ModelServiceStatusBroadcastEvent for health status transitions

        Args:
            health_transitions: List of (session_id, old_status, new_status) tuples
        """
        if not health_transitions:
            return

        try:
            for session_id, old_status, new_status in health_transitions:
                # Only publish events for meaningful transitions (not None -> None)
                if old_status == new_status:
                    continue

                # Convert UUID to SessionId format
                session_id_obj = SessionId(session_id)

                log.info(
                    "Publishing health status transition events for session {}: {} -> {}",
                    session_id,
                    old_status,
                    new_status,
                )
                # Create broadcast event (MyPy expects additional fields, but runtime only needs session_id and new_status)
                broadcast_event = ModelServiceStatusBroadcastEvent(
                    session_id=session_id_obj,
                    new_status=new_status,
                )
                await self.event_producer.broadcast_event(broadcast_event)

                log.debug(
                    "Successfully published health status transition events for session {}",
                    session_id,
                )

        except Exception as e:
            log.error("Failed to publish health status transition events: {}", e)
            # Don't re-raise as this is optional functionality - health check itself was successful
