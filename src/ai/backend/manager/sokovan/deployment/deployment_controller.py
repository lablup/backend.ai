"""Deployment controller for managing model services and deployments."""

import dataclasses
import logging
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.exception import UnreachableError
from ai.backend.common.types import ClusterMode, ResourceSlot, RuntimeVariant
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.deployment.creator import (
    DeploymentCreationDraft,
    DeploymentPolicyConfig,
    ModelRevisionCreator,
    NewDeploymentCreator,
    VFolderMountsCreator,
)
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentLifecycleSubStep,
    DeploymentNetworkSpec,
    ExecutionSpec,
    ModelRevisionData,
    ModelRevisionSpec,
    ModelRevisionSpecDraft,
    MountMetadata,
    ReplicaSpec,
    ResourceSpec,
    RevisionDraft,
    RouteInfo,
    RouteTrafficStatus,
    merge_revision_drafts,
)
from ai.backend.manager.data.deployment_revision_preset.types import (
    DeploymentRevisionPresetData,
)
from ai.backend.manager.data.image.types import ImageIdentifier
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.deployment_policy import BlueGreenSpec, RollingUpdateSpec
from ai.backend.manager.models.deployment_revision_preset.types import PresetValueEntry
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.routing.conditions import RouteConditions
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.repositories.deployment.creators import (
    DeploymentCreatorSpec,
    DeploymentMetadataFields,
    DeploymentNetworkFields,
    DeploymentReplicaFields,
)
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
        creator: NewDeploymentCreator,
    ) -> DeploymentInfo:
        """Create a new endpoint with optional policy.

        Resolves deployment-level fields (replica, network, history limit, policy)
        against the revision preset before creating the endpoint. The endpoint
        is created without an initial revision; callers must call
        ``add_deployment_revision`` separately to add and (optionally) activate
        the first revision.

        Args:
            creator: Resolved deployment creator. ``creator.policy`` (or the
                preset-derived policy) is applied during creation.

        Returns:
            DeploymentInfo for the newly created endpoint.
        """
        log.info("Creating deployment '{}'", creator.metadata.name)
        resolved = await self._apply_deployment_level_preset(creator)
        metadata = resolved.metadata
        replica_spec = resolved.replica_spec
        network_spec = resolved.network
        if replica_spec is None or network_spec is None or metadata.revision_history_limit is None:
            raise UnreachableError(
                "_apply_deployment_level_preset must populate replica_spec, network, "
                "and revision_history_limit"
            )
        creator_spec = DeploymentCreatorSpec(
            metadata=DeploymentMetadataFields(
                name=metadata.name,
                domain=metadata.domain,
                project_id=metadata.project,
                resource_group=metadata.resource_group,
                created_user_id=metadata.created_user,
                session_owner_id=metadata.session_owner,
                revision_history_limit=metadata.revision_history_limit,
                tag=metadata.tag,
            ),
            replica=DeploymentReplicaFields(
                replica_count=replica_spec.replica_count,
                desired_replica_count=replica_spec.desired_replica_count,
            ),
            network=DeploymentNetworkFields(
                open_to_public=network_spec.open_to_public,
                url=network_spec.url,
            ),
            revision=None,
        )
        rbac_creator: RBACEntityCreator[EndpointRow] = RBACEntityCreator(
            spec=creator_spec,
            element_type=RBACElementType.MODEL_DEPLOYMENT,
            scope_ref=RBACElementRef(
                element_type=RBACElementType.USER, element_id=str(metadata.created_user)
            ),
            additional_scope_refs=[],
        )
        return await self._deployment_repository.create_endpoint(rbac_creator, resolved.policy)

    async def build_creator_from_legacy_draft(
        self,
        draft: DeploymentCreationDraft,
    ) -> tuple[NewDeploymentCreator, ModelRevisionCreator]:
        """Resolve a legacy ``DeploymentCreationDraft`` into v2 (creator, revision).

        Performs DB-touching resolution so the higher-level service layer can
        compose ``create_deployment`` + ``add_deployment_revision`` uniformly:

        - Resolves ``image_identifier`` (canonical + arch) → ``image_id`` (UUID).
        - Pulls ``default_architecture`` from the scaling group as the lowest-
          priority fallback for the revision draft.
        - Validates the resolved revision spec via the runtime-variant
          validator and the scheduling controller, preserving legacy fast-fail
          semantics before any endpoint row is written.
        """
        log.info(
            "Building creator from legacy draft '{}' in project {}",
            draft.name,
            draft.project,
        )
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
        model_revision_spec = self._revision_spec_from_draft(
            merged, mounts=draft.draft_model_revision.mounts
        )
        validator = self._revision_generator_registry.get(
            model_revision_spec.execution.runtime_variant
        )
        await validator.validate_revision(model_revision_spec)
        await self._scheduling_controller.validate_session_spec(
            SessionValidationSpec.from_revision(model_revision=model_revision_spec)
        )
        image_id = await self._deployment_repository.get_image_id(
            model_revision_spec.image_identifier
        )
        creator = NewDeploymentCreator(
            metadata=draft.metadata,
            replica_spec=draft.replica_spec,
            network=draft.network,
            model_revision=None,
            policy=None,
        )
        # Carry the merged draft form forward; ``add_deployment_revision``
        # re-merges and resolves at its own persistence boundary.
        revision = ModelRevisionCreator(
            image_id=image_id,
            resource_spec=model_revision_spec.resource_spec,
            mounts=VFolderMountsCreator(
                model_vfolder_id=model_revision_spec.mounts.model_vfolder_id,
                model_definition_path=model_revision_spec.mounts.model_definition_path,
                model_mount_destination=model_revision_spec.mounts.model_mount_destination,
            ),
            execution=model_revision_spec.execution,
            model_definition=merged.model_definition,
            revision_preset_id=None,
        )
        return creator, revision

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
        endpoint_id: uuid.UUID,
        overrides: RevisionDraft,
        mounts: MountMetadata,
        preset_id: uuid.UUID | None = None,
        base: RevisionDraft | None = None,
    ) -> ModelRevisionData:
        """Create a new immutable revision on an existing deployment.

        Revisions are immutable — every mutation (legacy ModifyEndpoint included)
        must go through this single entry point. Callers control the base by
        passing ``base`` (``None`` for fresh add, a current-revision draft for
        modify). ``mounts`` carries the vfolder context required by file-based
        draft generators and is not part of the merged RevisionDraft — mount
        identity is not a merge candidate.

        Merge order (low → high):
            1. preset (if ``preset_id`` is supplied)
            2. base (caller-provided — e.g. current revision on modify)
            3. deployment-config.yaml
            4. model-definition.yaml (``model_definition`` field only)
            5. overrides (highest — explicit user input)
        """
        log.info("Adding revision to deployment {}", endpoint_id)

        runtime_variant = overrides.runtime_variant or (
            base.runtime_variant if base is not None else None
        )
        if runtime_variant is None:
            raise InvalidAPIParameters("runtime_variant is required to add a revision")
        context_environ = overrides.environ or (base.environ if base is not None else None)
        context_execution = ExecutionSpec(
            runtime_variant=runtime_variant,
            environ=dict(context_environ) if context_environ else None,
        )

        merged = await self._build_revision_draft(
            request_draft=overrides,
            mounts=mounts,
            execution=context_execution,
            preset_id=preset_id,
            default_architecture=None,
            base=base,
        )

        endpoint_info = await self._deployment_repository.get_endpoint_info(endpoint_id)
        spec = DeploymentRevisionCreatorSpec(
            endpoint_id=endpoint_id,
            image_id=merged.image_id,
            resource_group=endpoint_info.metadata.resource_group,
            resource_slots=ResourceSlot(merged.resource_slots or {}),
            resource_opts=dict(merged.resource_opts) if merged.resource_opts else {},
            cluster_mode=(merged.cluster_mode or ClusterMode.SINGLE_NODE).value,
            cluster_size=merged.cluster_size or 1,
            model_id=mounts.model_vfolder_id,
            model_mount_destination=mounts.model_mount_destination,
            model_definition_path=mounts.model_definition_path,
            # Resolve the merged draft into a strict ModelDefinition; this is
            # the single point where required-field validation runs.
            model_definition=(
                merged.model_definition.to_resolved()
                if merged.model_definition is not None
                else None
            ),
            startup_command=merged.startup_command,
            bootstrap_script=merged.bootstrap_script,
            environ=dict(merged.environ) if merged.environ else {},
            callback_url=str(merged.callback_url) if merged.callback_url else None,
            runtime_variant=merged.runtime_variant or runtime_variant,
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
                element_id=str(endpoint_id),
            ),
        )
        revision_data = await self._deployment_repository.create_revision_with_next_number(
            rbac_creator, endpoint_id
        )
        await self._prune_revision_history(
            endpoint_id, endpoint_info.metadata.revision_history_limit
        )
        return revision_data

    async def add_deployment_revision(
        self,
        deployment_id: uuid.UUID,
        revision: ModelRevisionCreator,
        *,
        auto_activate: bool,
    ) -> ModelRevisionData:
        """Add a revision derived from a ``ModelRevisionCreator`` and optionally activate it.

        Single high-level entry point for v2 ``add_model_revision`` and the
        legacy create/modify flows. Internally delegates to ``add_revision``
        (preset/yaml/request merge + RBAC-checked persist + history prune)
        and, when ``auto_activate=True``, immediately calls
        ``activate_revision`` to set ``deploying_revision`` and trigger the
        DEPLOYING lifecycle.
        """
        mounts = MountMetadata(
            model_vfolder_id=revision.mounts.model_vfolder_id,
            model_definition_path=revision.mounts.model_definition_path,
            model_mount_destination=revision.mounts.model_mount_destination,
        )
        revision_data = await self.add_revision(
            endpoint_id=deployment_id,
            overrides=revision_draft_from_creator(revision),
            mounts=mounts,
            preset_id=revision.revision_preset_id,
        )
        if auto_activate:
            await self.activate_revision(deployment_id, revision_data.id)
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
        base: RevisionDraft | None = None,
    ) -> RevisionDraft:
        """Collect RevisionDrafts from each independent source and merge them.

        Merge order (later overrides earlier):
            1. default architecture (legacy create fallback; lowest)
            2. revision preset (optional)
            3. caller-provided base (e.g. current revision on modify)
            4. deployment-config.yaml in the model vfolder
            5. model-definition.yaml in the model vfolder (model_definition only)
            6. request (highest priority)
        """
        drafts: list[RevisionDraft] = []
        if default_architecture is not None:
            drafts.append(RevisionDraft(image_architecture=default_architecture))
        if preset_id is not None and self._preset_draft_generator is not None:
            drafts.append(await self._preset_draft_generator.generate(preset_id))
        if base is not None:
            drafts.append(base)
        drafts.append(
            await self._deployment_config_draft_generator.generate(
                mounts.model_vfolder_id, execution.runtime_variant
            )
        )
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
            # Resolve the merged draft into a strict ModelDefinition (legacy
            # ``ModelRevisionSpec`` carries the strict type).
            model_definition=(
                merged.model_definition.to_resolved()
                if merged.model_definition is not None
                else None
            ),
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

    # ========== Deployment-level Preset Resolution ==========

    # System defaults used when neither the caller input nor the preset provides a value.
    _DEFAULT_REVISION_HISTORY_LIMIT = 10
    _DEFAULT_REPLICA_COUNT = 1
    _DEFAULT_OPEN_TO_PUBLIC = False

    async def _apply_deployment_level_preset(
        self,
        creator: NewDeploymentCreator,
    ) -> NewDeploymentCreator:
        """Resolve deployment-level fields against the revision preset defaults.

        Priority: explicit caller input > preset default > system default.

        Deployment-level fields currently resolved: ``metadata.revision_history_limit``,
        ``replica_spec``, ``network``, and ``policy``. Fields that were left as ``None``
        on the input creator are filled in from the preset (if a ``revision_preset_id``
        is set on the model revision) and then from the system defaults.
        """
        preset_data: DeploymentRevisionPresetData | None = None
        if (
            creator.model_revision is not None
            and creator.model_revision.revision_preset_id is not None
            and self._deployment_revision_preset_repository is not None
        ):
            preset_data = await self._deployment_revision_preset_repository.get_by_id(
                creator.model_revision.revision_preset_id,
            )

        resolved_history_limit = creator.metadata.revision_history_limit
        if resolved_history_limit is None and preset_data is not None:
            resolved_history_limit = preset_data.revision_history_limit
        if resolved_history_limit is None:
            resolved_history_limit = self._DEFAULT_REVISION_HISTORY_LIMIT
        resolved_metadata = dataclasses.replace(
            creator.metadata,
            revision_history_limit=resolved_history_limit,
        )

        resolved_replica_spec = creator.replica_spec
        if resolved_replica_spec is None:
            preset_replica = (
                preset_data.replica_count
                if preset_data is not None and preset_data.replica_count is not None
                else self._DEFAULT_REPLICA_COUNT
            )
            resolved_replica_spec = ReplicaSpec(replica_count=preset_replica)

        resolved_network = creator.network
        if resolved_network is None:
            preset_open = (
                preset_data.open_to_public
                if preset_data is not None and preset_data.open_to_public is not None
                else self._DEFAULT_OPEN_TO_PUBLIC
            )
            resolved_network = DeploymentNetworkSpec(open_to_public=preset_open)

        resolved_policy = creator.policy
        if resolved_policy is None and preset_data is not None:
            resolved_policy = self._build_policy_from_preset(preset_data)

        return dataclasses.replace(
            creator,
            metadata=resolved_metadata,
            replica_spec=resolved_replica_spec,
            network=resolved_network,
            policy=resolved_policy,
        )

    @staticmethod
    def _build_policy_from_preset(
        preset_data: DeploymentRevisionPresetData,
    ) -> DeploymentPolicyConfig | None:
        """Reconstruct a DeploymentPolicyConfig from preset-stored strategy fields."""
        if preset_data.deployment_strategy is None:
            return None
        spec_dict = preset_data.deployment_strategy_spec or {}
        strategy_spec: RollingUpdateSpec | BlueGreenSpec
        match preset_data.deployment_strategy:
            case DeploymentStrategy.ROLLING:
                strategy_spec = (
                    RollingUpdateSpec.model_validate(spec_dict)
                    if spec_dict
                    else RollingUpdateSpec()
                )
            case DeploymentStrategy.BLUE_GREEN:
                strategy_spec = (
                    BlueGreenSpec.model_validate(spec_dict) if spec_dict else BlueGreenSpec()
                )
        return DeploymentPolicyConfig(
            strategy=preset_data.deployment_strategy,
            strategy_spec=strategy_spec,
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
