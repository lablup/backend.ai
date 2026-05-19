"""Deployment controller for managing model services and deployments."""

import dataclasses
import functools
import logging
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.exception import UnreachableError
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_preset import DeploymentPresetID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.resource_group import ResourceGroupName
from ai.backend.common.types import (
    ClusterMode,
    MountInfoEntry,
    ResourceSlot,
)
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
    ImageIdentifierDraft,
    ModelRevisionData,
    ModelRevisionSpec,
    ModelRevisionSpecDraft,
    MountInfo,
    ReplicaSpec,
    RevisionDraft,
    RouteInfo,
    RouteTrafficStatus,
)
from ai.backend.manager.data.deployment_revision_preset.types import (
    DeploymentRevisionPresetData,
)
from ai.backend.manager.data.image.types import ImageIdentifier
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.deployment import EndpointNotFound
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
from ai.backend.manager.sokovan.deployment.exceptions import (
    InvalidEndpointState,
)
from ai.backend.manager.sokovan.deployment.revision_draft import RevisionDraftReader
from ai.backend.manager.sokovan.deployment.types import (
    ActivateRevisionResult,
    DeploymentLifecycleType,
)
from ai.backend.manager.sokovan.deployment.validators import (
    DeploymentRevisionValidationContext,
    DeploymentRevisionValidator,
    RequiredResourceSlotRule,
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
    revision_draft_reader: RevisionDraftReader
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
    _revision_draft_reader: RevisionDraftReader
    _deployment_revision_preset_repository: "DeploymentRevisionPresetRepository | None"
    _deployment_revision_validator: DeploymentRevisionValidator

    def __init__(self, args: DeploymentControllerArgs) -> None:
        """Initialize the deployment controller with required services."""
        self._scheduling_controller = args.scheduling_controller
        self._deployment_repository = args.deployment_repository
        self._config_provider = args.config_provider
        self._storage_manager = args.storage_manager
        self._event_producer = args.event_producer
        self._valkey_schedule = args.valkey_schedule
        self._revision_draft_reader = args.revision_draft_reader
        self._deployment_revision_preset_repository = args.deployment_revision_preset_repository
        self._deployment_revision_validator = DeploymentRevisionValidator([
            RequiredResourceSlotRule(),
        ])

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
        # Resolve ``options`` by snapshot-copying the resource group's
        # ``default_deployment_options``. ``creator.options`` will
        # eventually let the API caller override this (commit C); for
        # now it is always ``None`` and we use the RG default verbatim.
        options = creator.options
        if options is None:
            options = (
                await self._deployment_repository.get_resource_group_default_deployment_options(
                    ResourceGroupName(metadata.resource_group)
                )
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
            options=options,
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

        Delegates draft ingestion to ``RevisionDraftReader`` (one read pass
        per source) and relies on ``RevisionDraft.merge`` for the layered
        combination. The caller's ``image_identifier`` is resolved to an
        ``ImageID`` up front because the draft chain now carries a single
        image pointer (no canonical + architecture pair).
        """
        log.info(
            "Building creator from legacy draft '{}' in project {}",
            draft.name,
            draft.project,
        )
        image_id = await self._resolve_draft_image_id(
            draft.draft_model_revision.image_identifier,
            resource_group=draft.metadata.resource_group,
        )
        request_draft = draft.draft_model_revision.to_draft(image_id)
        drafts = await self._revision_draft_reader.read_for_legacy_model_service_deployment(
            request_draft=request_draft,
            execution=draft.draft_model_revision.execution,
            preset_id=None,
        )
        merged = functools.reduce(RevisionDraft.merge, drafts, RevisionDraft())
        model_revision_spec = merged.to_model_revision_spec()
        validation_ctx = await self._build_deployment_revision_validation_context()
        self._deployment_revision_validator.validate_legacy_revision_spec(
            model_revision_spec, validation_ctx
        )
        await self._scheduling_controller.validate_session_spec(
            SessionValidationSpec.from_revision_spec(model_revision=model_revision_spec)
        )
        creator = NewDeploymentCreator(
            metadata=draft.metadata,
            replica_spec=draft.replica_spec,
            network=draft.network,
            model_revision=None,
            policy=None,
        )
        # ``draft.draft_model_revision.mounts.extra_mounts`` is already
        # ``list[MountInfoEntry]`` because the legacy validator pre-resolved
        # via ``prepare_vfolder_mounts``. Project into ``MountInfo`` with
        # the concrete ``mount_perm`` carried over as an explicit override;
        # ``add_deployment_revision`` applies the final permission cap before
        # delegating to ``add_revision``.
        legacy_extra_mounts = [
            MountInfo(
                vfolder_id=m.vfolder_id,
                mount_destination=m.mount_destination,
                mount_perm=m.mount_perm,
                subpath=m.subpath,
            )
            for m in draft.draft_model_revision.mounts.extra_mounts
        ]
        revision = ModelRevisionCreator(
            image_id=merged.image_id,
            resource_spec=model_revision_spec.resource_spec,
            mounts=VFolderMountsCreator(
                model_vfolder_id=model_revision_spec.mounts.model_vfolder_id,
                model_definition_path=model_revision_spec.mounts.model_definition_path,
                model_mount_destination=model_revision_spec.mounts.model_mount_destination,
                extra_mounts=legacy_extra_mounts,
                vfolder_subpath=model_revision_spec.mounts.vfolder_subpath,
            ),
            execution=model_revision_spec.execution,
            model_definition=merged.model_definition,
            revision_preset_id=None,
        )
        return creator, revision

    async def update_deployment(
        self,
        endpoint_id: DeploymentID,
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
        if modified_endpoint.current_revision is not None:
            await self._scheduling_controller.validate_session_spec(
                SessionValidationSpec.from_revision(
                    model_revision=modified_endpoint.current_revision
                )
            )
        res = await self._deployment_repository.update_endpoint_with_spec(updater)
        try:
            await self.mark_lifecycle_needed(DeploymentLifecycleType.CHECK_REPLICA)
        except Exception as e:
            log.error("Failed to mark deployment lifecycle needed: {}", e)
        return res

    async def destroy_deployment(
        self,
        endpoint_id: DeploymentID,
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
        endpoint_id: DeploymentID,
        overrides: RevisionDraft,
        preset_id: DeploymentPresetID | None = None,
    ) -> ModelRevisionData:
        """Create a new immutable revision on an existing deployment.

        Revisions are immutable — every mutation (legacy ModifyEndpoint included)
        must go through this single entry point. ``overrides.mounts`` carries
        the vfolder context required by file-based draft sources and final
        revision persistence.

        Merge order (low → high) is assembled by ``RevisionDraftReader``:
            1. model mount destination as the ``model_path`` default
            2. runtime-variant baseline model definition
            3. revision preset (if ``preset_id`` is supplied)
            4. deployment-config.yaml   (only when the variant reads vfolder files)
            5. model-definition.yaml    (only when the variant reads vfolder files)
            6. overrides (highest — explicit user input)

        ``runtime_variant_id`` is resolved before the draft chain runs because
        the runtime variant's baseline model definition is the first merge
        layer. Callers that drive a revision entirely from a preset (model
        card deploy) leave ``overrides.runtime_variant_id`` unset — in that
        case the preset's ``runtime_variant_id`` is used as the effective id.
        """
        log.info("Adding revision to deployment {}", endpoint_id)

        runtime_variant_id = overrides.runtime_variant_id
        if runtime_variant_id is None and preset_id is not None:
            if self._deployment_revision_preset_repository is None:
                raise InvalidAPIParameters(
                    "runtime_variant_id is required and preset repository is not available."
                )
            preset_data = await self._deployment_revision_preset_repository.get_by_id(preset_id)
            runtime_variant_id = preset_data.runtime_variant_id
        if runtime_variant_id is None:
            raise InvalidAPIParameters(
                "runtime_variant_id is required; provide it in the request "
                "or via a revision preset that sets runtime_variant_id."
            )

        drafts = await self._revision_draft_reader.read_for_deployment_revision(
            runtime_variant_id=runtime_variant_id,
            request_draft=overrides,
            preset_id=preset_id,
        )
        merged = functools.reduce(RevisionDraft.merge, drafts, RevisionDraft())

        endpoint_info = await self._deployment_repository.get_endpoint_info(endpoint_id)
        if merged.image_id is None:
            raise InvalidAPIParameters("image_id is required to add a revision")
        if merged.mounts is None:
            raise InvalidAPIParameters("mounts are required to add a revision")
        if merged.model_definition is None:
            raise InvalidAPIParameters(
                "model_definition is required to add a revision; provide it in the request,"
                " revision preset, or via a model-definition.yaml in the model vfolder"
            )
        resolved_model_definition = merged.model_definition.to_resolved()
        if not resolved_model_definition.models:
            raise InvalidAPIParameters("model_definition.models must contain at least one entry")
        spec = DeploymentRevisionCreatorSpec(
            deployment_id=DeploymentID(endpoint_id),
            image_id=merged.image_id,
            resource_group=endpoint_info.metadata.resource_group,
            resource_slots=ResourceSlot(merged.resource_slots or {}),
            resource_opts=dict(merged.resource_opts) if merged.resource_opts else {},
            cluster_mode=(merged.cluster_mode or ClusterMode.SINGLE_NODE).value,
            cluster_size=merged.cluster_size or 1,
            model_vfolder_id=merged.mounts.model_vfolder_id,
            model_mount_destination=merged.mounts.model_mount_destination,
            vfolder_subpath=merged.mounts.vfolder_subpath,
            model_definition_path=merged.mounts.model_definition_path,
            model_definition=resolved_model_definition,
            startup_command=merged.startup_command,
            bootstrap_script=merged.bootstrap_script,
            environ=dict(merged.environ) if merged.environ else {},
            callback_url=str(merged.callback_url) if merged.callback_url else None,
            runtime_variant_id=runtime_variant_id,
            extra_mounts=list(merged.mounts.extra_mounts),
            preset_values=[
                PresetValueEntry(preset_id=pv.preset_id, value=pv.value)
                for pv in (merged.preset_values or [])
            ],
            revision_preset_id=preset_id,
        )
        validation_ctx = await self._build_deployment_revision_validation_context()
        self._deployment_revision_validator.validate(spec, validation_ctx)
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
        deployment_id: DeploymentID,
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
        # Snapshot each extra mount's permission at revision-write time.
        # The vfolder's current stored permission is always read and caps
        # the caller's request so a mount cannot be elevated beyond what
        # the vfolder grants (``vfolder_perm.cap(user_perm)``). Entries
        # with ``mount_perm is None`` fall through to the vfolder's own
        # permission. The resolved ``MountInfoEntry`` is frozen on the
        # row so later vfolder permission changes cannot retroactively
        # alter sessions spawned from this revision.
        vfolder_perms = await self._deployment_repository.resolve_vfolder_permissions([
            m.vfolder_id for m in revision.mounts.extra_mounts
        ])
        extra_mount_entries = [
            MountInfoEntry(
                vfolder_id=m.vfolder_id,
                mount_destination=m.mount_destination,
                mount_perm=vfolder_perms[m.vfolder_id].cap(m.mount_perm),
                subpath=m.subpath,
            )
            for m in revision.mounts.extra_mounts
        ]
        revision_data = await self.add_revision(
            endpoint_id=deployment_id,
            overrides=revision.to_draft_with_extra_mount(extra_mount_entries),
            preset_id=revision.revision_preset_id,
        )
        if auto_activate:
            await self.activate_revision(deployment_id, revision_data.id)
        return revision_data

    async def activate_revision(
        self,
        deployment_id: DeploymentID,
        revision_id: DeploymentRevisionID,
    ) -> ActivateRevisionResult:
        """Activate a specific revision by initiating the deployment strategy.

        Sets deploying_revision and transitions the deployment to DEPLOYING state.
        The coordinator will execute the configured deployment strategy (rolling
        update, blue-green, etc.) and swap deploying_revision → current_revision
        on completion.

        If a previous rollout is still in progress, its ``deploying_revision`` is
        overwritten; routes belonging to the preempted revision are picked up by
        ``RouteEvictionHandler``'s orphan-revision branch on the next route tick.

        Raises:
            EndpointNotFound: If the deployment does not exist.
            InvalidEndpointState: If the revision is already current.
        """
        # 1. Validate revision exists
        _revision = await self._deployment_repository.get_revision(revision_id)

        # 2. Validate deployment state
        deployment_info = await self._deployment_repository.get_endpoint_info(deployment_id)
        if (
            deployment_info.current_revision is not None
            and deployment_info.current_revision.id == revision_id
        ):
            raise InvalidEndpointState(
                f"Revision {revision_id} is already the current revision "
                f"of deployment {deployment_id}."
            )

        # 3. Set deploying_revision (override any in-flight rollout)
        previous_revision_id, updated = await self._deployment_repository.set_deploying_revision(
            deployment_id, revision_id
        )
        if not updated:
            raise EndpointNotFound(f"Endpoint {deployment_id} not found")

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
        resource_group: str,
    ) -> ModelRevisionSpec:
        """Build a final ``ModelRevisionSpec`` from a legacy draft via the
        ``RevisionDraftReader`` pipeline.

        ``resource_group`` feeds the lowest-priority architecture fallback
        when the caller supplies only the image canonical (no architecture):
        the scaling-group's most common live-agent architecture is used.

        Public entry point used by callers that still need a ``ModelRevisionSpec``
        outside the ``create_deployment`` flow (e.g. model_serving create /
        try_start).
        """
        image_id = await self._resolve_draft_image_id(
            draft_revision.image_identifier, resource_group=resource_group
        )
        request_draft = draft_revision.to_draft(image_id)
        drafts = await self._revision_draft_reader.read_for_legacy_model_service_deployment(
            request_draft=request_draft,
            execution=draft_revision.execution,
            preset_id=None,
        )
        merged = functools.reduce(RevisionDraft.merge, drafts, RevisionDraft())
        model_revision_spec = merged.to_model_revision_spec()
        validation_ctx = await self._build_deployment_revision_validation_context()
        self._deployment_revision_validator.validate_legacy_revision_spec(
            model_revision_spec, validation_ctx
        )
        return model_revision_spec

    # ========== Revision Private Helpers ==========

    async def _build_deployment_revision_validation_context(
        self,
    ) -> DeploymentRevisionValidationContext:
        """Assemble the global config consumed by ``_deployment_revision_validator``.

        Carries orthogonal global validation prerequisites (e.g.
        ``resource_slot_types.required``) that are not derivable from the
        per-request creator spec.
        """
        required_slot_names = await self._deployment_repository.fetch_revision_required_slot_names()
        return DeploymentRevisionValidationContext(required_slot_names=required_slot_names)

    async def _resolve_draft_image_id(
        self,
        image_identifier: ImageIdentifierDraft,
        resource_group: str,
    ) -> ImageID | None:
        """Resolve the (canonical, architecture) request to an ``ImageID``.

        When the caller supplies ``canonical`` but omits ``architecture``, the
        scaling group's default architecture (most common live-agent arch)
        is used as a fallback. Returns ``None`` if the caller supplied no
        canonical reference at all (e.g. preset is expected to carry the
        image id later).
        """
        if image_identifier is None or image_identifier.canonical is None:
            return None
        architecture = image_identifier.architecture
        if not architecture:
            architecture = (
                await self._deployment_repository.get_default_architecture_from_scaling_group(
                    resource_group
                )
            )
            if architecture is None:
                raise InvalidAPIParameters(
                    "architecture is required for image resolution and no default "
                    f"architecture is available in scaling group '{resource_group}'."
                )
        return await self._deployment_repository.get_image_id(
            ImageIdentifier(
                canonical=image_identifier.canonical,
                architecture=architecture,
            )
        )

    async def _prune_revision_history(
        self,
        deployment_id: DeploymentID,
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
                if preset_data is not None
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
    ) -> DeploymentPolicyConfig:
        """Reconstruct a DeploymentPolicyConfig from preset-stored strategy fields."""
        spec_dict = preset_data.deployment_strategy_spec
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
