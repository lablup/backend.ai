from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from ai.backend.common.config import ModelDefinitionDraft
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.identifier.deployment_preset import DeploymentPresetID
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.manager.data.deployment.types import (
    DeploymentMetadata,
    DeploymentNetworkSpec,
    DeploymentOptions,
    ExecutionSpec,
    ImageIdentifierDraft,
    ModelRevisionSpec,
    ModelRevisionSpecDraft,
    MountInfo,
    ReplicaSpec,
    ResourceSpec,
    RevisionDraft,
)
from ai.backend.manager.data.deployment_revision_preset.types import PresetValueData
from ai.backend.manager.models.deployment_policy import BlueGreenSpec, RollingUpdateSpec


@dataclass
class VFolderMountsCreator:
    # ``model_vfolder_id`` is required: ``AddRevisionInput`` makes
    # ``model_mount_config`` a required input (the revision preset does not
    # carry a model vfolder), so the write path always supplies a concrete
    # vfolder id. The other fields keep server-side column defaults so a
    # partial mount config still produces a valid row.
    model_vfolder_id: VFolderUUID
    model_definition_path: str | None = None
    model_mount_destination: str = "/models"
    extra_mounts: list[MountInfo] = field(default_factory=list)


@dataclass
class ModelRevisionCreator:
    """Creator for model revision.

    Note: Uses image_id directly instead of image_identifier.
    The image_id is resolved by the GQL layer before being passed here.

    ``resource_spec`` and ``execution`` are optional: when omitted the
    revision preset (or the deployment's existing revision on modify)
    must supply the missing fields. Hard-coded defaults at adapter sites
    would otherwise silently override the preset.
    """

    # ``image_id`` is None when no image has been resolved yet at creation
    # time (e.g. revision preset supplies it later). A persisted revision
    # may also surface ``image_id is None`` if the referenced image row
    # was deleted (see ``deployment_revisions.image`` SET NULL FK).
    image_id: ImageID | None
    mounts: VFolderMountsCreator
    resource_spec: ResourceSpec | None = None
    execution: ExecutionSpec | None = None
    model_definition: ModelDefinitionDraft | None = None
    revision_preset_id: DeploymentPresetID | None = None
    preset_values: list[PresetValueData] = field(default_factory=list)

    def to_draft(self) -> RevisionDraft:
        """Project this v2 creator onto a ``RevisionDraft`` layer.

        ``image_id`` is already resolved upstream. Optional ``resource_spec`` /
        ``execution`` are projected only when set; leaving them ``None`` lets
        preset (or other lower-priority sources) supply the missing fields
        without being overridden.
        """
        rs = self.resource_spec
        ex = self.execution
        return RevisionDraft(
            image_id=self.image_id,
            resource_slots=rs.resource_slots if rs is not None else None,
            resource_opts=rs.resource_opts if rs is not None else None,
            cluster_mode=rs.cluster_mode if rs is not None else None,
            cluster_size=rs.cluster_size if rs is not None else None,
            startup_command=ex.startup_command if ex is not None else None,
            bootstrap_script=ex.bootstrap_script if ex is not None else None,
            environ=ex.environ if ex is not None else None,
            runtime_variant_id=ex.runtime_variant_id if ex is not None else None,
            callback_url=ex.callback_url if ex is not None else None,
            inference_runtime_config=ex.inference_runtime_config if ex is not None else None,
            model_definition=self.model_definition,
        )


@dataclass
class DeploymentCreator:
    metadata: DeploymentMetadata
    replica_spec: ReplicaSpec
    network: DeploymentNetworkSpec
    model_revision: ModelRevisionSpec
    policy: DeploymentPolicyConfig | None = None

    @property
    def domain(self) -> str:
        """Get the domain name from metadata."""
        return self.metadata.domain

    @property
    def project(self) -> UUID:
        """Get the project ID from metadata."""
        return self.metadata.project

    @property
    def name(self) -> str:
        """Get the deployment name from metadata."""
        return self.metadata.name


@dataclass
class DeploymentCreationDraft:
    metadata: DeploymentMetadata
    replica_spec: ReplicaSpec
    network: DeploymentNetworkSpec
    draft_model_revision: ModelRevisionSpecDraft

    # Accessor properties for backward compatibility
    @property
    def image_identifier(self) -> ImageIdentifierDraft:
        """Get the requested image identifier from model revision spec."""
        return self.draft_model_revision.image_identifier

    @property
    def domain(self) -> str:
        """Get the domain name from metadata."""
        return self.metadata.domain

    @property
    def project(self) -> UUID:
        """Get the project ID from metadata."""
        return self.metadata.project

    @property
    def name(self) -> str:
        """Get the deployment name from metadata."""
        return self.metadata.name

    def to_creator(
        self,
        model_revision: ModelRevisionSpec,
    ) -> DeploymentCreator:
        return DeploymentCreator(
            metadata=self.metadata,
            replica_spec=self.replica_spec,
            network=self.network,
            model_revision=model_revision,
        )


@dataclass
class DeploymentPolicyConfig:
    """Policy configuration without a target deployment."""

    strategy: DeploymentStrategy
    strategy_spec: RollingUpdateSpec | BlueGreenSpec


@dataclass
class DeploymentPolicyCreator:
    """Creator for deployment policy bound to an existing deployment."""

    deployment_id: UUID
    strategy: DeploymentStrategy
    strategy_spec: RollingUpdateSpec | BlueGreenSpec


@dataclass
class NewDeploymentCreator:
    metadata: DeploymentMetadata
    # `None` means the caller did not specify these deployment-level settings;
    # the service resolves them against the revision preset (if any) and then
    # falls back to the system default.
    replica_spec: ReplicaSpec | None = None
    network: DeploymentNetworkSpec | None = None
    model_revision: ModelRevisionCreator | None = None
    policy: DeploymentPolicyConfig | None = None
    # ``None`` defers to the resource group's ``default_deployment_options``
    # (snapshot-copied at create time). An explicit value overrides.
    options: DeploymentOptions | None = None
