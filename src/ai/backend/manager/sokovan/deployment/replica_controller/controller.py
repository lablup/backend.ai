"""Replica controller for managing deployment replicas."""

import logging
from dataclasses import dataclass
from uuid import UUID, uuid4

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import SessionTypes
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.repositories.deployment import DeploymentRepository

from ..exceptions import ReplicaCreationError
from .network_configurator import NetworkConfigurator
from .spec_builder import SpecBuilder
from .types import ReplicaData, ReplicaSpec, SessionEnqueueSpec

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class ReplicaControllerArgs:
    """Arguments for initializing ReplicaController."""

    repository: DeploymentRepository
    config_provider: ManagerConfigProvider
    event_producer: EventProducer


class ReplicaController:
    """Controller for managing replicas (sessions) in deployments."""

    _repository: DeploymentRepository
    _config_provider: ManagerConfigProvider
    _event_producer: EventProducer
    _spec_builder: SpecBuilder
    _network_configurator: NetworkConfigurator

    def __init__(self, args: ReplicaControllerArgs) -> None:
        self._repository = args.repository
        self._config_provider = args.config_provider
        self._event_producer = args.event_producer
        self._spec_builder = SpecBuilder()
        self._network_configurator = NetworkConfigurator()

    async def create_replicas(
        self,
        spec: ReplicaSpec,
        count: int,
    ) -> list[ReplicaData]:
        """
        Create multiple replicas for an endpoint.

        :param spec: Specification for creating replicas
        :param count: Number of replicas to create
        :return: List of created replica data
        """
        if count <= 0:
            raise ReplicaCreationError(f"Invalid replica count: {count}")

        created_replicas: list[ReplicaData] = []

        try:
            for i in range(count):
                # Build session enqueue specification
                session_spec = self._build_session_spec(spec, i)

                # Configure network
                network_config = await self._network_configurator.configure(
                    spec.endpoint_id,
                    session_spec.session_name,
                    spec.network_config,
                )

                # Create route for this replica
                route_id = await self._repository.create_route(
                    spec.endpoint_id,
                    session_id=None,  # Will be updated after session creation
                )

                # Enqueue session
                session_id = await self._enqueue_session(session_spec)

                # Update route with session ID
                await self._repository.update_route_session(route_id, session_id)

                # Create replica data
                replica_data = await self._repository.create_replica(
                    endpoint_id=spec.endpoint_id,
                    session_id=session_id,
                    route_id=route_id,
                )

                created_replicas.append(replica_data)

                log.info(
                    "Created replica {} for endpoint {}",
                    session_id,
                    spec.endpoint_id,
                )

        except Exception as e:
            log.error(
                "Failed to create replicas for endpoint {}: {}",
                spec.endpoint_id,
                str(e),
            )
            # Cleanup partially created replicas
            await self._cleanup_replicas(created_replicas)
            raise ReplicaCreationError(f"Failed to create replicas: {str(e)}") from e

        return created_replicas

    async def destroy_replicas(
        self,
        endpoint_id: UUID,
        replica_ids: list[UUID],
    ) -> None:
        """
        Destroy specified replicas for an endpoint.

        :param endpoint_id: ID of the endpoint
        :param replica_ids: List of replica IDs to destroy
        """
        for replica_id in replica_ids:
            try:
                replica_data = await self._repository.get_replica(replica_id)
                if replica_data and replica_data.endpoint_id == endpoint_id:
                    # Terminate session
                    await self._terminate_session(replica_data.session_id)

                    # Delete route
                    if replica_data.route_id:
                        await self._repository.delete_route(replica_data.route_id)

                    # Update replica status
                    await self._repository.update_replica_status(
                        replica_id,
                        "terminated",
                    )

                    log.info(
                        "Destroyed replica {} for endpoint {}",
                        replica_id,
                        endpoint_id,
                    )
            except Exception as e:
                log.error(
                    "Failed to destroy replica {} for endpoint {}: {}",
                    replica_id,
                    endpoint_id,
                    str(e),
                )

    def _build_session_spec(
        self,
        replica_spec: ReplicaSpec,
        index: int,
    ) -> SessionEnqueueSpec:
        """Build session enqueue specification from replica spec."""
        session_name = f"replica-{replica_spec.endpoint_id}-{index}-{uuid4().hex[:8]}"

        return self._spec_builder.build(
            endpoint_id=replica_spec.endpoint_id,
            session_name=session_name,
            session_type=SessionTypes.INFERENCE,
            image=replica_spec.image,
            resources=replica_spec.resources,
            mounts=replica_spec.mounts,
            environ=replica_spec.environ,
            scaling_group=replica_spec.scaling_group,
            cluster_mode=replica_spec.cluster_mode,
            cluster_size=replica_spec.cluster_size,
            network_config=replica_spec.network_config,
            startup_command=replica_spec.startup_command,
            bootstrap_script=replica_spec.bootstrap_script,
            tag=f"endpoint:{replica_spec.endpoint_id}",
        )

    async def _enqueue_session(
        self,
        spec: SessionEnqueueSpec,
    ) -> UUID:
        """
        Enqueue a session for creation.

        :param spec: Session enqueue specification
        :return: Session ID
        """
        # This will be implemented to call the actual session enqueue logic
        # For now, return a placeholder UUID
        session_id = uuid4()
        log.debug("Enqueued session {} with spec: {}", session_id, spec)
        return session_id

    async def _terminate_session(
        self,
        session_id: UUID,
    ) -> None:
        """
        Terminate a session.

        :param session_id: ID of the session to terminate
        """
        # This will be implemented to call the actual session termination logic
        log.debug("Terminating session {}", session_id)

    async def _cleanup_replicas(
        self,
        replicas: list[ReplicaData],
    ) -> None:
        """
        Cleanup partially created replicas.

        :param replicas: List of replicas to cleanup
        """
        for replica in replicas:
            try:
                if replica.session_id:
                    await self._terminate_session(replica.session_id)
                if replica.route_id:
                    await self._repository.delete_route(replica.route_id)
            except Exception as e:
                log.error(
                    "Failed to cleanup replica {}: {}",
                    replica.id,
                    str(e),
                )
