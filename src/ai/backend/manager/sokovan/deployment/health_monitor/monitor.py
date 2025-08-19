"""Main health monitor for deployments."""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.repositories.deployment import DeploymentRepository

from ..exceptions import HealthCheckError
from ..replica_controller import ReplicaController
from ..types import ReadinessStatus, SyncStatus
from .readiness_checker import ReadinessChecker
from .sync_checker import SyncChecker
from .types import HealthStatus

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class HealthMonitorArgs:
    """Arguments for initializing HealthMonitor."""

    repository: DeploymentRepository
    config_provider: ManagerConfigProvider
    replica_controller: ReplicaController


class HealthMonitor:
    """Monitor health of deployments and their replicas."""

    _repository: DeploymentRepository
    _config_provider: ManagerConfigProvider
    _replica_controller: ReplicaController
    _sync_checker: SyncChecker
    _readiness_checker: ReadinessChecker

    def __init__(self, args: HealthMonitorArgs) -> None:
        self._repository = args.repository
        self._config_provider = args.config_provider
        self._replica_controller = args.replica_controller
        self._sync_checker = SyncChecker(args.repository)
        self._readiness_checker = ReadinessChecker(args.repository, args.config_provider)

    async def check_endpoint_health(
        self,
        endpoint_id: UUID,
    ) -> HealthStatus:
        """
        Check the health of an endpoint and its replicas.

        :param endpoint_id: ID of the endpoint to check
        :return: Health status of the endpoint
        """
        try:
            # Check route-session synchronization
            sync_result = await self._sync_checker.check_sync(endpoint_id)

            # Check readiness via appproxy
            readiness_result = await self._readiness_checker.check_readiness(endpoint_id)

            # Determine overall sync status
            if (
                sync_result.out_of_sync_routes
                or sync_result.orphaned_routes
                or sync_result.orphaned_sessions
            ):
                route_sync_status = SyncStatus.OUT_OF_SYNC
            else:
                route_sync_status = SyncStatus.SYNCED

            # Determine overall readiness status
            if readiness_result.not_ready_replicas or readiness_result.unknown_replicas:
                readiness_status = ReadinessStatus.NOT_READY
            else:
                readiness_status = ReadinessStatus.READY

            # Identify healthy and unhealthy replicas
            healthy_replicas = list(
                set(readiness_result.ready_replicas) & set(sync_result.synced_routes)
            )
            unhealthy_replicas = list(
                set(readiness_result.not_ready_replicas)
                | set(readiness_result.unknown_replicas)
                | set(sync_result.out_of_sync_routes)
                | set(sync_result.orphaned_routes)
            )

            # Build health status
            health_status = HealthStatus(
                endpoint_id=endpoint_id,
                route_sync_status=route_sync_status,
                readiness_status=readiness_status,
                healthy_replicas=healthy_replicas,
                unhealthy_replicas=unhealthy_replicas,
                timestamp=datetime.now(timezone.utc),
                details={
                    "synced_routes": str(len(sync_result.synced_routes)),
                    "out_of_sync_routes": str(len(sync_result.out_of_sync_routes)),
                    "orphaned_routes": str(len(sync_result.orphaned_routes)),
                    "orphaned_sessions": str(len(sync_result.orphaned_sessions)),
                    "ready_replicas": str(len(readiness_result.ready_replicas)),
                    "not_ready_replicas": str(len(readiness_result.not_ready_replicas)),
                },
            )

            log.debug(
                "Health check for endpoint {}: sync={}, readiness={}, healthy={}, unhealthy={}",
                endpoint_id,
                route_sync_status,
                readiness_status,
                len(healthy_replicas),
                len(unhealthy_replicas),
            )

            return health_status

        except Exception as e:
            log.error(
                "Failed to check health for endpoint {}: {}",
                endpoint_id,
                str(e),
            )
            raise HealthCheckError(f"Health check failed: {str(e)}") from e

    async def reconcile_unhealthy_replicas(
        self,
        health_status: HealthStatus,
    ) -> None:
        """
        Reconcile unhealthy replicas by replacing or recovering them.

        :param health_status: Health status containing unhealthy replicas
        """
        if not health_status.unhealthy_replicas:
            return

        log.info(
            "Reconciling {} unhealthy replicas for endpoint {}",
            len(health_status.unhealthy_replicas),
            health_status.endpoint_id,
        )

        try:
            # Get endpoint configuration
            endpoint_data = await self._repository.get_endpoint_data(health_status.endpoint_id)
            if not endpoint_data:
                log.error("Endpoint {} not found", health_status.endpoint_id)
                return

            # Destroy unhealthy replicas
            await self._replica_controller.destroy_replicas(
                health_status.endpoint_id,
                health_status.unhealthy_replicas,
            )

            # Create replacement replicas if needed
            current_healthy_count = len(health_status.healthy_replicas)
            desired_count = endpoint_data.desired_replicas
            replicas_to_create = max(0, desired_count - current_healthy_count)

            if replicas_to_create > 0:
                log.info(
                    "Creating {} replacement replicas for endpoint {}",
                    replicas_to_create,
                    health_status.endpoint_id,
                )

                # Get replica spec from endpoint configuration
                replica_spec = await self._repository.get_replica_spec(health_status.endpoint_id)
                if replica_spec:
                    await self._replica_controller.create_replicas(
                        replica_spec,
                        replicas_to_create,
                    )

        except Exception as e:
            log.error(
                "Failed to reconcile unhealthy replicas for endpoint {}: {}",
                health_status.endpoint_id,
                str(e),
            )

    async def check_all_endpoints(self) -> list[HealthStatus]:
        """
        Check health of all active endpoints.

        :return: List of health statuses for all endpoints
        """
        try:
            # Get all active endpoints
            endpoint_ids = await self._repository.get_active_endpoint_ids()

            health_statuses = []
            for endpoint_id in endpoint_ids:
                try:
                    health_status = await self.check_endpoint_health(endpoint_id)
                    health_statuses.append(health_status)
                except Exception as e:
                    log.error(
                        "Failed to check health for endpoint {}: {}",
                        endpoint_id,
                        str(e),
                    )

            return health_statuses

        except Exception as e:
            log.error("Failed to check all endpoints: {}", str(e))
            return []
