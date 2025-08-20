"""Main deployment repository implementation."""

import uuid
from typing import Any, Optional

from pydantic import HttpUrl

from ai.backend.common.types import RuntimeVariant, SessionId
from ai.backend.manager.data.model_serving.types import EndpointLifecycle, RouteStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.model_serving.types import RouteInfo, ServiceInfo

from .db_source import DeploymentDBSource
from .types import EndpointCreationArgs, EndpointData, RouteData


class DeploymentRepository:
    """Repository for deployment-related operations."""

    _db_source: DeploymentDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = DeploymentDBSource(db)

    # Endpoint operations

    async def create_endpoint(
        self,
        args: EndpointCreationArgs,
    ) -> uuid.UUID:
        """Create a new endpoint."""
        return await self._db_source.create_endpoint(args)

    async def get_endpoint_info(
        self,
        endpoint_id: uuid.UUID,
    ) -> Optional[EndpointData]:
        """Get endpoint information."""
        return await self._db_source.get_endpoint(endpoint_id)

    async def get_all_active_endpoints(self) -> list[EndpointData]:
        """Get all active endpoints for synchronization."""
        return await self._db_source.get_all_active_endpoints()

    async def update_endpoint_lifecycle(
        self,
        endpoint_id: uuid.UUID,
        lifecycle: EndpointLifecycle,
    ) -> bool:
        """Update endpoint lifecycle status."""
        return await self._db_source.update_endpoint_lifecycle(endpoint_id, lifecycle)

    async def update_endpoint_replicas(
        self,
        endpoint_id: uuid.UUID,
        desired_session_count: int,
    ) -> bool:
        """Update endpoint desired session count."""
        return await self._db_source.update_endpoint_replicas(endpoint_id, desired_session_count)

    async def update_endpoint_replicas_and_rebalance(
        self,
        endpoint_id: uuid.UUID,
        target_replicas: int,
    ) -> bool:
        """Update endpoint replicas and rebalance traffic ratios in a single transaction."""
        return await self._db_source.update_endpoint_replicas_and_rebalance(
            endpoint_id, target_replicas
        )

    async def delete_endpoint(
        self,
        endpoint_id: uuid.UUID,
    ) -> bool:
        """Delete an endpoint and all its routes."""
        return await self._db_source.delete_endpoint_with_routes(endpoint_id)

    async def get_service_endpoint(
        self,
        endpoint_id: uuid.UUID,
    ) -> Optional[HttpUrl]:
        """Get service endpoint URL."""
        endpoint = await self._db_source.get_endpoint(endpoint_id)
        if not endpoint or not endpoint.service_endpoint:
            return None
        return HttpUrl(endpoint.service_endpoint)

    # Route operations

    async def create_route(
        self,
        endpoint_id: uuid.UUID,
        traffic_ratio: float,
    ) -> uuid.UUID:
        """Create a new route for an endpoint."""
        return await self._db_source.create_route(endpoint_id, traffic_ratio)

    async def get_routes_by_endpoint(
        self,
        endpoint_id: uuid.UUID,
    ) -> list[RouteData]:
        """Get all routes for an endpoint."""
        return await self._db_source.get_routes_by_endpoint(endpoint_id)

    async def update_route_session(
        self,
        route_id: uuid.UUID,
        session_id: SessionId,
    ) -> bool:
        """Update route with session ID."""
        return await self._db_source.update_route_session(route_id, session_id)

    async def update_route_status(
        self,
        route_id: uuid.UUID,
        status: RouteStatus,
        error_data: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Update route status."""
        return await self._db_source.update_route_status(route_id, status, error_data)

    async def update_route_traffic_ratio(
        self,
        route_id: uuid.UUID,
        traffic_ratio: float,
    ) -> bool:
        """Update route traffic ratio."""
        return await self._db_source.update_route_traffic_ratio(route_id, traffic_ratio)

    async def delete_route(
        self,
        route_id: uuid.UUID,
    ) -> bool:
        """Delete a route."""
        return await self._db_source.delete_route(route_id)

    # delete_routes_by_endpoint is now handled internally by delete_endpoint

    # Auto-scaling operations are not immediately needed - removed for now

    async def get_service_info(
        self,
        endpoint_id: uuid.UUID,
    ) -> Optional[ServiceInfo]:
        """Get complete service information for an endpoint."""
        # Get endpoint and routes in a single database operation
        result = await self._db_source.get_endpoint_with_routes(endpoint_id)
        if not result:
            return None

        endpoint = result.endpoint
        routes = result.routes

        # Convert routes to RouteInfo
        active_routes = [
            RouteInfo(
                route_id=route.route_id,
                session_id=route.session_id,
                traffic_ratio=route.traffic_ratio,
            )
            for route in routes
            if route.session_id
        ]

        # Extract extra mounts from resource_opts
        extra_mounts = []
        if endpoint.resource_opts:
            for mount_data in endpoint.resource_opts.get("extra_mounts", []):
                if "vfolder_id" in mount_data:
                    extra_mounts.append(uuid.UUID(mount_data["vfolder_id"]))

        # Construct service endpoint URL if available
        service_endpoint = None
        if endpoint.service_endpoint:
            service_endpoint = HttpUrl(endpoint.service_endpoint)

        # Get model definition path from resource_opts
        model_definition_path = None
        if endpoint.resource_opts:
            model_definition_path = endpoint.resource_opts.get("startup_command")

        return ServiceInfo(
            endpoint_id=endpoint.endpoint_id,
            model_id=endpoint.model_id,
            extra_mounts=extra_mounts,
            name=endpoint.name,
            model_definition_path=model_definition_path,
            replicas=len(routes),  # Current replica count
            desired_session_count=endpoint.desired_session_count,
            active_routes=active_routes,
            service_endpoint=service_endpoint,
            is_public=endpoint.is_public,
            runtime_variant=RuntimeVariant(endpoint.runtime_variant),
        )
