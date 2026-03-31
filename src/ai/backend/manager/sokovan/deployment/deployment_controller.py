"""Deployment controller for managing model services and deployments."""

import logging
import uuid
from dataclasses import dataclass
from decimal import Decimal

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import ResourceSlot
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.deployment.creator import DeploymentCreationDraft
from ai.backend.manager.data.deployment.scale import AutoScalingRule, AutoScalingRuleCreator
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentLifecycleSubStep,
    DeploymentPolicyData,
    RouteInfo,
    RouteSearchResult,
    RouteTrafficStatus,
)
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.deployment_policy import BlueGreenSpec, RollingUpdateSpec
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.routing.conditions import RouteConditions
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.repositories.deployment.creators.endpoint import LegacyEndpointCreatorSpec
from ai.backend.manager.repositories.deployment.updaters import (
    DeploymentUpdaterSpec,
    RouteUpdaterSpec,
)
from ai.backend.manager.repositories.scaling_group import ScalingGroupRepository
from ai.backend.manager.sokovan.deployment.revision_generator.registry import (
    RevisionGeneratorRegistry,
)
from ai.backend.manager.sokovan.deployment.types import DeploymentLifecycleType
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController
from ai.backend.manager.sokovan.scheduling_controller.types import SessionValidationSpec
from ai.backend.manager.types import OptionalState

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass(frozen=True)
class SurgeShortfallDetail:
    """Diagnostic detail when surge resources are insufficient."""

    strategy: DeploymentStrategy
    surge_count: int
    scaling_group: str
    insufficient_slots: list[str]

    @property
    def surge_description(self) -> str:
        match self.strategy:
            case DeploymentStrategy.ROLLING:
                return f"Rolling update max_surge={self.surge_count}"
            case DeploymentStrategy.BLUE_GREEN:
                return f"Blue-green deployment replica_count={self.surge_count}"

    @property
    def error_message(self) -> str:
        return (
            f"{self.surge_description} requires additional resources "
            f"that exceed the available capacity in scaling group "
            f"'{self.scaling_group}'. "
            f"Insufficient resources: {', '.join(self.insufficient_slots)}"
        )


@dataclass(frozen=True)
class SurgeResourceCheckResult:
    """Result of a deployment surge resource availability check."""

    sufficient: bool
    shortfall: SurgeShortfallDetail | None = None


@dataclass
class DeploymentControllerArgs:
    """Arguments for initializing DeploymentController."""

    scheduling_controller: SchedulingController
    deployment_repository: DeploymentRepository
    scaling_group_repository: ScalingGroupRepository
    config_provider: ManagerConfigProvider
    storage_manager: StorageSessionManager
    event_producer: EventProducer
    valkey_schedule: ValkeyScheduleClient
    revision_generator_registry: RevisionGeneratorRegistry


class DeploymentController:
    """Controller for deployment and model service management."""

    _scheduling_controller: SchedulingController
    _deployment_repository: DeploymentRepository
    _scaling_group_repository: ScalingGroupRepository
    _config_provider: ManagerConfigProvider
    _storage_manager: StorageSessionManager
    _event_producer: EventProducer
    _valkey_schedule: ValkeyScheduleClient
    _revision_generator_registry: RevisionGeneratorRegistry

    def __init__(self, args: DeploymentControllerArgs) -> None:
        """Initialize the deployment controller with required services."""
        self._scheduling_controller = args.scheduling_controller
        self._deployment_repository = args.deployment_repository
        self._scaling_group_repository = args.scaling_group_repository
        self._config_provider = args.config_provider
        self._storage_manager = args.storage_manager
        self._event_producer = args.event_producer
        self._valkey_schedule = args.valkey_schedule
        self._revision_generator_registry = args.revision_generator_registry

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
            default_architecture=default_architecture,
        )
        await self._scheduling_controller.validate_session_spec(
            SessionValidationSpec.from_revision(model_revision=model_revision)
        )
        image_id = await self._deployment_repository.get_image_id(model_revision.image_identifier)

        spec = LegacyEndpointCreatorSpec.from_deployment_creator(
            creator=draft.to_creator(model_revision),
            image_id=image_id,
        )
        creator = RBACEntityCreator(
            spec=spec,
            element_type=RBACElementType.MODEL_DEPLOYMENT,
            scope_ref=RBACElementRef(
                element_type=RBACElementType.USER, element_id=str(draft.metadata.created_user)
            ),
            additional_scope_refs=[],
        )
        return await self._deployment_repository.create_endpoint_legacy(creator)

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
        if modified_endpoint.current_revision_id is not None:
            current_revision = modified_endpoint.resolve_revision_spec(
                modified_endpoint.current_revision_id
            )
            await self._scheduling_controller.validate_session_spec(
                SessionValidationSpec.from_revision(model_revision=current_revision)
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

    async def mark_lifecycle_needed(
        self,
        lifecycle_type: DeploymentLifecycleType,
        sub_step: DeploymentLifecycleSubStep | None = None,
    ) -> None:
        """
        Mark that a deployment lifecycle operation is needed for the next cycle.

        This is the public interface for hinting that deployment lifecycle operations
        should be processed. The actual processing will be handled by the coordinator.

        Args:
            lifecycle_type: Type of deployment lifecycle to mark as needed
            sub_step: Optional sub-step for finer-grained dispatch
        """
        sub_step_value = sub_step.value if sub_step is not None else None
        await self._valkey_schedule.mark_deployment_needed(lifecycle_type.value, sub_step_value)
        log.debug(
            "Marked deployment lifecycle needed for type: {}, sub_step: {}",
            lifecycle_type.value,
            sub_step_value,
        )

    # ========== Rolling Update Validation ==========

    async def check_deployment_surge_resources(
        self,
        deployment_info: DeploymentInfo,
        revision_id: uuid.UUID,
    ) -> SurgeResourceCheckResult:
        """Check whether the scaling group has enough free resources for the deployment surge.

        Depending on the strategy, a different number of extra routes must be
        provisioned while old routes are still running:

        - **Rolling update**: up to ``max_surge`` extra routes beyond the desired count.
        - **Blue-green**: the full ``target_replica_count`` worth of new routes, since
          old and new routes coexist until traffic is switched.

        This is called once at the start of ``activate_revision`` as a pre-flight check.
        The underlying query computes actual resource usage from kernel allocations,
        which is relatively expensive.

        Args:
            deployment_info: Current deployment information
            revision_id: ID of the revision being activated

        Returns:
            SurgeResourceCheckResult with ``sufficient=True`` when resources are adequate,
            or ``sufficient=False`` with detail fields populated otherwise.
        """
        if deployment_info.policy is not None:
            policy = deployment_info.policy
        else:
            policy = await self._deployment_repository.get_deployment_policy(deployment_info.id)
        spec = policy.strategy_spec

        desired_replicas = deployment_info.replica_spec.target_replica_count
        surge_count = self._resolve_surge_count(spec, desired_replicas)
        if surge_count == 0:
            return SurgeResourceCheckResult(sufficient=True)

        revision_data = await self._deployment_repository.get_revision(revision_id)
        per_route_slots = revision_data.resource_config.resource_slot
        cluster_size = revision_data.cluster_config.size
        total_surge = surge_count * cluster_size
        surge_slots = ResourceSlot({k: v * total_surge for k, v in per_route_slots.data.items()})

        scaling_group = deployment_info.metadata.resource_group
        resource_info = await self._scaling_group_repository.get_resource_info(scaling_group)
        free_slots = ResourceSlot({sq.slot_name: sq.quantity for sq in resource_info.free})

        if surge_slots <= free_slots:
            return SurgeResourceCheckResult(sufficient=True)

        insufficient_slots = []
        for slot_name in surge_slots.keys():
            required = surge_slots.get(slot_name, Decimal(0))
            available = free_slots.get(slot_name, Decimal(0))
            if required > available:
                insufficient_slots.append(
                    f"{slot_name}: required={required}, available={available}"
                )
        return SurgeResourceCheckResult(
            sufficient=False,
            shortfall=SurgeShortfallDetail(
                strategy=policy.strategy,
                surge_count=surge_count,
                scaling_group=scaling_group,
                insufficient_slots=insufficient_slots,
            ),
        )

    @staticmethod
    def _resolve_surge_count(
        spec: RollingUpdateSpec | BlueGreenSpec,
        desired_replicas: int,
    ) -> int:
        match spec:
            case RollingUpdateSpec():
                return spec.resolve_max_surge(desired_replicas)
            case BlueGreenSpec():
                return desired_replicas

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
    ) -> RouteInfo | None:
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
    ) -> RouteInfo | None:
        """Update route traffic status.

        Args:
            route_id: The route ID
            traffic_status: New traffic status

        Returns:
            Updated RouteInfo if found, None otherwise
        """
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
