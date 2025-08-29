"""Deployment controller for managing model services and deployments."""

import logging
import uuid
from dataclasses import dataclass
from typing import Optional

import yarl


from ai.backend.common.docker import ImageRef
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import KernelEnqueueingConfig, SessionId, SessionTypes, VFolderMount
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.model_serving.creator import (
    ModelServiceCreator,
    RouteInfo,
    ServiceInfo,
)
from ai.backend.manager.models.endpoint import EndpointLifecycle
from ai.backend.manager.models.routing import RouteStatus
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.repositories.deployment.types import (
    EndpointCreationArgs,
    EndpointData,
    RouteData,
)
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    SessionCreationSpec,
    UserScope,
)

# from ai.backend.manager.services.model_serving.types import (
#     ModelServiceCreator,
#     RouteInfo,
#     ServiceInfo,
# )
from ..scheduling_controller import SchedulingController
from .exceptions import EndpointNotFound, ServiceInfoRetrievalFailed

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class DeploymentControllerArgs:
    """Arguments for initializing DeploymentController."""

    scheduling_controller: SchedulingController
    deployment_repository: DeploymentRepository
    config_provider: ManagerConfigProvider
    storage_manager: StorageSessionManager
    event_producer: EventProducer


class DeploymentController:
    """Controller for deployment and model service management."""

    _scheduling_controller: SchedulingController
    _deployment_repository: DeploymentRepository
    _config_provider: ManagerConfigProvider
    _storage_manager: StorageSessionManager
    _event_producer: EventProducer

    def __init__(self, args: DeploymentControllerArgs) -> None:
        """Initialize the deployment controller with required services."""
        self._scheduling_controller = args.scheduling_controller
        self._deployment_repository = args.deployment_repository
        self._config_provider = args.config_provider
        self._storage_manager = args.storage_manager
        self._event_producer = args.event_producer

    async def create_model_service(
        self,
        spec: ModelServiceCreator,
    ) -> ServiceInfo:
        """
        Create a new model service deployment.

        This method orchestrates the creation of a model service by:
        1. Validating the specification
        2. Creating endpoint and routing entries
        3. Preparing session specifications for each replica
        4. Enqueuing sessions through the SchedulingController

        Args:
            spec: Model service creation specification

        Returns:
            ServiceInfo: Information about the created model service
        """
        log.info(
            "Creating model service '{}' with {} replicas",
            spec.service_name,
            spec.replicas,
        )

        # Prepare resource_opts to store for future scaling operations
        endpoint_resource_opts = {
            "image_ref": spec.image,
            "architecture": spec.architecture,
            "access_key": spec.model_service_prepare_ctx.owner_access_key,
            "scaling_group": spec.config.scaling_group,
            "cluster_size": spec.cluster_size,
            "cluster_mode": spec.cluster_mode,
            "resources": spec.config.resources,
            "resource_opts": spec.config.resource_opts,
            "environ": spec.config.environ or {},
            "model_mount_destination": spec.config.model_mount_destination,
            "extra_mounts": [
                {
                    "vfolder_id": str(vfolder_id),
                    "mount_path": mount_option.mount_destination or f"/mnt/{vfolder_id}",
                    "permission": mount_option.permission.value
                    if mount_option.permission
                    else "rw",
                }
                for vfolder_id, mount_option in spec.config.extra_mounts.items()
            ],
            "sudo_session_enabled": spec.sudo_session_enabled,
            "bootstrap_script": spec.bootstrap_script,
            "startup_command": spec.startup_command or spec.config.model_definition_path,
            "callback_url": spec.callback_url,
            "tag": spec.tag,
        }

        # Create endpoint in database
        endpoint_args = EndpointCreationArgs.from_creator(spec)
        # endpoint_args = EndpointCreationArgs(
        #     name=spec.service_name,
        #     model_id=spec.model_service_prepare_ctx.model_id,
        #     owner_id=spec.model_service_prepare_ctx.owner_uuid,
        #     group_id=spec.model_service_prepare_ctx.group_id,
        #     domain_name=spec.domain_name,
        #     is_public=spec.open_to_public,
        #     runtime_variant=spec.runtime_variant,
        #     desired_session_count=spec.replicas,
        #     resource_opts=endpoint_resource_opts,
        #     scaling_group=spec.config.scaling_group,
        # )
        endpoint_id = await self._deployment_repository.create_endpoint(endpoint_args)

        # Create routing entries for replicas
        route_ids = []
        for _ in range(spec.replicas):
            route_id = await self._deployment_repository.create_route(
                endpoint_id,
                traffic_ratio=1.0 / spec.replicas,  # Equal distribution initially
            )
            route_ids.append(route_id)

        # Prepare session specifications for replicas
        session_ids: list[SessionId] = []
        active_routes: list[RouteInfo] = []

        for replica_idx in range(spec.replicas):
            session_spec = await self._prepare_session_spec_for_replica(
                spec,
                replica_idx,
                endpoint_id,
                route_ids[replica_idx],
            )

            # Enqueue session through SchedulingController
            session_id = await self._scheduling_controller.enqueue_session(session_spec)
            session_ids.append(session_id)

            # Update route with session ID
            await self._deployment_repository.update_route_session(
                route_ids[replica_idx],
                session_id,
            )

            active_routes.append(
                RouteInfo(
                    route_id=route_ids[replica_idx],
                    session_id=session_id,
                    traffic_ratio=1.0 / spec.replicas,
                )
            )

            log.debug(
                "Enqueued replica {} for service '{}' with session ID {}",
                replica_idx,
                spec.service_name,
                session_id,
            )

        # Fetch service endpoint URL if needed
        service_endpoint = await self._deployment_repository.get_service_endpoint(endpoint_id)

        # Return complete service information
        return ServiceInfo(
            endpoint_id=endpoint_id,
            model_id=spec.model_service_prepare_ctx.model_id,
            extra_mounts=[
                mount.vfid.folder_id for mount in spec.model_service_prepare_ctx.extra_mounts
            ],
            name=spec.service_name,
            model_definition_path=spec.config.model_definition_path,
            replicas=spec.replicas,
            desired_session_count=spec.replicas,
            active_routes=active_routes,
            service_endpoint=service_endpoint,
            is_public=spec.open_to_public,
            runtime_variant=spec.runtime_variant,
        )

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
        endpoint_info: Optional[EndpointData],
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
        endpoint_info: EndpointData,
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
        environ = (
            endpoint_info.resource_opts.get("environ", {}) if endpoint_info.resource_opts else {}
        )
        environ.update({
            "BACKEND_ENDPOINT_ID": str(endpoint_id),
            "BACKEND_ROUTE_ID": str(route_id),
            "BACKEND_MODEL_PATH": endpoint_info.resource_opts.get(
                "model_mount_destination", "/models"
            )
            if endpoint_info.resource_opts
            else "/models",
            "BACKEND_SERVICE_NAME": endpoint_info.name,
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
            "service_name": endpoint_info.name,
            "replica_index": replica_idx,
        }

        # Get other necessary fields from resource_opts
        resource_opts = endpoint_info.resource_opts or {}

        # Create kernel specifications from resource_opts
        kernel_config = KernelEnqueueingConfig(
            image_ref=resource_opts.get("image_ref", ""),  # type: ignore[typeddict-item]
            cluster_role="main",
            cluster_idx=0,
            local_rank=0,
            cluster_hostname=f"{endpoint_info.name}-{replica_idx}",
            creation_config={
                "architecture": resource_opts.get("architecture", "x86_64"),
                "resource_opts": resource_opts.get("resource_opts", {}),
                "resource_slots": resource_opts.get("resources", {}),
                "environ": environ,
            },
            bootstrap_script=resource_opts.get("bootstrap_script", ""),
            startup_command=resource_opts.get("startup_command"),
            uid=None,
            main_gid=None,
            supplementary_gids=[],
        )

        # Prepare creation spec
        creation_spec = {
            "mounts": mounts,
            "environ": environ,
            "resources": resource_opts.get("resources", {}),
            "resource_opts": resource_opts.get("resource_opts", {}),
        }

        return SessionCreationSpec(
            session_creation_id=f"{endpoint_info.name}-{replica_idx:03d}-{uuid.uuid4().hex[:8]}",
            session_name=f"{endpoint_info.name}-{replica_idx:03d}",
            session_type=SessionTypes.INFERENCE,
            user_scope=UserScope(
                domain_name=endpoint_info.domain_name,
                group_id=endpoint_info.group_id,
                user_uuid=endpoint_info.owner_id,
                user_role="user",  # Default role for model service
            ),
            access_key=resource_opts.get("access_key", ""),
            scaling_group=resource_opts.get("scaling_group", "default"),
            cluster_size=resource_opts.get("cluster_size", 1),
            cluster_mode=resource_opts.get("cluster_mode", "single-node"),
            priority=0,
            resource_policy={},  # Would need to be fetched from somewhere
            kernel_specs=[kernel_config],
            creation_spec=creation_spec,
            sudo_session_enabled=resource_opts.get("sudo_session_enabled", False),
            callback_url=yarl.URL(str(resource_opts.get("callback_url")))
            if resource_opts.get("callback_url")
            else None,
            internal_data=internal_data,
            session_tag=resource_opts.get("tag"),
            route_id=route_id,
        )

    async def _prepare_session_spec_for_replica(
        self,
        model_spec: ModelServiceCreator,
        replica_idx: int,
        endpoint_id: uuid.UUID,
        route_id: uuid.UUID,
    ) -> SessionCreationSpec:
        """
        Prepare a session creation specification for a model service replica.

        Args:
            model_spec: Model service specification
            replica_idx: Index of the replica
            endpoint_id: ID of the endpoint
            route_id: ID of the route

        Returns:
            SessionCreationSpec: Session specification ready for enqueuing
        """
        # Convert ModelServiceCreator to SessionCreationSpec

        # Convert extra mounts to VFolderMount list
        # VFolderMount expects different fields based on common/types.py
        # For now, we'll use the model_service_prepare_ctx.extra_mounts which already has VFolderMount objects
        mounts: list[VFolderMount] = list(model_spec.model_service_prepare_ctx.extra_mounts)

        # Prepare environment variables
        environ = model_spec.config.environ or {}
        # Add model service specific environment variables
        environ.update({
            "BACKEND_ENDPOINT_ID": str(endpoint_id),
            "BACKEND_ROUTE_ID": str(route_id),
            "BACKEND_MODEL_PATH": model_spec.config.model_mount_destination,
            "BACKEND_SERVICE_NAME": model_spec.service_name,
            "BACKEND_REPLICA_INDEX": str(replica_idx),
        })

        # Resolve group ID properly
        try:
            group_id = uuid.UUID(model_spec.group_name)
        except ValueError:
            # If group_name is not a UUID, use the group_id from prepare context
            group_id = model_spec.model_service_prepare_ctx.group_id

        # Prepare internal data for session
        internal_data = {
            "model_service": True,
            "endpoint_id": str(endpoint_id),
            "route_id": str(route_id),
            "service_name": model_spec.service_name,
            "replica_index": replica_idx,
        }

        image_ref = ImageRef.from_image_str(model_spec.image, None, "", architecture=model_spec.architecture)
        # Create kernel specifications based on the model spec
        kernel_config = KernelEnqueueingConfig(
            image_ref=image_ref,
            cluster_role="main",
            cluster_idx=0,
            local_rank=0,
            cluster_hostname=f"{model_spec.service_name}-{replica_idx}",
            creation_config={
                "architecture": model_spec.architecture,
                "resource_opts": model_spec.config.resource_opts,
                "resource_slots": model_spec.config.resources,
                "environ": environ,
            },
            bootstrap_script=model_spec.bootstrap_script or "",
            startup_command=model_spec.startup_command or model_spec.config.model_definition_path,
            uid=None,
            main_gid=None,
            supplementary_gids=[],
        )

        # Prepare creation spec with proper field structure
        creation_spec = {
            "mounts": mounts,
            "environ": environ,
            "resources": model_spec.config.resources,
            "resource_opts": model_spec.config.resource_opts,
        }

        return SessionCreationSpec(
            session_creation_id=f"{model_spec.service_name}-{replica_idx:03d}-{uuid.uuid4().hex[:8]}",
            session_name=f"{model_spec.service_name}-{replica_idx:03d}",
            session_type=SessionTypes.INFERENCE,
            user_scope=UserScope(
                domain_name=model_spec.domain_name,
                group_id=group_id,
                user_uuid=model_spec.model_service_prepare_ctx.owner_uuid,
                user_role="user",  # Default role for model service
            ),
            access_key=model_spec.model_service_prepare_ctx.owner_access_key,
            scaling_group=model_spec.config.scaling_group,
            cluster_size=model_spec.cluster_size,
            cluster_mode=model_spec.cluster_mode,
            priority=0,
            resource_policy=model_spec.model_service_prepare_ctx.resource_policy,
            kernel_specs=[kernel_config],
            creation_spec=creation_spec,
            sudo_session_enabled=model_spec.sudo_session_enabled,
            callback_url=yarl.URL(str(model_spec.callback_url))
            if model_spec.callback_url
            else None,
            internal_data=internal_data,
            session_tag=model_spec.tag,
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
                routes = await self._deployment_repository.get_routes_by_endpoint(
                    endpoint.endpoint_id
                )

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
                        endpoint.endpoint_id,
                        EndpointLifecycle.CREATED,  # Use CREATED instead of READY
                    )
                elif healthy_routes > 0:
                    # Some routes healthy - degraded state
                    sync_stats["degraded"] += 1
                    await self._deployment_repository.update_endpoint_lifecycle(
                        endpoint.endpoint_id,
                        EndpointLifecycle.CREATED,  # Keep as CREATED but track degraded status separately
                    )
                else:
                    # No healthy routes
                    sync_stats["failed"] += 1
                    await self._deployment_repository.update_endpoint_lifecycle(
                        endpoint.endpoint_id,
                        EndpointLifecycle.DESTROYING,  # Mark for cleanup if all routes failed
                    )

                # Handle failed routes - mark for recovery in next cycle
                # Auto-scaling and recovery will be handled by periodic timer
                if failed_routes and endpoint.desired_session_count > healthy_routes:
                    log.debug(
                        "Endpoint {} has {} failed routes, will be handled in next auto-scaling cycle",
                        endpoint.endpoint_id,
                        len(failed_routes),
                    )

            except Exception as e:
                log.error(
                    "Error synchronizing endpoint {}: {}",
                    endpoint.endpoint_id,
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
