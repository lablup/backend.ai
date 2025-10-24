from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

from ai.backend.manager.data.deployment.types import (
    DeploymentMetadata,
    DeploymentNetworkSpec,
    ExecutionSpec,
    ModelRevisionSpec,
    MountInfo,
    MountMetadata,
    ReplicaSpec,
    ResourceSpec,
)
from ai.backend.manager.data.image.types import ImageIdentifier


@dataclass
class VFolderMountsCreator:
    model_vfolder_id: UUID
    model_definition_path: Optional[str] = None
    model_mount_destination: str = "/models"
    extra_mounts: list[MountInfo] = field(default_factory=list)


@dataclass
class ModelRevisionCreator:
    image_identifier: ImageIdentifier
    resource_spec: ResourceSpec
    mounts: VFolderMountsCreator
    execution: ExecutionSpec

    def to_revision_spec(self, mount_metadata: MountMetadata) -> ModelRevisionSpec:
        return ModelRevisionSpec(
            image_identifier=self.image_identifier,
            resource_spec=self.resource_spec,
            mounts=mount_metadata,
            execution=self.execution,
        )


@dataclass
class DeploymentCreator:
    metadata: DeploymentMetadata
    replica_spec: ReplicaSpec
    network: DeploymentNetworkSpec
    model_revision: ModelRevisionSpec

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
class NewDeploymentCreator:
    metadata: DeploymentMetadata
    replica_spec: ReplicaSpec
    network: DeploymentNetworkSpec
    model_revision: ModelRevisionCreator
