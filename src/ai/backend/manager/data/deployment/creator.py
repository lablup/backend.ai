from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.manager.data.deployment.types import (
    DeploymentMetadata,
    DeploymentNetworkSpec,
    ExecutionSpec,
    ImageIdentifierDraft,
    ModelRevisionSpec,
    ModelRevisionSpecDraft,
    MountInfo,
    ReplicaSpec,
    ResourceSpec,
)
from ai.backend.manager.data.image.types import ImageIdentifier
from ai.backend.manager.models.deployment_policy import BlueGreenSpec, RollingUpdateSpec


@dataclass
class VFolderMountsCreator:
    model_vfolder_id: UUID
    model_definition_path: Optional[str] = None
    model_mount_destination: str = "/models"
    extra_mounts: list[MountInfo] = field(default_factory=list)


@dataclass
class ModelRevisionCreator:
    """Creator for model revision.

    Note: Uses image_id directly instead of image_identifier.
    The image_id is resolved by the GQL layer before being passed here.
    """

    image_id: UUID
    resource_spec: ResourceSpec
    mounts: VFolderMountsCreator
    execution: ExecutionSpec


@dataclass
class DeploymentCreator:
    metadata: DeploymentMetadata
    replica_spec: ReplicaSpec
    network: DeploymentNetworkSpec
    model_revision: ModelRevisionSpec
    policy: Optional[DeploymentPolicyConfig] = None

    # Accessor properties for backward compatibility
    @property
    def image_identifier(self) -> ImageIdentifier:
        """Get the image identifier from model revision spec."""
        return self.model_revision.image_identifier

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
    """Configuration for deployment policy.

    Passed from GQL layer to service layer for policy creation/update.
    """

    strategy: DeploymentStrategy
    strategy_spec: RollingUpdateSpec | BlueGreenSpec
    rollback_on_failure: bool = False


@dataclass
class NewDeploymentCreator:
    metadata: DeploymentMetadata
    replica_spec: ReplicaSpec
    network: DeploymentNetworkSpec
    model_revision: ModelRevisionCreator
    policy: Optional[DeploymentPolicyConfig] = None
