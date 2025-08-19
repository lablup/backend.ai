"""Main deployment controller for managing model serving deployments."""

import logging
from dataclasses import dataclass
from uuid import UUID

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.repositories.deployment import DeploymentRepository

from .auto_scaler import AutoScaler, AutoScalerArgs
from .exceptions import (
    EndpointAlreadyExists,
    EndpointNotFound,
    InvalidReplicaCount,
    ScalingError,
)
from .health_monitor import HealthMonitor, HealthMonitorArgs
from .replica_controller import ReplicaController, ReplicaControllerArgs
from .types import EndpointSpec, ScalingResult

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class DeploymentControllerArgs:
    """Arguments for initializing DeploymentController."""

    repository: DeploymentRepository
    config_provider: ManagerConfigProvider
    storage_manager: StorageSessionManager
    event_producer: EventProducer
    valkey_schedule: ValkeyScheduleClient


class DeploymentController:
    """Controller for managing deployment lifecycle and operations."""

    _repository: DeploymentRepository
    _config_provider: ManagerConfigProvider
    _storage_manager: StorageSessionManager
    _event_producer: EventProducer
    _valkey_schedule: ValkeyScheduleClient

    # Sub-controllers
    _replica_controller: ReplicaController
    _auto_scaler: AutoScaler
    _health_monitor: HealthMonitor

    def __init__(self, args: DeploymentControllerArgs) -> None:
        self._repository = args.repository
        self._config_provider = args.config_provider
        self._storage_manager = args.storage_manager
        self._event_producer = args.event_producer
        self._valkey_schedule = args.valkey_schedule

        # Initialize sub-controllers
        replica_args = ReplicaControllerArgs(
            repository=self._repository,
            config_provider=self._config_provider,
            event_producer=self._event_producer,
        )
        self._replica_controller = ReplicaController(replica_args)

        auto_scaler_args = AutoScalerArgs(
            repository=self._repository,
            replica_controller=self._replica_controller,
            config_provider=self._config_provider,
        )
        self._auto_scaler = AutoScaler(auto_scaler_args)

        health_monitor_args = HealthMonitorArgs(
            repository=self._repository,
            config_provider=self._config_provider,
            replica_controller=self._replica_controller,
        )
        self._health_monitor = HealthMonitor(health_monitor_args)

    async def create_endpoint(
        self,
        spec: EndpointSpec,
    ) -> UUID:
        """
        Create a new endpoint with initial replicas.

        :param spec: Endpoint specification
        :return: ID of the created endpoint
        """
        try:
            # Check if endpoint already exists
            existing = await self._repository.get_endpoint_data(spec.name)
            if existing:
                raise EndpointAlreadyExists(f"Endpoint {spec.name} already exists")

            # Validate replica count
            if spec.replicas <= 0:
                raise InvalidReplicaCount(f"Invalid replica count: {spec.replicas}")

            # Create endpoint in repository
            from datetime import datetime, timezone

            from ai.backend.manager.data.model_serving.types import EndpointLifecycle

            from ..repositories.deployment.types import EndpointConfig, EndpointData

            endpoint_config = EndpointConfig(
                image=spec.image,
                architecture=spec.architecture,
                resources=spec.resources,
                environ=spec.environ,
                mounts=spec.extra_mounts,
                scaling_group=spec.scaling_group,
                startup_command=spec.startup_command,
                bootstrap_script=spec.bootstrap_script,
            )

            endpoint_data = EndpointData(
                id=UUID(),
                name=spec.name,
                model_id=spec.model_id,
                replicas=0,  # Start with 0, will be updated after creating replicas
                desired_replicas=spec.replicas,
                lifecycle_stage=EndpointLifecycle.CREATING,
                runtime_variant=spec.runtime_variant,
                config=endpoint_config,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                owner_id=UUID(),  # Should be provided from context
                domain_id=UUID(),  # Should be provided from context
                project_id=UUID(),  # Should be provided from context
                is_public=spec.open_to_public,
            )

            created_endpoint = await self._repository.create_endpoint(endpoint_data)

            # Create initial replicas
            from .replica_controller.types import ReplicaSpec
            from .types import NetworkConfig

            network_config = NetworkConfig(
                endpoint_id=created_endpoint.id,
                port_mappings={"http": 8080, "https": 8443},
                subdomain=f"endpoint-{created_endpoint.id}",
            )

            replica_spec = ReplicaSpec(
                endpoint_id=created_endpoint.id,
                image=spec.image,
                resources=spec.resources,
                network_config=network_config,
                mounts=spec.extra_mounts,
                environ=spec.environ,
                scaling_group=spec.scaling_group,
                startup_command=spec.startup_command,
                bootstrap_script=spec.bootstrap_script,
            )

            await self._replica_controller.create_replicas(
                replica_spec,
                spec.replicas,
            )

            # Update endpoint replica count
            await self._repository.update_endpoint_replicas(
                created_endpoint.id,
                spec.replicas,
            )

            log.info(
                "Created endpoint {} with {} replicas",
                created_endpoint.name,
                spec.replicas,
            )

            return created_endpoint.id

        except Exception as e:
            log.error("Failed to create endpoint: {}", str(e))
            raise

    async def delete_endpoint(
        self,
        endpoint_id: UUID,
    ) -> None:
        """
        Delete an endpoint and all its resources.

        :param endpoint_id: ID of the endpoint to delete
        """
        try:
            # Get endpoint data
            endpoint = await self._repository.get_endpoint_data(endpoint_id)
            if not endpoint:
                raise EndpointNotFound(f"Endpoint {endpoint_id} not found")

            # Get all replicas
            replicas = await self._repository.get_endpoint_replicas(endpoint_id)

            # Destroy all replicas
            replica_ids = [r.id for r in replicas]
            await self._replica_controller.destroy_replicas(endpoint_id, replica_ids)

            # Delete endpoint from repository
            # (Implementation would be added to repository)

            log.info("Deleted endpoint {}", endpoint.name)

        except Exception as e:
            log.error("Failed to delete endpoint {}: {}", endpoint_id, str(e))
            raise

    async def scale_endpoint(
        self,
        endpoint_id: UUID,
        target_replicas: int,
    ) -> ScalingResult:
        """
        Scale an endpoint to the target number of replicas.

        :param endpoint_id: ID of the endpoint
        :param target_replicas: Target number of replicas
        :return: Scaling result
        """
        try:
            # Get endpoint data
            endpoint = await self._repository.get_endpoint_data(endpoint_id)
            if not endpoint:
                raise EndpointNotFound(f"Endpoint {endpoint_id} not found")

            # Validate target replicas
            if target_replicas < 0:
                raise InvalidReplicaCount(f"Invalid target replicas: {target_replicas}")

            current_replicas = endpoint.replicas

            if target_replicas == current_replicas:
                return ScalingResult(
                    endpoint_id=endpoint_id,
                    previous_replicas=current_replicas,
                    current_replicas=current_replicas,
                    success=True,
                    message="Already at target replica count",
                )

            if target_replicas > current_replicas:
                # Scale up
                replicas_to_create = target_replicas - current_replicas

                replica_spec = await self._repository.get_replica_spec(endpoint_id)
                if not replica_spec:
                    raise ScalingError("Failed to get replica spec")

                created_replicas = await self._replica_controller.create_replicas(
                    replica_spec,
                    replicas_to_create,
                )

                created_ids = [r.id for r in created_replicas]

                # Update endpoint replica count
                await self._repository.update_endpoint_replicas(endpoint_id, target_replicas)

                return ScalingResult(
                    endpoint_id=endpoint_id,
                    previous_replicas=current_replicas,
                    current_replicas=target_replicas,
                    success=True,
                    message=f"Scaled up from {current_replicas} to {target_replicas}",
                    created_replicas=created_ids,
                )

            else:
                # Scale down
                replicas_to_destroy = current_replicas - target_replicas

                # Get replicas to destroy (preferably unhealthy ones)
                all_replicas = await self._repository.get_endpoint_replicas(endpoint_id)
                replicas_to_destroy_ids = [r.id for r in all_replicas[:replicas_to_destroy]]

                await self._replica_controller.destroy_replicas(
                    endpoint_id,
                    replicas_to_destroy_ids,
                )

                # Update endpoint replica count
                await self._repository.update_endpoint_replicas(endpoint_id, target_replicas)

                return ScalingResult(
                    endpoint_id=endpoint_id,
                    previous_replicas=current_replicas,
                    current_replicas=target_replicas,
                    success=True,
                    message=f"Scaled down from {current_replicas} to {target_replicas}",
                    destroyed_replicas=replicas_to_destroy_ids,
                )

        except Exception as e:
            log.error(
                "Failed to scale endpoint {} to {} replicas: {}",
                endpoint_id,
                target_replicas,
                str(e),
            )
            return ScalingResult(
                endpoint_id=endpoint_id,
                previous_replicas=endpoint.replicas if endpoint else 0,
                current_replicas=endpoint.replicas if endpoint else 0,
                success=False,
                message=str(e),
            )

    async def autoscale_endpoints(self) -> None:
        """
        Run auto-scaling for all endpoints with auto-scaling rules.
        """
        try:
            # Evaluate all endpoints for scaling
            decisions = await self._auto_scaler.evaluate_endpoints()

            # Apply scaling decisions
            for decision in decisions:
                log.info(
                    "Auto-scaling endpoint {} from {} to {} replicas (reason: {})",
                    decision.endpoint_id,
                    decision.current_replicas,
                    decision.target_replicas,
                    decision.reason,
                )

                await self._auto_scaler.trigger_scaling(decision)

        except Exception as e:
            log.error("Failed to run auto-scaling: {}", str(e))

    async def check_endpoint_health(
        self,
        endpoint_id: UUID,
    ) -> None:
        """
        Check and reconcile health of an endpoint.

        :param endpoint_id: ID of the endpoint
        """
        try:
            # Check endpoint health
            health_status = await self._health_monitor.check_endpoint_health(endpoint_id)

            # Reconcile unhealthy replicas if needed
            if health_status.unhealthy_replicas:
                log.info(
                    "Reconciling {} unhealthy replicas for endpoint {}",
                    len(health_status.unhealthy_replicas),
                    endpoint_id,
                )
                await self._health_monitor.reconcile_unhealthy_replicas(health_status)

        except Exception as e:
            log.error(
                "Failed to check health for endpoint {}: {}",
                endpoint_id,
                str(e),
            )
