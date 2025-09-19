"""Deployment controller for managing model services and deployments."""

import logging
import uuid
from dataclasses import dataclass

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.deployment.creator import DeploymentCreator
from ai.backend.manager.data.deployment.modifier import DeploymentModifier
from ai.backend.manager.data.deployment.scale import AutoScalingRule, AutoScalingRuleCreator
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    ModelRevisionSpec,
)
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.sokovan.deployment.definition_generator.registry import (
    ModelDefinitionGeneratorRegistry,
    RegistryArgs,
)
from ai.backend.manager.sokovan.deployment.types import DeploymentLifecycleType
from ai.backend.manager.sokovan.scheduling_controller.types import SessionValidationSpec

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
    valkey_schedule: ValkeyScheduleClient


class DeploymentController:
    """Controller for deployment and model service management."""

    _scheduling_controller: SchedulingController
    _deployment_repository: DeploymentRepository
    _config_provider: ManagerConfigProvider
    _storage_manager: StorageSessionManager
    _event_producer: EventProducer
    _valkey_schedule: ValkeyScheduleClient
    _model_definition_generator_registry: ModelDefinitionGeneratorRegistry

    def __init__(self, args: DeploymentControllerArgs) -> None:
        """Initialize the deployment controller with required services."""
        self._scheduling_controller = args.scheduling_controller
        self._deployment_repository = args.deployment_repository
        self._config_provider = args.config_provider
        self._storage_manager = args.storage_manager
        self._event_producer = args.event_producer
        self._valkey_schedule = args.valkey_schedule
        self._model_definition_generator_registry = ModelDefinitionGeneratorRegistry(
            RegistryArgs(deployment_repository=self._deployment_repository)
        )

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
        await self._validate_model_revision(creator.model_revision)
        deployment_info = await self._deployment_repository.create_endpoint(creator)
        return deployment_info

    async def _validate_model_revision(self, model_revision: ModelRevisionSpec) -> None:
        """Validate the model revision specification."""
        generator = self._model_definition_generator_registry.get(
            model_revision.execution.runtime_variant
        )
        model_revision = await generator.generate_model_revision(model_revision)
        await self._scheduling_controller.validate_session_spec(
            SessionValidationSpec.from_revision(model_revision=model_revision)
        )

    async def update_deployment(
        self,
        endpoint_id: uuid.UUID,
        modifier: DeploymentModifier,
    ) -> DeploymentInfo:
        """
        Update an existing deployment with new specifications.

        Args:
            endpoint_id: ID of the deployment to update
            modifier: Deployment modification specification

        Returns:
            DeploymentInfo: Information about the updated deployment
        """
        log.info("Updating deployment {}", endpoint_id)
        modified_endpoint = await self._deployment_repository.get_modified_endpoint(
            endpoint_id=endpoint_id, modifier=modifier
        )
        target_revision = modified_endpoint.target_revision()
        if target_revision:
            await self._validate_model_revision(target_revision)
        res = await self._deployment_repository.update_endpoint_with_modifier(endpoint_id, modifier)
        try:
            await self.mark_lifecycle_needed(DeploymentLifecycleType.CHECK_REPLICA)
        except Exception as e:
            log.error("Failed to mark deployment lifecycle needed: {}", e)
        return res

    async def destroy_deployment(
        self,
        endpoint_id: uuid.UUID,
    ) -> bool:
        """
        Destroy an existing deployment and its associated model service.

        Args:
            endpoint_id: ID of the endpoint to terminate
        Returns:
            bool: True if termination was successful, False otherwise
        """
        return await self._deployment_repository.destroy_endpoint(endpoint_id)

    async def create_autoscaling_rule(
        self,
        endpoint_id: uuid.UUID,
        creator: AutoScalingRuleCreator,
    ) -> AutoScalingRule:
        return await self._deployment_repository.create_autoscaling_rule(
            endpoint_id,
            creator,
        )

    async def list_autoscaling_rules(
        self,
        endpoint_id: uuid.UUID,
    ) -> list[AutoScalingRule]:
        return await self._deployment_repository.list_autoscaling_rules(
            endpoint_id,
        )

    async def delete_autoscaling_rule(
        self,
        rule_id: uuid.UUID,
    ) -> bool:
        return await self._deployment_repository.delete_autoscaling_rule(
            rule_id,
        )

    async def mark_lifecycle_needed(self, lifecycle_type: DeploymentLifecycleType) -> None:
        """
        Mark that a deployment lifecycle operation is needed for the next cycle.

        This is the public interface for hinting that deployment lifecycle operations
        should be processed. The actual processing will be handled by the coordinator.

        Args:
            lifecycle_type: Type of deployment lifecycle to mark as needed
        """
        await self._valkey_schedule.mark_deployment_needed(lifecycle_type.value)
        log.debug("Marked deployment lifecycle needed for type: {}", lifecycle_type.value)
