"""Deployment controller for managing model services and deployments."""

import logging
import uuid
from dataclasses import dataclass
from typing import Optional

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.deployment.creator import DeploymentCreationDraft
from ai.backend.manager.data.deployment.scale import AutoScalingRule, AutoScalingRuleCreator
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    RouteInfo,
    RouteSearchResult,
    RouteTrafficStatus,
)
from ai.backend.manager.models.deployment_policy import DeploymentPolicyData
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.repositories.deployment.options import RouteConditions
from ai.backend.manager.repositories.deployment.updaters import (
    DeploymentPolicyUpdaterSpec,
    DeploymentUpdaterSpec,
    RouteUpdaterSpec,
)
from ai.backend.manager.sokovan.deployment.revision_generator.registry import (
    RevisionGeneratorRegistry,
    RevisionGeneratorRegistryArgs,
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
    _revision_generator_registry: RevisionGeneratorRegistry

    def __init__(self, args: DeploymentControllerArgs) -> None:
        """Initialize the deployment controller with required services."""
        self._scheduling_controller = args.scheduling_controller
        self._deployment_repository = args.deployment_repository
        self._config_provider = args.config_provider
        self._storage_manager = args.storage_manager
        self._event_producer = args.event_producer
        self._valkey_schedule = args.valkey_schedule
        self._revision_generator_registry = RevisionGeneratorRegistry(
            RevisionGeneratorRegistryArgs(deployment_repository=self._deployment_repository)
        )

    async def create_deployment(
        self,
        draft: DeploymentCreationDraft,
    ) -> DeploymentInfo:
        """
        Create a new deployment based on the provided specification.

        Args:
            draft: Deployment creation specification

        Returns:
            DeploymentInfo: Information about the created deployment
        """
        log.info("Creating deployment '{}' in project {}", draft.name, draft.project)

        # Pre-fetch default architecture from scaling group
        default_architecture = (
            await self._deployment_repository.get_default_architecture_from_scaling_group(
                draft.metadata.resource_group
            )
        )

        generator = self._revision_generator_registry.get(
            draft.draft_model_revision.execution.runtime_variant
        )
        model_revision = await generator.generate_revision(
            draft_revision=draft.draft_model_revision,
            vfolder_id=draft.draft_model_revision.mounts.model_vfolder_id,
            model_definition_path=draft.draft_model_revision.mounts.model_definition_path,
            default_architecture=default_architecture,
        )
        await self._scheduling_controller.validate_session_spec(
            SessionValidationSpec.from_revision(model_revision=model_revision)
        )

        deployment_info = await self._deployment_repository.create_endpoint_legacy(
            draft.to_creator(model_revision)
        )
        return deployment_info

    async def update_deployment(
        self,
        endpoint_id: uuid.UUID,
        spec: DeploymentUpdaterSpec,
    ) -> DeploymentInfo:
        """
        Update an existing deployment with new specifications.

        Args:
            endpoint_id: ID of the deployment to update
            spec: Deployment updater specification

        Returns:
            DeploymentInfo: Information about the updated deployment
        """
        log.info("Updating deployment {}", endpoint_id)
        updater = Updater[EndpointRow](spec=spec, pk_value=endpoint_id)
        modified_endpoint = await self._deployment_repository.get_modified_endpoint(
            endpoint_id=endpoint_id, updater=updater
        )
        target_revision = modified_endpoint.target_revision()
        if target_revision:
            await self._scheduling_controller.validate_session_spec(
                SessionValidationSpec.from_revision(model_revision=target_revision)
            )
        res = await self._deployment_repository.update_endpoint_with_spec(updater)
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

    # ========== Deployment Policy Methods ==========

    async def get_deployment_policy(
        self,
        endpoint_id: uuid.UUID,
    ) -> DeploymentPolicyData:
        """Get the deployment policy for an endpoint.

        Args:
            endpoint_id: ID of the endpoint

        Returns:
            DeploymentPolicyData: Policy data
        """
        return await self._deployment_repository.get_deployment_policy(endpoint_id)

    async def update_deployment_policy(
        self,
        endpoint_id: uuid.UUID,
        updater_spec: DeploymentPolicyUpdaterSpec,
    ) -> DeploymentPolicyData:
        """Update the deployment policy for an endpoint.

        Args:
            endpoint_id: ID of the endpoint
            updater_spec: Policy update specification

        Returns:
            DeploymentPolicyData: Updated policy data
        """
        # First get the policy to find its ID (primary key)
        policy = await self._deployment_repository.get_deployment_policy(endpoint_id)
        return await self._deployment_repository.update_deployment_policy(
            Updater(spec=updater_spec, pk_value=policy.id)
        )

    # Route operations

    async def search_routes(
        self,
        querier: BatchQuerier,
    ) -> RouteSearchResult:
        """Search routes with pagination and filtering.

        Args:
            querier: BatchQuerier containing conditions, orders, and pagination

        Returns:
            RouteSearchResult with items, total_count, and pagination info
        """
        return await self._deployment_repository.search_routes(querier)

    async def get_route(
        self,
        route_id: uuid.UUID,
    ) -> Optional[RouteInfo]:
        """Get a single route by its ID.

        Args:
            route_id: The route ID

        Returns:
            RouteInfo if found, None otherwise
        """
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1),
            conditions=[RouteConditions.by_ids([route_id])],
        )
        result = await self._deployment_repository.search_routes(querier)
        return result.items[0] if result.items else None

    async def update_route_traffic_status(
        self,
        route_id: uuid.UUID,
        traffic_status: RouteTrafficStatus,
    ) -> Optional[RouteInfo]:
        """Update route traffic status.

        Args:
            route_id: The route ID
            traffic_status: New traffic status

        Returns:
            Updated RouteInfo if found, None otherwise
        """
        from ai.backend.manager.models.routing import RoutingRow
        from ai.backend.manager.types import OptionalState

        spec = RouteUpdaterSpec(
            traffic_status=OptionalState.update(traffic_status),
        )
        updater: Updater[RoutingRow] = Updater(spec=spec, pk_value=route_id)
        success = await self._deployment_repository.update_route(updater)
        if not success:
            return None
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1),
            conditions=[RouteConditions.by_ids([route_id])],
        )
        result = await self._deployment_repository.search_routes(querier)
        return result.items[0] if result.items else None
