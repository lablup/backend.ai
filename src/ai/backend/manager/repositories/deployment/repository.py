"""Main deployment repository implementation."""

import logging
import uuid
from typing import Any, Optional

from pydantic import HttpUrl

from ai.backend.common.types import RuntimeVariant, SessionId
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.deployment.creator import DeploymentCreator
from ai.backend.manager.data.deployment.modifier import DeploymentModifier
from ai.backend.manager.data.deployment.types import DeploymentInfo
from ai.backend.manager.data.model_serving.types import EndpointLifecycle, RouteStatus
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.model_serving.types import (
    ModelServiceDefinition,
    RouteInfo,
    ServiceInfo,
)
from ai.backend.manager.sokovan.deployment.exceptions import (
    EndpointNotFound,
)

from .db_source import DeploymentDBSource
from .preparation_types import DeploymentPreparationData
from .storage_source import DeploymentStorageSource
from .types import RouteData

log = BraceStyleAdapter(logging.getLogger(__name__))


class DeploymentRepository:
    """Repository for deployment-related operations."""

    _db_source: DeploymentDBSource
    _storage_source: DeploymentStorageSource

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        storage_manager: StorageSessionManager,
    ) -> None:
        self._db_source = DeploymentDBSource(db)
        self._storage_source = DeploymentStorageSource(storage_manager)

    # Endpoint operations

    async def create_endpoint(
        self,
        creator: DeploymentCreator,
    ) -> DeploymentInfo:
        """Create a new endpoint and return DeploymentInfo."""
        return await self._db_source.create_endpoint(creator)

    async def get_endpoint_info(
        self,
        endpoint_id: uuid.UUID,
    ) -> DeploymentInfo:
        """Get endpoint information.

        Raises:
            EndpointNotFound: If the endpoint does not exist
        """
        return await self._db_source.get_endpoint(endpoint_id)

    async def get_all_active_endpoints(self) -> list[DeploymentInfo]:
        """Get all active endpoints for synchronization."""
        return await self._db_source.get_all_active_endpoints()

    async def update_endpoint_lifecycle(
        self,
        endpoint_id: uuid.UUID,
        lifecycle: EndpointLifecycle,
    ) -> bool:
        """Update endpoint lifecycle status."""
        return await self._db_source.update_endpoint_lifecycle(endpoint_id, lifecycle)

    async def update_endpoint_replicas_and_rebalance(
        self,
        endpoint_id: uuid.UUID,
        target_replicas: int,
    ) -> bool:
        """Update endpoint replicas and rebalance traffic ratios in a single transaction."""
        return await self._db_source.update_endpoint_replicas_and_rebalance(
            endpoint_id, target_replicas
        )

    async def update_endpoint_with_modifier(
        self,
        endpoint_id: uuid.UUID,
        modifier: DeploymentModifier,
    ) -> DeploymentInfo:
        """Update endpoint using a deployment modifier.

        Args:
            endpoint_id: ID of the endpoint to update
            modifier: Deployment modifier containing partial updates

        Returns:
            DeploymentInfo: Updated deployment information

        Raises:
            NoUpdatesToApply: If there are no updates to apply
            EndpointNotFound: If the endpoint does not exist
        """
        return await self._db_source.update_endpoint_with_modifier(endpoint_id, modifier)

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
        try:
            endpoint = await self._db_source.get_endpoint(endpoint_id)
            if not endpoint.network.url:
                return None
            return HttpUrl(endpoint.network.url)
        except EndpointNotFound:
            return None

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

    # Data fetching operations

    async def fetch_deployment_preparation_data(
        self,
        vfolder_id: uuid.UUID,
        domain_name: str,
        group_name: str,
        endpoint_name: str,
    ) -> DeploymentPreparationData:
        """Fetch all preparation data needed for deployment validation.

        Raises:
            ModelVFolderNotFound: If vfolder doesn't exist
            InvalidVFolderOwnership: If vfolder has project ownership
            GroupNotFound: If group doesn't exist
            DuplicateEndpointName: If endpoint name already exists
        """
        return await self._db_source.fetch_deployment_preparation_data(
            vfolder_id=vfolder_id,
            domain_name=domain_name,
            group_name=group_name,
            endpoint_name=endpoint_name,
        )

    async def fetch_service_definition(
        self,
        vfolder_id: uuid.UUID,
    ) -> Optional[ModelServiceDefinition]:
        """Fetch service definition from model vfolder.

        Args:
            vfolder_id: ID of the model vfolder

        Returns:
            Parsed service definition or None if not found
        """
        # Get vfolder info from DB
        vfolder_row = await self._db_source.get_vfolder_by_id(vfolder_id)
        if not vfolder_row:
            return None

        # Read service definition from storage
        return await self._storage_source.fetch_service_config(vfolder_row)

    async def check_model_definition_exists(
        self,
        vfolder_id: uuid.UUID,
        model_definition_path: str,
    ) -> bool:
        """Check if model definition file exists in vfolder.

        Args:
            vfolder_id: ID of the model vfolder
            model_definition_path: Path to model definition file

        Returns:
            True if file exists, False otherwise
        """
        # Get vfolder info from DB
        vfolder_row = await self._db_source.get_vfolder_by_id(vfolder_id)
        if not vfolder_row:
            return False

        # Check file existence in storage
        return await self._storage_source.check_model_definition_exists(
            vfolder_row,
            model_definition_path,
        )

    # Additional operations for model serving

    async def list_endpoints_by_owner(
        self,
        owner_id: uuid.UUID,
        name: Optional[str] = None,
    ) -> list[DeploymentInfo]:
        """List endpoints by owner with optional name filter."""
        return await self._db_source.list_endpoints_by_name(owner_id, name)

    async def get_service_info(
        self,
        endpoint_id: uuid.UUID,
    ) -> Optional[ServiceInfo]:
        """Get complete service information for an endpoint."""
        # Get endpoint and routes in a single database operation
        try:
            result = await self._db_source.get_endpoint_with_routes(endpoint_id)
        except EndpointNotFound:
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

    async def clear_endpoint_errors(
        self,
        endpoint_id: uuid.UUID,
    ) -> bool:
        """Clear error states for all routes of an endpoint."""
        routes = await self.get_routes_by_endpoint(endpoint_id)
        success = True
        for route in routes:
            if route.status == RouteStatus.FAILED_TO_START:
                result = await self.update_route_status(
                    route.route_id,
                    RouteStatus.UNHEALTHY,
                    error_data=None,
                )
                success = success and result
        return success
