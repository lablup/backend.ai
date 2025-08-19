"""Deployment repository for data access."""

import logging
from typing import Optional
from uuid import UUID

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.sokovan.deployment.replica_controller.types import ReplicaSpec

from .cache_source.cache_source import DeploymentCacheSource
from .db_source.db_source import DeploymentDBSource
from .types import (
    EndpointData,
    HealthData,
    ReplicaData,
    ReplicaUpdate,
    RouteData,
    ScalingData,
)
from .types.health import SessionAppproxyData

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class DeploymentRepository:
    """
    Repository that orchestrates between DB and cache sources for deployment operations.
    """

    _db_source: DeploymentDBSource
    _cache_source: DeploymentCacheSource
    _config_provider: ManagerConfigProvider

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        valkey_stat: ValkeyStatClient,
        config_provider: ManagerConfigProvider,
    ):
        self._db_source = DeploymentDBSource(db)
        self._cache_source = DeploymentCacheSource(valkey_stat)
        self._config_provider = config_provider

    # Endpoint operations

    async def get_endpoint_data(
        self,
        endpoint_id: UUID,
    ) -> Optional[EndpointData]:
        """
        Get endpoint data by ID.

        :param endpoint_id: ID of the endpoint
        :return: Endpoint data or None if not found
        """
        return await self._db_source.get_endpoint_data(endpoint_id)

    async def get_active_endpoint_ids(self) -> list[UUID]:
        """
        Get IDs of all active endpoints.

        :return: List of active endpoint IDs
        """
        return await self._db_source.get_active_endpoint_ids()

    async def create_endpoint(
        self,
        endpoint_data: EndpointData,
    ) -> EndpointData:
        """
        Create a new endpoint.

        :param endpoint_data: Endpoint data to create
        :return: Created endpoint data
        """
        return await self._db_source.create_endpoint(endpoint_data)

    async def update_endpoint_replicas(
        self,
        endpoint_id: UUID,
        desired_replicas: int,
    ) -> None:
        """
        Update desired replica count for an endpoint.

        :param endpoint_id: ID of the endpoint
        :param desired_replicas: New desired replica count
        """
        await self._db_source.update_endpoint_replicas(endpoint_id, desired_replicas)

    # Route operations

    async def get_endpoint_routes(
        self,
        endpoint_id: UUID,
    ) -> list[RouteData]:
        """
        Get all routes for an endpoint.

        :param endpoint_id: ID of the endpoint
        :return: List of route data
        """
        return await self._db_source.get_endpoint_routes(endpoint_id)

    async def create_route(
        self,
        endpoint_id: UUID,
        session_id: Optional[UUID] = None,
    ) -> UUID:
        """
        Create a new route for an endpoint.

        :param endpoint_id: ID of the endpoint
        :param session_id: Optional session ID
        :return: ID of the created route
        """
        return await self._db_source.create_route(endpoint_id, session_id)

    async def update_route_session(
        self,
        route_id: UUID,
        session_id: UUID,
    ) -> None:
        """
        Update session ID for a route.

        :param route_id: ID of the route
        :param session_id: New session ID
        """
        await self._db_source.update_route_session(route_id, session_id)

    async def delete_route(
        self,
        route_id: UUID,
    ) -> None:
        """
        Delete a route.

        :param route_id: ID of the route to delete
        """
        await self._db_source.delete_route(route_id)

    # Replica operations

    async def get_replica(
        self,
        replica_id: UUID,
    ) -> Optional[ReplicaData]:
        """
        Get replica data by ID.

        :param replica_id: ID of the replica
        :return: Replica data or None if not found
        """
        return await self._db_source.get_replica(replica_id)

    async def get_endpoint_replicas(
        self,
        endpoint_id: UUID,
    ) -> list[ReplicaData]:
        """
        Get all replicas for an endpoint.

        :param endpoint_id: ID of the endpoint
        :return: List of replica data
        """
        return await self._db_source.get_endpoint_replicas(endpoint_id)

    async def create_replica(
        self,
        endpoint_id: UUID,
        session_id: UUID,
        route_id: UUID,
    ) -> ReplicaData:
        """
        Create a new replica record.

        :param endpoint_id: ID of the endpoint
        :param session_id: ID of the session
        :param route_id: ID of the route
        :return: Created replica data
        """
        return await self._db_source.create_replica(endpoint_id, session_id, route_id)

    async def update_replica_status(
        self,
        replica_id: UUID,
        status: str,
    ) -> None:
        """
        Update status of a replica.

        :param replica_id: ID of the replica
        :param status: New status
        """
        await self._db_source.update_replica_status(replica_id, status)

    async def batch_update_replicas(
        self,
        updates: list[ReplicaUpdate],
    ) -> None:
        """
        Batch update multiple replicas.

        :param updates: List of replica updates
        """
        await self._db_source.batch_update_replicas(updates)

    # Session operations

    async def get_endpoint_sessions(
        self,
        endpoint_id: UUID,
    ) -> list:
        """
        Get all sessions for an endpoint.

        :param endpoint_id: ID of the endpoint
        :return: List of session data
        """
        return await self._db_source.get_endpoint_sessions(endpoint_id)

    async def get_session_appproxy_endpoint(
        self,
        session_id: UUID,
    ) -> Optional[SessionAppproxyData]:
        """
        Get appproxy endpoint for a session.

        :param session_id: ID of the session
        :return: Session appproxy data or None
        """
        return await self._db_source.get_session_appproxy_endpoint(session_id)

    # Scaling operations

    async def get_scaling_data(
        self,
        endpoint_id: UUID,
    ) -> Optional[ScalingData]:
        """
        Get all data required for scaling decisions.

        :param endpoint_id: ID of the endpoint
        :return: Scaling data or None if endpoint not found
        """
        # Get endpoint data
        endpoint = await self.get_endpoint_data(endpoint_id)
        if not endpoint:
            return None

        # Get routes
        routes = await self.get_endpoint_routes(endpoint_id)

        # Get metrics from cache
        metrics = await self._cache_source.get_endpoint_metrics(endpoint_id)

        # Get auto-scaling rules
        rules = await self._db_source.get_auto_scaling_rules(endpoint_id)

        # Get last scaling time from cache
        last_scaling_time = await self._cache_source.get_last_scaling_time(endpoint_id)

        return ScalingData(
            endpoint=endpoint,
            routes=routes,
            metrics=metrics,
            rules=rules,
            last_scaling_time=last_scaling_time,
        )

    async def update_last_scaling_time(
        self,
        endpoint_id: UUID,
        timestamp: str,
    ) -> None:
        """
        Update last scaling time for an endpoint.

        :param endpoint_id: ID of the endpoint
        :param timestamp: Scaling timestamp
        """
        await self._cache_source.set_last_scaling_time(endpoint_id, timestamp)

    # Health operations

    async def get_health_data(
        self,
        endpoint_id: UUID,
    ) -> Optional[HealthData]:
        """
        Get health data for an endpoint.

        :param endpoint_id: ID of the endpoint
        :return: Health data or None
        """
        return await self._db_source.get_health_data(endpoint_id)

    async def update_health_data(
        self,
        health_data: HealthData,
    ) -> None:
        """
        Update health data for an endpoint.

        :param health_data: Health data to update
        """
        await self._db_source.update_health_data(health_data)

    # Spec operations

    async def get_replica_spec(
        self,
        endpoint_id: UUID,
    ) -> Optional[ReplicaSpec]:
        """
        Get replica specification for an endpoint.

        :param endpoint_id: ID of the endpoint
        :return: Replica spec or None
        """
        endpoint_data = await self.get_endpoint_data(endpoint_id)
        if not endpoint_data:
            return None

        # Build replica spec from endpoint configuration
        from ai.backend.manager.sokovan.deployment.types import NetworkConfig

        network_config = NetworkConfig(
            endpoint_id=endpoint_id,
            port_mappings={"http": 8080, "https": 8443},
            subdomain=f"endpoint-{endpoint_id}",
        )

        return ReplicaSpec(
            endpoint_id=endpoint_id,
            image=endpoint_data.config.image,
            resources=endpoint_data.config.resources,
            network_config=network_config,
            mounts=endpoint_data.config.mounts,
            environ=endpoint_data.config.environ,
            scaling_group=endpoint_data.config.scaling_group,
            startup_command=endpoint_data.config.startup_command,
            bootstrap_script=endpoint_data.config.bootstrap_script,
        )
