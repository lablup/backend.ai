"""Deployment controller for managing model services and deployments."""

import logging
import uuid
from dataclasses import dataclass
from typing import Optional

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    KernelEnqueueingConfig,
    SessionTypes,
    VFolderMount,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.deployment.creator import DeploymentCreator
from ai.backend.manager.data.deployment.types import DeploymentInfo
from ai.backend.manager.models.endpoint import EndpointLifecycle
from ai.backend.manager.models.routing import RouteStatus
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.repositories.deployment.types import (
    RouteData,
)
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    SessionCreationSpec,
    UserScope,
)
from ai.backend.manager.services.model_serving.types import (
    ServiceInfo,
)
from ai.backend.manager.sokovan.deployment.validators.validator import DeploymentValidator

from ..scheduling_controller import SchedulingController
from .exceptions import EndpointNotFound, ServiceInfoRetrievalFailed

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class DeploymentControllerArgs:
    """Arguments for initializing DeploymentController."""

    scheduling_controller: SchedulingController
    deployment_validator: DeploymentValidator
    deployment_repository: DeploymentRepository
    config_provider: ManagerConfigProvider
    storage_manager: StorageSessionManager
    event_producer: EventProducer


class DeploymentController:
    """Controller for deployment and model service management."""

    _scheduling_controller: SchedulingController
    _deployment_validator: DeploymentValidator
    _deployment_repository: DeploymentRepository
    _config_provider: ManagerConfigProvider
    _storage_manager: StorageSessionManager
    _event_producer: EventProducer

    def __init__(self, args: DeploymentControllerArgs) -> None:
        """Initialize the deployment controller with required services."""
        self._scheduling_controller = args.scheduling_controller
        self._deployment_validator = args.deployment_validator
        self._deployment_repository = args.deployment_repository
        self._config_provider = args.config_provider
        self._storage_manager = args.storage_manager
        self._event_producer = args.event_producer

    async def create_deployment(
        self,
        spec: DeploymentCreator,
    ) -> DeploymentInfo:
        """
        Create a new deployment using the new DeploymentCreator specification.

        Returns:
            DeploymentInfo: Information about the created deployment
        """
        await self._deployment_validator.validate(spec)

        return await self._deployment_repository.create_endpoint(spec)

    async def delete_model_service(
        self,
        endpoint_id: uuid.UUID,
        force: bool = False,
    ) -> bool:
        """
        Delete a model service deployment.

        Args:
            endpoint_id: ID of the endpoint to delete
            force: Whether to force deletion

        Returns:
            bool: True if deletion was successful
        """
        log.info("Deleting model service with endpoint ID {}", endpoint_id)

        # Fetch all routes and their associated sessions
        routes = await self._deployment_repository.get_routes_by_endpoint(endpoint_id)

        session_ids = []
        for route in routes:
            if route.session_id:
                session_ids.append(route.session_id)

        # Mark sessions for termination
        if session_ids:
            termination_result = await self._scheduling_controller.mark_sessions_for_termination(
                session_ids,
                reason="MODEL_SERVICE_DELETION",
            )
            log.info(
                "Marked {} sessions for termination for endpoint {}",
                termination_result.processed_count(),
                endpoint_id,
            )

        # Delete endpoint (which also deletes all routes in a single transaction)
        await self._deployment_repository.delete_endpoint(endpoint_id)

        log.info("Successfully deleted model service endpoint {}", endpoint_id)
        return True

    async def scale_model_service(
        self,
        endpoint_id: uuid.UUID,
        target_replicas: int,
    ) -> ServiceInfo:
        """
        Scale a model service to the target number of replicas.

        Args:
            endpoint_id: ID of the endpoint to scale
            target_replicas: Target number of replicas

        Returns:
            ServiceInfo: Updated service information
        """
        log.info(
            "Scaling model service {} to {} replicas",
            endpoint_id,
            target_replicas,
        )

        # Get endpoint info and current routes
        endpoint_info = await self._deployment_repository.get_endpoint_info(endpoint_id)
        current_routes = await self._deployment_repository.get_routes_by_endpoint(endpoint_id)
        current_replicas = len(current_routes)

        if current_replicas == target_replicas:
            log.info("Model service {} already has {} replicas", endpoint_id, target_replicas)
        elif current_replicas < target_replicas:
            # Scale out - create new sessions
            await self._scale_out(
                endpoint_id,
                endpoint_info,
                current_replicas,
                target_replicas,
            )
        else:
            # Scale in - terminate excess sessions
            await self._scale_in(
                endpoint_id,
                current_routes,
                current_replicas,
                target_replicas,
            )

        # Update endpoint replica count and rebalance traffic ratios in a single transaction
        await self._deployment_repository.update_endpoint_replicas_and_rebalance(
            endpoint_id,
            target_replicas,
        )

        # Return complete service info
        service_info = await self._deployment_repository.get_service_info(endpoint_id)
        if not service_info:
            raise ServiceInfoRetrievalFailed(
                f"Could not retrieve service info for endpoint {endpoint_id}"
            )
        return service_info

    async def _scale_out(
        self,
        endpoint_id: uuid.UUID,
        endpoint_info: Optional[DeploymentInfo],
        current_replicas: int,
        target_replicas: int,
    ) -> None:
        """
        Scale out by creating new replicas.

        Args:
            endpoint_id: ID of the endpoint
            endpoint_info: Endpoint information
            current_replicas: Current number of replicas
            target_replicas: Target number of replicas
        """
        num_to_create = target_replicas - current_replicas
        log.info("Scaling out: creating {} new replicas", num_to_create)

        if not endpoint_info:
            raise EndpointNotFound(f"Endpoint {endpoint_id} not found")

        # Create new routes and sessions
        for i in range(num_to_create):
            # Create new route
            route_id = await self._deployment_repository.create_route(
                endpoint_id,
                traffic_ratio=1.0 / target_replicas,
            )

            # Create session spec from endpoint info
            session_spec = await self._prepare_session_spec_from_endpoint(
                endpoint_info,
                current_replicas + i,  # replica index
                endpoint_id,
                route_id,
            )

            # Enqueue session
            session_id = await self._scheduling_controller.enqueue_session(session_spec)

            # Update route with session ID
            await self._deployment_repository.update_route_session(
                route_id,
                session_id,
            )

            log.debug(
                "Created new replica {} for endpoint {} with session ID {}",
                current_replicas + i,
                endpoint_id,
                session_id,
            )

    async def _scale_in(
        self,
        endpoint_id: uuid.UUID,
        current_routes: list[RouteData],
        current_replicas: int,
        target_replicas: int,
    ) -> None:
        """
        Scale in by removing excess replicas.

        Args:
            endpoint_id: ID of the endpoint
            current_routes: Current routes
            current_replicas: Current number of replicas
            target_replicas: Target number of replicas
        """
        num_to_remove = current_replicas - target_replicas
        log.info("Scaling in: removing {} replicas", num_to_remove)

        # Select routes to remove (preferably inactive or errored ones first)
        routes_to_remove = current_routes[-num_to_remove:]  # Remove last ones for simplicity

        session_ids_to_terminate = []
        for route in routes_to_remove:
            if route.session_id:
                session_ids_to_terminate.append(route.session_id)
            # Delete the route
            await self._deployment_repository.delete_route(route.route_id)

        # Terminate sessions
        if session_ids_to_terminate:
            await self._scheduling_controller.mark_sessions_for_termination(
                session_ids_to_terminate,
                reason="MODEL_SERVICE_SCALE_IN",
            )

    async def _prepare_session_spec_from_endpoint(
        self,
        endpoint_info: DeploymentInfo,
        replica_idx: int,
        endpoint_id: uuid.UUID,
        route_id: uuid.UUID,
    ) -> SessionCreationSpec:
        """
        Prepare a session creation specification from endpoint information.

        Args:
            endpoint_info: Endpoint information from database
            replica_idx: Index of the replica
            endpoint_id: ID of the endpoint
            route_id: ID of the route

        Returns:
            SessionCreationSpec: Session specification ready for enqueuing
        """
        # Prepare environment variables
        # Get the first model revision (assuming single revision for now)
        model_revision = endpoint_info.model_revisions[0] if endpoint_info.model_revisions else None
        environ = model_revision.execution.environ or {} if model_revision else {}
        environ.update({
            "BACKEND_ENDPOINT_ID": str(endpoint_id),
            "BACKEND_ROUTE_ID": str(route_id),
            "BACKEND_MODEL_PATH": model_revision.mounts.model_definition_path
            if model_revision
            else "/models",
            "BACKEND_SERVICE_NAME": endpoint_info.metadata.name,
            "BACKEND_REPLICA_INDEX": str(replica_idx),
        })

        # For now, create empty mounts list - actual VFolderMount creation would need more context
        # This would need to be properly implemented based on actual VFolderMount structure
        mounts: list[VFolderMount] = []

        # Prepare internal data
        internal_data = {
            "model_service": True,
            "endpoint_id": str(endpoint_id),
            "route_id": str(route_id),
            "service_name": endpoint_info.metadata.name,
            "replica_index": replica_idx,
        }

        # Get resource and execution specs from model revision
        resource_spec = model_revision.resource_spec if model_revision else None
        execution_spec = model_revision.execution if model_revision else None

        # Create kernel specifications
        kernel_config = KernelEnqueueingConfig(
            image_ref=str(model_revision.image) if model_revision else "",  # type: ignore[typeddict-item]
            cluster_role="main",
            cluster_idx=0,
            local_rank=0,
            cluster_hostname=f"{endpoint_info.metadata.name}-{replica_idx}",
            creation_config={
                "architecture": "x86_64",  # TODO: Get from somewhere
                "resource_opts": resource_spec.resource_opts or {} if resource_spec else {},
                "resource_slots": resource_spec.resource_slots if resource_spec else {},
                "environ": environ,
            },
            bootstrap_script=execution_spec.bootstrap_script or "" if execution_spec else "",
            startup_command=execution_spec.startup_command if execution_spec else None,
            uid=None,
            main_gid=None,
            supplementary_gids=[],
        )

        # Prepare creation spec
        creation_spec = {
            "mounts": mounts,
            "environ": environ,
            "resources": resource_spec.resource_slots if resource_spec else {},
            "resource_opts": resource_spec.resource_opts or {} if resource_spec else {},
        }

        return SessionCreationSpec(
            session_creation_id=f"{endpoint_info.metadata.name}-{replica_idx:03d}-{uuid.uuid4().hex[:8]}",
            session_name=f"{endpoint_info.metadata.name}-{replica_idx:03d}",
            session_type=SessionTypes.INFERENCE,
            user_scope=UserScope(
                domain_name=endpoint_info.metadata.domain,
                group_id=endpoint_info.metadata.project,
                user_uuid=endpoint_info.metadata.session_owner,
                user_role="user",  # Default role for model service
            ),
            access_key=AccessKey(""),  # TODO: Get from somewhere
            scaling_group=endpoint_info.metadata.resource_group,
            cluster_size=resource_spec.cluster_size if resource_spec else 1,
            cluster_mode=ClusterMode(resource_spec.cluster_mode)
            if resource_spec
            else ClusterMode.SINGLE_NODE,
            priority=0,
            resource_policy={},  # Would need to be fetched from somewhere
            kernel_specs=[kernel_config],
            creation_spec=creation_spec,
            sudo_session_enabled=False,  # TODO: Get from somewhere
            callback_url=execution_spec.callback_url if execution_spec else None,
            internal_data=internal_data,
            session_tag=endpoint_info.metadata.tag,
            route_id=route_id,
        )

    async def sync_deployments(self) -> None:
        """
        Synchronize deployment state with actual session state.

        This method ensures consistency between the deployment
        metadata and the actual running sessions.

        Note: This should be called periodically by a global timer,
        similar to the scheduler's operation cycles.
        """
        log.info("Starting deployment synchronization")

        # Fetch all active deployments (endpoints)
        endpoints = await self._deployment_repository.get_all_active_endpoints()

        sync_stats = {
            "total_endpoints": len(endpoints),
            "healthy": 0,
            "degraded": 0,
            "failed": 0,
            "routes_updated": 0,
            "sessions_restarted": 0,
        }

        for endpoint in endpoints:
            try:
                # Get all routes for this endpoint
                routes = await self._deployment_repository.get_routes_by_endpoint(endpoint.id)

                healthy_routes = 0
                failed_routes = []

                for route in routes:
                    if route.session_id:
                        # For now, we rely on route status which should be updated by event handlers
                        # TODO: Implement session state checking via event system or other mechanism
                        if route.status == RouteStatus.HEALTHY:
                            healthy_routes += 1
                        elif route.status in [RouteStatus.FAILED_TO_START, RouteStatus.UNHEALTHY]:
                            failed_routes.append(route)
                    else:
                        # Route has no session - might need to create one
                        failed_routes.append(route)

                # Update endpoint status based on route health
                if healthy_routes == len(routes):
                    # All routes healthy
                    sync_stats["healthy"] += 1
                    await self._deployment_repository.update_endpoint_lifecycle(
                        endpoint.id,
                        EndpointLifecycle.CREATED,  # Use CREATED instead of READY
                    )
                elif healthy_routes > 0:
                    # Some routes healthy - degraded state
                    sync_stats["degraded"] += 1
                    await self._deployment_repository.update_endpoint_lifecycle(
                        endpoint.id,
                        EndpointLifecycle.CREATED,  # Keep as CREATED but track degraded status separately
                    )
                else:
                    # No healthy routes
                    sync_stats["failed"] += 1
                    await self._deployment_repository.update_endpoint_lifecycle(
                        endpoint.id,
                        EndpointLifecycle.DESTROYING,  # Mark for cleanup if all routes failed
                    )

                # Handle failed routes - mark for recovery in next cycle
                # Auto-scaling and recovery will be handled by periodic timer
                if failed_routes and endpoint.replica_spec.replica_count > healthy_routes:
                    log.debug(
                        "Endpoint {} has {} failed routes, will be handled in next auto-scaling cycle",
                        endpoint.id,
                        len(failed_routes),
                    )

            except Exception as e:
                log.error(
                    "Error synchronizing endpoint {}: {}",
                    endpoint.id,
                    e,
                )

        log.info(
            "Deployment synchronization completed: {} endpoints (healthy: {}, degraded: {}, "
            "failed: {}), {} routes updated, {} sessions restarted",
            sync_stats["total_endpoints"],
            sync_stats["healthy"],
            sync_stats["degraded"],
            sync_stats["failed"],
            sync_stats["routes_updated"],
            sync_stats["sessions_restarted"],
        )
