"""Deployment controller for managing model services and deployments."""

import logging
import uuid
from dataclasses import dataclass

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.deployment.creator import DeploymentCreator
from ai.backend.manager.data.deployment.types import DeploymentInfo
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.repositories.deployment import DeploymentRepository

from ..scheduling_controller import SchedulingController

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

    async def create_deployment(
        self,
        creator: DeploymentCreator,
    ) -> DeploymentInfo:
        """
        Create a new deployment based on the provided specification.

        Args:
            creator: Deployment creation specification

        Returns:
            DeploymentInfo: Information about the created deployment
        """
        log.info("Creating deployment '{}' in project {}", creator.name, creator.project)

        # Create deployment entry in the database
        deployment_info = await self._deployment_repository.create_endpoint(creator)
        return deployment_info

    async def terminate_deployment(
        self,
        endpoint_id: uuid.UUID,
    ) -> bool:
        """
        Terminate an existing deployment and its associated model service.

        Args:
            endpoint_id: ID of the endpoint to terminate
        Returns:
            bool: True if termination was successful, False otherwise
        """
        return await self._deployment_repository.terminate_endpoint(endpoint_id)
