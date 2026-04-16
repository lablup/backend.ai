"""Deployment controller for managing model services and deployments."""

import logging
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import ClusterMode, ResourceSlot, RuntimeVariant
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
    ModelRevisionSpec,
    ModelRevisionSpecDraft,
    MountMetadata,
    ResourceSpec,
    RevisionDraft,
    RouteInfo,
    RouteTrafficStatus,
    merge_revision_drafts,
)
from ai.backend.manager.data.image.types import ImageIdentifier
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.errors.api import InvalidAPIParameters
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
from ai.backend.manager.sokovan.deployment.definition_generator.registry import (
    ModelDefinitionGeneratorRegistry,
)
from ai.backend.manager.sokovan.deployment.exceptions import (
    DeploymentAlreadyInProgress,
    InvalidEndpointState,
)
from ai.backend.manager.sokovan.deployment.revision_draft import (
    DeploymentConfigDraftGenerator,
    ModelDefinitionDraftGenerator,
    PresetDraftGenerator,
    revision_draft_from_creator,
    revision_draft_from_spec,
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
    _deployment_config_draft_generator: DeploymentConfigDraftGenerator
    _model_definition_draft_generator: ModelDefinitionDraftGenerator
    _preset_draft_generator: PresetDraftGenerator | None

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
        self._deployment_config_draft_generator = DeploymentConfigDraftGenerator(
            args.deployment_repository
        )
        self._model_definition_draft_generator = ModelDefinitionDraftGenerator(
            args.model_definition_generator_registry
        )
        self._preset_draft_generator = (
            PresetDraftGenerator(args.deployment_revision_preset_repository)
            if args.deployment_revision_preset_repository is not None
            else None
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

        default_architecture = (
            await self._deployment_repository.get_default_architecture_from_scaling_group(
                draft.metadata.resource_group
            )
        )

        request_draft = revision_draft_from_spec(draft.draft_model_revision)
        merged = await self._build_revision_draft(
            request_draft=request_draft,
            mounts=draft.draft_model_revision.mounts,
            execution=draft.draft_model_revision.execution,
            preset_id=None,
            default_architecture=default_architecture,
        )
        model_revision = self._revision_spec_from_draft(
            merged, mounts=draft.draft_model_revision.mounts
        )

        validator = self._revision_generator_registry.get(model_revision.execution.runtime_variant)
        await validator.validate_revision(model_revision)

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

        Builds a RevisionDraft from each independent source and merges them:
        deployment-config.yaml → preset → model-definition.yaml → request.

        This is the single authority for revision creation — all API paths
        (v2 GQL, legacy GQL) must go through this method.
        """
        log.info("Adding model revision to deployment {}", deployment_id)

        endpoint_info = await self._deployment_repository.get_endpoint_info(deployment_id)

        mounts = MountMetadata(
            model_vfolder_id=creator.mounts.model_vfolder_id,
            model_definition_path=creator.mounts.model_definition_path,
            model_mount_destination=creator.mounts.model_mount_destination,
        )
        request_draft = revision_draft_from_creator(creator)
        merged = await self._build_revision_draft(
            request_draft=request_draft,
            mounts=mounts,
            execution=creator.execution,
            preset_id=creator.revision_preset_id,
            default_architecture=None,
        )

        runtime_variant = merged.runtime_variant or creator.execution.runtime_variant
        spec = DeploymentRevisionCreatorSpec(
            endpoint_id=deployment_id,
            image_id=merged.image_id or creator.image_id,
            resource_group=endpoint_info.metadata.resource_group,
            resource_slots=ResourceSlot(merged.resource_slots or {}),
            resource_opts=dict(merged.resource_opts) if merged.resource_opts else {},
            cluster_mode=(merged.cluster_mode or ClusterMode.SINGLE_NODE).value,
            cluster_size=merged.cluster_size or 1,
            model_id=creator.mounts.model_vfolder_id,
            model_mount_destination=creator.mounts.model_mount_destination,
            model_definition_path=creator.mounts.model_definition_path,
            model_definition=merged.model_definition,
            startup_command=merged.startup_command,
            bootstrap_script=merged.bootstrap_script,
            environ=dict(merged.environ) if merged.environ else {},
            callback_url=str(merged.callback_url) if merged.callback_url else None,
            runtime_variant=runtime_variant,
            extra_mounts=(),
            preset_values=[
                PresetValueEntry(preset_id=pv.preset_id, value=pv.value)
                for pv in (merged.preset_values or [])
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

    async def resolve_legacy_revision_spec(
        self,
        draft_revision: ModelRevisionSpecDraft,
        default_architecture: str | None = None,
    ) -> ModelRevisionSpec:
        """Build a final ``ModelRevisionSpec`` from a legacy draft via the unified
        4-way merge pipeline (deployment-config.yaml + model-definition.yaml
        + request, plus default architecture as the lowest-priority fallback).

        Public entry point used by callers that still need a ``ModelRevisionSpec``
        outside the ``create_deployment`` flow (e.g. model_serving create / try_start).
        """
        request_draft = revision_draft_from_spec(draft_revision)
        merged = await self._build_revision_draft(
            request_draft=request_draft,
            mounts=draft_revision.mounts,
            execution=draft_revision.execution,
            preset_id=None,
            default_architecture=default_architecture,
        )
        spec = self._revision_spec_from_draft(merged, mounts=draft_revision.mounts)
        validator = self._revision_generator_registry.get(spec.execution.runtime_variant)
        await validator.validate_revision(spec)
        return spec

    # ========== Revision Private Helpers ==========

    async def _build_revision_draft(
        self,
        request_draft: RevisionDraft,
        mounts: MountMetadata,
        execution: ExecutionSpec,
        preset_id: uuid.UUID | None,
        default_architecture: str | None,
    ) -> RevisionDraft:
        """Collect RevisionDrafts from each independent source and merge them.

        Merge order (later overrides earlier):
            1. default architecture (lowest priority)
            2. deployment-config.yaml in the model vfolder
            3. revision preset (optional)
            4. model-definition.yaml in the model vfolder (model_definition only)
            5. request (highest priority)
        """
        drafts: list[RevisionDraft] = []
        if default_architecture is not None:
            drafts.append(RevisionDraft(image_architecture=default_architecture))
        drafts.append(
            await self._deployment_config_draft_generator.generate(
                mounts.model_vfolder_id, execution.runtime_variant
            )
        )
        if preset_id is not None and self._preset_draft_generator is not None:
            drafts.append(await self._preset_draft_generator.generate(preset_id))
        drafts.append(await self._model_definition_draft_generator.generate(mounts, execution))
        drafts.append(request_draft)
        return merge_revision_drafts(*drafts)

    def _revision_spec_from_draft(
        self,
        merged: RevisionDraft,
        mounts: MountMetadata,
    ) -> ModelRevisionSpec:
        """Assemble a ModelRevisionSpec from a fully merged RevisionDraft.

        Used by the legacy creation flow where the image is identified by
        (canonical, architecture) rather than by a pre-resolved image id.
        """
        if not merged.image_canonical:
            raise InvalidAPIParameters("image canonical is required to build a revision")
        runtime_variant: RuntimeVariant | None = merged.runtime_variant
        if runtime_variant is None:
            raise InvalidAPIParameters("runtime_variant is required to build a revision")
        image_identifier = ImageIdentifier(
            canonical=merged.image_canonical,
            architecture=merged.image_architecture or "",
        )
        return ModelRevisionSpec(
            image_identifier=image_identifier,
            resource_spec=ResourceSpec(
                cluster_mode=merged.cluster_mode or ClusterMode.SINGLE_NODE,
                cluster_size=merged.cluster_size or 1,
                resource_slots=merged.resource_slots or {},
                resource_opts=merged.resource_opts,
            ),
            mounts=mounts,
            execution=ExecutionSpec(
                startup_command=merged.startup_command,
                bootstrap_script=merged.bootstrap_script,
                environ=dict(merged.environ) if merged.environ else None,
                runtime_variant=runtime_variant,
                callback_url=merged.callback_url,
                inference_runtime_config=merged.inference_runtime_config,
            ),
            model_definition=merged.model_definition,
        )

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
