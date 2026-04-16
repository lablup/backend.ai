"""Deployment controller for managing model services and deployments."""

import logging
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.config import ModelDefinition
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import ClusterMode, ResourceSlot
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.deployment.creator import (
    DeploymentCreationDraft,
    ModelRevisionCreator,
)
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentLifecycleSubStep,
    ExecutionSpec,
    ModelRevisionData,
    MountMetadata,
    ResourceSpec,
    RevisionDraft,
    RouteInfo,
    RouteTrafficStatus,
    merge_revision_drafts,
)
from ai.backend.manager.data.deployment_revision_preset.types import PresetValueData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.deployment_revision_preset.types import PresetValueEntry
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.routing.conditions import RouteConditions
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.repositories.deployment.creators.endpoint import LegacyEndpointCreatorSpec
from ai.backend.manager.repositories.deployment.creators.revision import (
    DeploymentRevisionCreatorSpec,
)
from ai.backend.manager.repositories.deployment.updaters import (
    DeploymentUpdaterSpec,
    RouteUpdaterSpec,
)
from ai.backend.manager.sokovan.deployment.definition_generator.base import ModelDefinitionContext
from ai.backend.manager.sokovan.deployment.definition_generator.registry import (
    ModelDefinitionGeneratorRegistry,
)
from ai.backend.manager.sokovan.deployment.exceptions import (
    DeploymentAlreadyInProgress,
    InvalidEndpointState,
)
from ai.backend.manager.sokovan.deployment.revision_generator.registry import (
    RevisionGeneratorRegistry,
)
from ai.backend.manager.sokovan.deployment.types import (
    ActivateRevisionResult,
    DeploymentLifecycleType,
)
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController
from ai.backend.manager.sokovan.scheduling_controller.types import SessionValidationSpec
from ai.backend.manager.types import OptionalState

if TYPE_CHECKING:
    from ai.backend.manager.repositories.deployment_revision_preset.repository import (
        DeploymentRevisionPresetRepository,
    )

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
    revision_generator_registry: RevisionGeneratorRegistry
    model_definition_generator_registry: ModelDefinitionGeneratorRegistry
    deployment_revision_preset_repository: "DeploymentRevisionPresetRepository | None"


class DeploymentController:
    """Controller for deployment and model service management.

    Owns all state-changing trigger operations for deployments:
    - create_deployment / update_deployment / destroy_deployment
    - add_revision / activate_revision
    - mark_lifecycle_needed

    Services compose these triggers; read-only queries (search/get) go
    directly from Service to Repository.
    """

    _scheduling_controller: SchedulingController
    _deployment_repository: DeploymentRepository
    _config_provider: ManagerConfigProvider
    _storage_manager: StorageSessionManager
    _event_producer: EventProducer
    _valkey_schedule: ValkeyScheduleClient
    _revision_generator_registry: RevisionGeneratorRegistry
    _model_definition_generator_registry: ModelDefinitionGeneratorRegistry
    _deployment_revision_preset_repository: "DeploymentRevisionPresetRepository | None"

    def __init__(self, args: DeploymentControllerArgs) -> None:
        """Initialize the deployment controller with required services."""
        self._scheduling_controller = args.scheduling_controller
        self._deployment_repository = args.deployment_repository
        self._config_provider = args.config_provider
        self._storage_manager = args.storage_manager
        self._event_producer = args.event_producer
        self._valkey_schedule = args.valkey_schedule
        self._revision_generator_registry = args.revision_generator_registry
        self._model_definition_generator_registry = args.model_definition_generator_registry
        self._deployment_revision_preset_repository = args.deployment_revision_preset_repository

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

    # ========== Revision Trigger Operations ==========

    async def add_revision(
        self,
        deployment_id: uuid.UUID,
        creator: ModelRevisionCreator,
    ) -> ModelRevisionData:
        """Add a new revision to a deployment.

        Full pipeline: preset apply → config merge → model definition resolve
        → revision create (with RBAC) → history pruning.

        This is the single authority for revision creation — all API paths
        (v2 GQL, legacy GQL) must go through this method.
        """
        log.info("Adding model revision to deployment {}", deployment_id)

        endpoint_info = await self._deployment_repository.get_endpoint_info(deployment_id)

        # 1. Apply preset defaults (revision-level)
        preset_applied = await self._apply_preset(creator)
        # 2. Merge deployment-config.yaml from vfolder
        merged_creator = await self._merge_deployment_config(preset_applied)
        # 3. Resolve final model definition
        resolved_model_definition = await self._resolve_model_definition(merged_creator)

        spec = DeploymentRevisionCreatorSpec(
            endpoint_id=deployment_id,
            image_id=merged_creator.image_id,
            resource_group=endpoint_info.metadata.resource_group,
            resource_slots=ResourceSlot(merged_creator.resource_spec.resource_slots),
            resource_opts=merged_creator.resource_spec.resource_opts or {},
            cluster_mode=merged_creator.resource_spec.cluster_mode.value,
            cluster_size=merged_creator.resource_spec.cluster_size,
            model_id=merged_creator.mounts.model_vfolder_id,
            model_mount_destination=merged_creator.mounts.model_mount_destination,
            model_definition_path=merged_creator.mounts.model_definition_path,
            model_definition=resolved_model_definition,
            startup_command=merged_creator.execution.startup_command,
            bootstrap_script=merged_creator.execution.bootstrap_script,
            environ=merged_creator.execution.environ or {},
            callback_url=str(merged_creator.execution.callback_url)
            if merged_creator.execution.callback_url
            else None,
            runtime_variant=merged_creator.execution.runtime_variant,
            extra_mounts=(),
            preset_values=[
                PresetValueEntry(preset_id=pv.preset_id, value=pv.value)
                for pv in merged_creator.preset_values
            ],
        )
        rbac_creator = RBACEntityCreator(
            spec=spec,
            element_type=RBACElementType.DEPLOYMENT_REVISION,
            scope_ref=RBACElementRef(
                element_type=RBACElementType.MODEL_DEPLOYMENT,
                element_id=str(deployment_id),
            ),
        )
        revision_data = await self._deployment_repository.create_revision_with_next_number(
            rbac_creator, deployment_id
        )

        # Prune old revisions beyond history limit
        await self._prune_revision_history(
            deployment_id, endpoint_info.metadata.revision_history_limit
        )

        return revision_data

    async def activate_revision(
        self,
        deployment_id: uuid.UUID,
        revision_id: uuid.UUID,
    ) -> ActivateRevisionResult:
        """Activate a specific revision by initiating the deployment strategy.

        Sets deploying_revision and transitions the deployment to DEPLOYING state.
        The coordinator will execute the configured deployment strategy (rolling
        update, blue-green, etc.) and swap deploying_revision → current_revision
        on completion.

        Raises:
            DeploymentAlreadyInProgress: If another revision is currently deploying.
            InvalidEndpointState: If the revision is already current.
        """
        # 1. Validate revision exists
        _revision = await self._deployment_repository.get_revision(revision_id)

        # 2. Validate deployment state
        deployment_info = await self._deployment_repository.get_endpoint_info(deployment_id)
        if deployment_info.deploying_revision_id is not None:
            raise DeploymentAlreadyInProgress(
                f"Deployment {deployment_id} already has deploying_revision "
                f"{deployment_info.deploying_revision_id} in progress."
            )
        if deployment_info.current_revision_id == revision_id:
            raise InvalidEndpointState(
                f"Revision {revision_id} is already the current revision "
                f"of deployment {deployment_id}."
            )

        # 3. Set deploying_revision atomically (WHERE deploying_revision IS NULL)
        previous_revision_id, updated = await self._deployment_repository.set_deploying_revision(
            deployment_id, revision_id
        )
        if not updated:
            raise DeploymentAlreadyInProgress(
                f"Deployment {deployment_id} already has a deploying revision in progress "
                f"(concurrent activation detected)."
            )

        # 4. Trigger DEPLOYING lifecycle
        await self.mark_lifecycle_needed(
            DeploymentLifecycleType.DEPLOYING,
            sub_step=DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING,
        )

        log.info(
            "Started deploying revision {} for deployment {} (current: {})",
            revision_id,
            deployment_id,
            previous_revision_id,
        )

        # 5. Return result with updated info and policy
        deployment_info = await self._deployment_repository.get_endpoint_info(deployment_id)
        deployment_policy = await self._deployment_repository.get_deployment_policy(deployment_id)

        return ActivateRevisionResult(
            deployment_info=deployment_info,
            previous_revision_id=previous_revision_id,
            activated_revision_id=revision_id,
            deployment_policy=deployment_policy,
        )

    # ========== Revision Private Helpers ==========

    async def _apply_preset(
        self,
        creator: ModelRevisionCreator,
    ) -> ModelRevisionCreator:
        """Apply DeploymentRevisionPreset values to the creator if revision_preset_id is set.

        Creates a RevisionDraft from the preset, another from the request,
        and merges them with request values taking priority.
        """
        if not creator.revision_preset_id or not self._deployment_revision_preset_repository:
            return creator

        preset_data = await self._deployment_revision_preset_repository.get_by_id(
            creator.revision_preset_id,
        )
        preset_slots = await self._deployment_revision_preset_repository.get_resource_slots(
            creator.revision_preset_id,
        )

        preset_draft = RevisionDraft(
            image_id=preset_data.image_id,
            resource_slots={slot_name: str(quantity) for slot_name, quantity in preset_slots},
            resource_opts={o.name: o.value for o in preset_data.resource_opts},
            cluster_mode=ClusterMode(preset_data.cluster_mode)
            if preset_data.cluster_mode
            else None,
            cluster_size=preset_data.cluster_size,
            startup_command=preset_data.startup_command,
            bootstrap_script=preset_data.bootstrap_script,
            environ={e.key: e.value for e in preset_data.environ},
            model_definition=(
                ModelDefinition(**preset_data.model_definition)
                if preset_data.model_definition
                else None
            ),
        )

        request_draft = RevisionDraft(
            image_id=creator.image_id,
            resource_slots=(
                dict(creator.resource_spec.resource_slots)
                if creator.resource_spec.resource_slots
                else None
            ),
            resource_opts=(
                dict(creator.resource_spec.resource_opts)
                if creator.resource_spec.resource_opts
                else None
            ),
            cluster_mode=creator.resource_spec.cluster_mode,
            cluster_size=creator.resource_spec.cluster_size,
            startup_command=creator.execution.startup_command,
            bootstrap_script=creator.execution.bootstrap_script,
            environ=creator.execution.environ,
            runtime_variant=creator.execution.runtime_variant,
            model_definition=creator.model_definition,
        )

        merged = merge_revision_drafts(preset_draft, request_draft)

        return ModelRevisionCreator(
            image_id=merged.image_id or creator.image_id,
            resource_spec=ResourceSpec(
                cluster_mode=merged.cluster_mode or creator.resource_spec.cluster_mode,
                cluster_size=merged.cluster_size or creator.resource_spec.cluster_size,
                resource_slots=merged.resource_slots or creator.resource_spec.resource_slots,
                resource_opts=merged.resource_opts,
            ),
            mounts=creator.mounts,
            execution=ExecutionSpec(
                startup_command=merged.startup_command,
                bootstrap_script=merged.bootstrap_script,
                environ=merged.environ,
                runtime_variant=merged.runtime_variant or creator.execution.runtime_variant,
                callback_url=creator.execution.callback_url,
                inference_runtime_config=creator.execution.inference_runtime_config,
            ),
            model_definition=merged.model_definition,
            revision_preset_id=creator.revision_preset_id,
            preset_values=[
                PresetValueData(preset_id=pv.preset_id, value=pv.value)
                for pv in preset_data.preset_values
            ],
        )

    async def _merge_deployment_config(
        self,
        revision_creator: ModelRevisionCreator,
    ) -> ModelRevisionCreator:
        """Merge deployment-config.yaml defaults from the model vfolder.

        The creator's values take precedence over deployment config defaults.
        If loading the config fails, the creator is returned as-is (configs are optional).
        """
        generator = self._revision_generator_registry.get(
            revision_creator.execution.runtime_variant
        )
        try:
            deployment_config = await generator.load_deployment_config(
                vfolder_id=revision_creator.mounts.model_vfolder_id,
                runtime_variant=revision_creator.execution.runtime_variant,
            )
        except Exception:
            log.warning(
                "Failed to load deployment config for vfolder {}, proceeding without it",
                revision_creator.mounts.model_vfolder_id,
                exc_info=True,
            )
            return revision_creator
        if deployment_config is None:
            return revision_creator

        merged_environ = revision_creator.execution.environ
        if deployment_config.environ:
            merged_environ = {
                **deployment_config.environ,
                **(revision_creator.execution.environ or {}),
            }

        merged_resource_slots = revision_creator.resource_spec.resource_slots
        if deployment_config.resource_slots:
            merged_resource_slots = {
                **deployment_config.resource_slots,
                **revision_creator.resource_spec.resource_slots,
            }

        return ModelRevisionCreator(
            image_id=revision_creator.image_id,
            resource_spec=revision_creator.resource_spec.model_copy(
                update={"resource_slots": merged_resource_slots},
            ),
            mounts=revision_creator.mounts,
            execution=revision_creator.execution.model_copy(
                update={"environ": merged_environ},
            ),
            model_definition=revision_creator.model_definition,
        )

    async def _resolve_model_definition(
        self,
        revision_creator: ModelRevisionCreator,
    ) -> ModelDefinition:
        """Generate the final model definition for a revision.

        Delegates to ModelDefinitionGeneratorRegistry for the full merge:
        programmatic generation → user override → storage file override.
        """
        context = ModelDefinitionContext(
            mounts=MountMetadata(
                model_vfolder_id=revision_creator.mounts.model_vfolder_id,
                model_definition_path=revision_creator.mounts.model_definition_path,
                model_mount_destination=revision_creator.mounts.model_mount_destination,
            ),
            execution=revision_creator.execution,
            model_definition=revision_creator.model_definition,
        )
        return await self._model_definition_generator_registry.generate_model_definition(context)

    async def _prune_revision_history(
        self,
        deployment_id: uuid.UUID,
        revision_history_limit: int | None,
    ) -> None:
        """Delete old revisions that exceed the history limit.

        Preserves current_revision and deploying_revision.
        """
        if revision_history_limit is None or revision_history_limit <= 0:
            return
        try:
            await self._deployment_repository.prune_old_revisions(
                deployment_id, revision_history_limit
            )
        except Exception:
            log.warning(
                "Failed to prune revision history for deployment {}, skipping",
                deployment_id,
                exc_info=True,
            )

    # ========== Route State Operations ==========

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
